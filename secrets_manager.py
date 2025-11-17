"""Secrets and Parameter Management for Supply Chain Agentic AI Application

This module provides centralized secrets and parameter management with:
- AWS Secrets Manager integration for sensitive data
- AWS Systems Manager Parameter Store integration for configuration
- Environment variable support
- Caching for performance
- Automatic secret rotation support
"""

import os
import json
import boto3
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError


class SecretsError(Exception):
    """Raised when secrets or parameters cannot be retrieved"""
    pass


class SecretsManager:
    """Manage secrets and parameters from AWS Secrets Manager and Parameter Store
    
    Provides a unified interface for retrieving sensitive configuration from
    AWS services with caching and fallback to environment variables.
    """
    
    def __init__(self, region: str = None, prefix: str = None):
        """Initialize secrets manager
        
        Args:
            region: AWS region. If None, uses AWS_REGION env var or default
            prefix: Prefix for parameter/secret names (e.g., 'sc-agent-dev')
        """
        self.region = region or os.getenv('AWS_REGION', 'us-east-1')
        self.prefix = prefix or os.getenv('SC_AGENT_PREFIX', 'sc-agent')
        
        # Initialize AWS clients
        try:
            self.ssm = boto3.client('ssm', region_name=self.region)
            self.secrets = boto3.client('secretsmanager', region_name=self.region)
        except Exception as e:
            print(f"Warning: Failed to initialize AWS clients: {e}")
            self.ssm = None
            self.secrets = None
        
        # Cache for retrieved values
        self._cache: Dict[str, Any] = {}
    
    def get_secret(self, name: str, use_cache: bool = True) -> str:
        """Retrieve secret from Secrets Manager
        
        Args:
            name: Secret name (without prefix)
            use_cache: Whether to use cached value
            
        Returns:
            Secret value as string
            
        Raises:
            SecretsError: If secret cannot be retrieved
            
        Example:
            >>> sm = SecretsManager(prefix='sc-agent-dev')
            >>> api_key = sm.get_secret('api-key')
        """
        cache_key = f"secret:{name}"
        
        # Check cache
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]
        
        # Try environment variable first (for local development)
        env_var = f"SECRET_{name.upper().replace('-', '_')}"
        if env_var in os.environ:
            value = os.environ[env_var]
            self._cache[cache_key] = value
            return value
        
        # Retrieve from Secrets Manager
        if not self.secrets:
            raise SecretsError(
                f"Secrets Manager client not initialized. "
                f"Set {env_var} environment variable for local development."
            )
        
        secret_name = f"{self.prefix}/{name}"
        
        try:
            response = self.secrets.get_secret_value(SecretId=secret_name)
            
            # Handle both string and JSON secrets
            if 'SecretString' in response:
                value = response['SecretString']
                
                # Try to parse as JSON
                try:
                    json_value = json.loads(value)
                    # If it's a dict with a single key, return that value
                    if isinstance(json_value, dict) and len(json_value) == 1:
                        value = list(json_value.values())[0]
                    else:
                        value = json_value
                except json.JSONDecodeError:
                    pass  # Keep as string
            else:
                # Binary secret
                value = response['SecretBinary']
            
            # Cache the value
            if use_cache:
                self._cache[cache_key] = value
            
            return value
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                raise SecretsError(f"Secret not found: {secret_name}")
            elif error_code == 'AccessDeniedException':
                raise SecretsError(f"Access denied to secret: {secret_name}")
            else:
                raise SecretsError(f"Error retrieving secret {secret_name}: {str(e)}")
    
    def get_parameter(self, name: str, use_cache: bool = True, decrypt: bool = True) -> str:
        """Retrieve parameter from Parameter Store
        
        Args:
            name: Parameter name (without prefix)
            use_cache: Whether to use cached value
            decrypt: Whether to decrypt SecureString parameters
            
        Returns:
            Parameter value as string
            
        Raises:
            SecretsError: If parameter cannot be retrieved
            
        Example:
            >>> sm = SecretsManager(prefix='sc-agent-dev')
            >>> db_name = sm.get_parameter('database-name')
        """
        cache_key = f"param:{name}"
        
        # Check cache
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]
        
        # Try environment variable first (for local development)
        env_var = f"PARAM_{name.upper().replace('-', '_')}"
        if env_var in os.environ:
            value = os.environ[env_var]
            self._cache[cache_key] = value
            return value
        
        # Retrieve from Parameter Store
        if not self.ssm:
            raise SecretsError(
                f"SSM client not initialized. "
                f"Set {env_var} environment variable for local development."
            )
        
        param_name = f"/{self.prefix}/{name}"
        
        try:
            response = self.ssm.get_parameter(
                Name=param_name,
                WithDecryption=decrypt
            )
            
            value = response['Parameter']['Value']
            
            # Cache the value
            if use_cache:
                self._cache[cache_key] = value
            
            return value
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ParameterNotFound':
                raise SecretsError(f"Parameter not found: {param_name}")
            elif error_code == 'AccessDeniedException':
                raise SecretsError(f"Access denied to parameter: {param_name}")
            else:
                raise SecretsError(f"Error retrieving parameter {param_name}: {str(e)}")
    
    def get_parameters_by_path(self, path: str, decrypt: bool = True) -> Dict[str, str]:
        """Retrieve all parameters under a path
        
        Args:
            path: Parameter path (without prefix)
            decrypt: Whether to decrypt SecureString parameters
            
        Returns:
            Dictionary of parameter names to values
            
        Example:
            >>> sm = SecretsManager(prefix='sc-agent-dev')
            >>> db_params = sm.get_parameters_by_path('database')
        """
        if not self.ssm:
            raise SecretsError("SSM client not initialized")
        
        full_path = f"/{self.prefix}/{path}"
        parameters = {}
        
        try:
            paginator = self.ssm.get_paginator('get_parameters_by_path')
            
            for page in paginator.paginate(
                Path=full_path,
                Recursive=True,
                WithDecryption=decrypt
            ):
                for param in page['Parameters']:
                    # Remove prefix from name
                    name = param['Name'].replace(f"{full_path}/", "")
                    parameters[name] = param['Value']
            
            return parameters
            
        except ClientError as e:
            raise SecretsError(f"Error retrieving parameters from path {full_path}: {str(e)}")
    
    def put_secret(self, name: str, value: str, description: str = "") -> str:
        """Store secret in Secrets Manager
        
        Args:
            name: Secret name (without prefix)
            value: Secret value (string or dict)
            description: Secret description
            
        Returns:
            Secret ARN
            
        Example:
            >>> sm = SecretsManager(prefix='sc-agent-dev')
            >>> sm.put_secret('api-key', 'my-secret-key')
        """
        if not self.secrets:
            raise SecretsError("Secrets Manager client not initialized")
        
        secret_name = f"{self.prefix}/{name}"
        
        # Convert dict to JSON string
        if isinstance(value, dict):
            value = json.dumps(value)
        
        try:
            # Try to update existing secret
            response = self.secrets.update_secret(
                SecretId=secret_name,
                SecretString=value
            )
            
            # Clear cache
            cache_key = f"secret:{name}"
            if cache_key in self._cache:
                del self._cache[cache_key]
            
            return response['ARN']
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Create new secret
                response = self.secrets.create_secret(
                    Name=secret_name,
                    Description=description,
                    SecretString=value
                )
                return response['ARN']
            else:
                raise SecretsError(f"Error storing secret {secret_name}: {str(e)}")
    
    def put_parameter(
        self,
        name: str,
        value: str,
        secure: bool = False,
        description: str = "",
        overwrite: bool = True
    ) -> str:
        """Store parameter in Parameter Store
        
        Args:
            name: Parameter name (without prefix)
            value: Parameter value
            secure: Whether to use SecureString type
            description: Parameter description
            overwrite: Whether to overwrite existing parameter
            
        Returns:
            Parameter version
            
        Example:
            >>> sm = SecretsManager(prefix='sc-agent-dev')
            >>> sm.put_parameter('database-name', 'my-db')
        """
        if not self.ssm:
            raise SecretsError("SSM client not initialized")
        
        param_name = f"/{self.prefix}/{name}"
        param_type = 'SecureString' if secure else 'String'
        
        try:
            response = self.ssm.put_parameter(
                Name=param_name,
                Value=value,
                Type=param_type,
                Description=description,
                Overwrite=overwrite
            )
            
            # Clear cache
            cache_key = f"param:{name}"
            if cache_key in self._cache:
                del self._cache[cache_key]
            
            return str(response['Version'])
            
        except ClientError as e:
            raise SecretsError(f"Error storing parameter {param_name}: {str(e)}")
    
    def clear_cache(self):
        """Clear the internal cache"""
        self._cache.clear()
    
    def __repr__(self) -> str:
        return f"SecretsManager(region='{self.region}', prefix='{self.prefix}')"


# Convenience functions for quick access
def get_secret(name: str, prefix: str = None, region: str = None) -> str:
    """Get secret from Secrets Manager
    
    Args:
        name: Secret name
        prefix: Optional prefix override
        region: Optional region override
        
    Returns:
        Secret value
    """
    sm = SecretsManager(region=region, prefix=prefix)
    return sm.get_secret(name)


def get_parameter(name: str, prefix: str = None, region: str = None) -> str:
    """Get parameter from Parameter Store
    
    Args:
        name: Parameter name
        prefix: Optional prefix override
        region: Optional region override
        
    Returns:
        Parameter value
    """
    sm = SecretsManager(region=region, prefix=prefix)
    return sm.get_parameter(name)
