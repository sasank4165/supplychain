"""Authentication and Authorization Manager"""
import boto3
import os
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import hmac
import base64

from auth import jwt_utils as jwt

class AuthManager:
    """Manages authentication and authorization for supply chain agents"""
    
    def __init__(self, user_pool_id: str, client_id: str, region: str = "us-east-1"):
        self.user_pool_id = user_pool_id
        self.client_id = client_id
        self.region = region
        self.cognito_client = boto3.client('cognito-idp', region_name=region)
        
        # Persona to group mapping
        self.persona_groups = {
            "warehouse_manager": "warehouse_managers",
            "field_engineer": "field_engineers",
            "procurement_specialist": "procurement_specialists"
        }
        
        # Role-based table access control
        self.role_table_access = {
            "warehouse_managers": [
                "product",
                "warehouse_product",
                "sales_order_header",
                "sales_order_line"
            ],
            "field_engineers": [
                "product",
                "warehouse_product",
                "sales_order_header",
                "sales_order_line"
            ],
            "procurement_specialists": [
                "product",
                "warehouse_product",
                "purchase_order_header",
                "purchase_order_line"
            ]
        }
        
        # Role-based agent access
        self.role_agent_access = {
            "warehouse_managers": ["sql_agent", "inventory_optimizer"],
            "field_engineers": ["sql_agent", "logistics_optimizer"],
            "procurement_specialists": ["sql_agent", "supplier_analyzer"]
        }
    
    def sign_up(self, username: str, password: str, email: str, persona: str) -> Dict:
        """Sign up a new user"""
        try:
            response = self.cognito_client.sign_up(
                ClientId=self.client_id,
                Username=username,
                Password=password,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'custom:persona', 'Value': persona}
                ]
            )
            return {
                "success": True,
                "user_sub": response['UserSub'],
                "message": "User created successfully. Please verify email."
            }
        except self.cognito_client.exceptions.UsernameExistsException:
            return {"success": False, "error": "Username already exists"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def sign_in(self, username: str, password: str) -> Dict:
        """Sign in a user and return tokens"""
        try:
            # Calculate SECRET_HASH if client secret is configured
            response = self.cognito_client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                }
            )
            
            if 'ChallengeName' in response:
                return {
                    "success": False,
                    "challenge": response['ChallengeName'],
                    "session": response['Session']
                }
            
            tokens = response['AuthenticationResult']
            
            # Decode ID token to get user info
            id_token = tokens['IdToken']
            user_info = self._decode_token(id_token)
            
            # Get user groups
            groups = self._get_user_groups(username)
            persona = self._get_persona_from_groups(groups)
            
            return {
                "success": True,
                "access_token": tokens['AccessToken'],
                "id_token": id_token,
                "refresh_token": tokens['RefreshToken'],
                "expires_in": tokens['ExpiresIn'],
                "username": user_info.get('cognito:username'),
                "email": user_info.get('email'),
                "groups": groups,
                "persona": persona
            }
        except self.cognito_client.exceptions.NotAuthorizedException:
            return {"success": False, "error": "Invalid username or password"}
        except self.cognito_client.exceptions.UserNotFoundException:
            return {"success": False, "error": "User not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def refresh_token(self, refresh_token: str) -> Dict:
        """Refresh access token"""
        try:
            response = self.cognito_client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='REFRESH_TOKEN_AUTH',
                AuthParameters={
                    'REFRESH_TOKEN': refresh_token
                }
            )
            
            tokens = response['AuthenticationResult']
            return {
                "success": True,
                "access_token": tokens['AccessToken'],
                "id_token": tokens['IdToken'],
                "expires_in": tokens['ExpiresIn']
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def sign_out(self, access_token: str) -> Dict:
        """Sign out a user"""
        try:
            self.cognito_client.global_sign_out(
                AccessToken=access_token
            )
            return {"success": True, "message": "Signed out successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def change_password(self, access_token: str, old_password: str, new_password: str) -> Dict:
        """Change user password"""
        try:
            self.cognito_client.change_password(
                AccessToken=access_token,
                PreviousPassword=old_password,
                ProposedPassword=new_password
            )
            return {"success": True, "message": "Password changed successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def forgot_password(self, username: str) -> Dict:
        """Initiate forgot password flow"""
        try:
            response = self.cognito_client.forgot_password(
                ClientId=self.client_id,
                Username=username
            )
            return {
                "success": True,
                "message": "Verification code sent to email",
                "code_delivery": response['CodeDeliveryDetails']
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def confirm_forgot_password(self, username: str, code: str, new_password: str) -> Dict:
        """Confirm forgot password with verification code"""
        try:
            self.cognito_client.confirm_forgot_password(
                ClientId=self.client_id,
                Username=username,
                ConfirmationCode=code,
                Password=new_password
            )
            return {"success": True, "message": "Password reset successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def verify_token(self, token: str) -> Dict:
        """Verify and decode JWT token"""
        try:
            decoded = self._decode_token(token)
            
            # Check expiration
            exp = decoded.get('exp', 0)
            if datetime.utcnow().timestamp() > exp:
                return {"valid": False, "error": "Token expired"}
            
            username = decoded.get('cognito:username')
            groups = self._get_user_groups(username)
            persona = self._get_persona_from_groups(groups)
            
            return {
                "valid": True,
                "username": username,
                "email": decoded.get('email'),
                "groups": groups,
                "persona": persona,
                "sub": decoded.get('sub')
            }
        except jwt.ExpiredSignatureError:
            return {"valid": False, "error": "Token expired"}
        except jwt.InvalidTokenError:
            return {"valid": False, "error": "Invalid token"}
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def check_table_access(self, groups: List[str], table_name: str) -> bool:
        """Check if user has access to a table"""
        for group in groups:
            if group in self.role_table_access:
                if table_name in self.role_table_access[group]:
                    return True
        return False
    
    def check_agent_access(self, groups: List[str], agent_name: str) -> bool:
        """Check if user has access to an agent"""
        for group in groups:
            if group in self.role_agent_access:
                if agent_name in self.role_agent_access[group]:
                    return True
        return False
    
    def get_accessible_tables(self, groups: List[str]) -> List[str]:
        """Get list of tables accessible to user"""
        tables = set()
        for group in groups:
            if group in self.role_table_access:
                tables.update(self.role_table_access[group])
        return list(tables)
    
    def get_accessible_agents(self, groups: List[str]) -> List[str]:
        """Get list of agents accessible to user"""
        agents = set()
        for group in groups:
            if group in self.role_agent_access:
                agents.update(self.role_agent_access[group])
        return list(agents)
    
    def _get_user_groups(self, username: str) -> List[str]:
        """Get user's Cognito groups"""
        try:
            response = self.cognito_client.admin_list_groups_for_user(
                Username=username,
                UserPoolId=self.user_pool_id
            )
            return [group['GroupName'] for group in response['Groups']]
        except Exception:
            return []
    
    def _get_persona_from_groups(self, groups: List[str]) -> Optional[str]:
        """Determine persona from groups"""
        for persona, group in self.persona_groups.items():
            if group in groups:
                return persona
        return None
    
    def _decode_token(self, token: str) -> Dict:
        """Decode JWT token without verification (for development)"""
        # In production, verify signature using Cognito public keys
        return jwt.decode(token, options={"verify_signature": False})
    
    def _get_cognito_public_keys(self):
        """Get Cognito public keys for token verification"""
        import requests
        keys_url = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"
        response = requests.get(keys_url)
        return response.json()['keys']


def require_auth(func):
    """Decorator to require authentication"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get token from request context
        token = kwargs.get('token') or kwargs.get('access_token')
        if not token:
            return {"error": "Authentication required", "status": 401}
        
        auth_manager = kwargs.get('auth_manager')
        if not auth_manager:
            return {"error": "Auth manager not configured", "status": 500}
        
        # Verify token
        verification = auth_manager.verify_token(token)
        if not verification.get('valid'):
            return {"error": verification.get('error', 'Invalid token'), "status": 401}
        
        # Add user info to kwargs
        kwargs['user_info'] = verification
        return func(*args, **kwargs)
    
    return wrapper


def require_persona(allowed_personas: List[str]):
    """Decorator to require specific persona"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_info = kwargs.get('user_info')
            if not user_info:
                return {"error": "User info not found", "status": 401}
            
            persona = user_info.get('persona')
            if persona not in allowed_personas:
                return {
                    "error": f"Access denied. Required persona: {', '.join(allowed_personas)}",
                    "status": 403
                }
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_table_access(table_name: str):
    """Decorator to require access to specific table"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_info = kwargs.get('user_info')
            auth_manager = kwargs.get('auth_manager')
            
            if not user_info or not auth_manager:
                return {"error": "Authentication required", "status": 401}
            
            groups = user_info.get('groups', [])
            if not auth_manager.check_table_access(groups, table_name):
                return {
                    "error": f"Access denied to table: {table_name}",
                    "status": 403
                }
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
