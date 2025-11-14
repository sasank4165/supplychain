"""Lambda Authorizer for API Gateway with Cognito JWT validation"""
import json
import os
import jwt
import requests
from typing import Dict, Any

# Cache for Cognito public keys
_jwks_cache = None

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda authorizer for API Gateway
    Validates Cognito JWT tokens and returns IAM policy
    """
    
    token = event.get('authorizationToken', '').replace('Bearer ', '')
    method_arn = event['methodArn']
    
    if not token:
        raise Exception('Unauthorized')
    
    try:
        # Verify and decode token
        user_info = verify_token(token)
        
        # Extract user details
        username = user_info.get('cognito:username')
        groups = user_info.get('cognito:groups', [])
        
        # Determine persona from groups
        persona = get_persona_from_groups(groups)
        
        # Generate IAM policy
        policy = generate_policy(
            principal_id=username,
            effect='Allow',
            resource=method_arn,
            context={
                'username': username,
                'groups': json.dumps(groups),
                'persona': persona,
                'email': user_info.get('email', '')
            }
        )
        
        return policy
        
    except jwt.ExpiredSignatureError:
        raise Exception('Token expired')
    except jwt.InvalidTokenError:
        raise Exception('Invalid token')
    except Exception as e:
        print(f"Authorization error: {str(e)}")
        raise Exception('Unauthorized')


def verify_token(token: str) -> Dict[str, Any]:
    """Verify Cognito JWT token"""
    
    user_pool_id = os.environ.get('USER_POOL_ID')
    region = os.environ.get('AWS_REGION', 'us-east-1')
    
    # Get Cognito public keys
    keys = get_cognito_public_keys(user_pool_id, region)
    
    # Decode token header to get key ID
    headers = jwt.get_unverified_header(token)
    kid = headers['kid']
    
    # Find the correct key
    key = None
    for k in keys:
        if k['kid'] == kid:
            key = k
            break
    
    if not key:
        raise jwt.InvalidTokenError('Public key not found')
    
    # Verify token
    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
    
    decoded = jwt.decode(
        token,
        public_key,
        algorithms=['RS256'],
        audience=os.environ.get('USER_POOL_CLIENT_ID'),
        issuer=f'https://cognito-idp.{region}.amazonaws.com/{user_pool_id}'
    )
    
    return decoded


def get_cognito_public_keys(user_pool_id: str, region: str) -> list:
    """Get Cognito public keys for token verification"""
    global _jwks_cache
    
    if _jwks_cache:
        return _jwks_cache
    
    keys_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
    response = requests.get(keys_url)
    jwks = response.json()
    
    _jwks_cache = jwks['keys']
    return _jwks_cache


def get_persona_from_groups(groups: list) -> str:
    """Determine persona from Cognito groups"""
    group_to_persona = {
        'warehouse_managers': 'warehouse_manager',
        'field_engineers': 'field_engineer',
        'procurement_specialists': 'procurement_specialist'
    }
    
    for group in groups:
        if group in group_to_persona:
            return group_to_persona[group]
    
    return 'unknown'


def generate_policy(principal_id: str, effect: str, resource: str, context: Dict = None) -> Dict:
    """Generate IAM policy for API Gateway"""
    
    policy = {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': resource
                }
            ]
        }
    }
    
    if context:
        policy['context'] = context
    
    return policy
