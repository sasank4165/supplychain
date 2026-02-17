"""
Configuration Manager for Supply Chain AI MVP

Loads and validates configuration from YAML file with environment variable substitution.
"""

import os
import re
import yaml
from typing import Any, Dict, Optional
from pathlib import Path


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


class ConfigManager:
    """Manages application configuration with validation and environment variable substitution."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration YAML file
            
        Raises:
            ConfigError: If configuration file is missing or invalid
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Returns:
            Configuration dictionary
            
        Raises:
            ConfigError: If file cannot be loaded
        """
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            raise ConfigError(
                f"Configuration file not found: {self.config_path}\n"
                f"Please create it from config.example.yaml"
            )
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            if config is None:
                raise ConfigError("Configuration file is empty")
            
            # Substitute environment variables
            config = self._substitute_env_vars(config)
            
            return config
            
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ConfigError(f"Error loading configuration: {e}")
    
    def _substitute_env_vars(self, obj: Any) -> Any:
        """
        Recursively substitute environment variables in configuration.
        
        Supports ${VAR_NAME} and ${VAR_NAME:default_value} syntax.
        
        Args:
            obj: Configuration object (dict, list, str, or other)
            
        Returns:
            Object with environment variables substituted
        """
        if isinstance(obj, dict):
            return {key: self._substitute_env_vars(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            return self._substitute_env_var_string(obj)
        else:
            return obj
    
    def _substitute_env_var_string(self, value: str) -> str:
        """
        Substitute environment variables in a string.
        
        Args:
            value: String potentially containing ${VAR_NAME} or ${VAR_NAME:default}
            
        Returns:
            String with environment variables substituted
        """
        # Pattern matches ${VAR_NAME} or ${VAR_NAME:default_value}
        pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
        
        def replace_var(match):
            var_name = match.group(1)
            default_value = match.group(2)
            
            env_value = os.environ.get(var_name)
            
            if env_value is not None:
                return env_value
            elif default_value is not None:
                return default_value
            else:
                raise ConfigError(
                    f"Environment variable '{var_name}' is not set and no default provided"
                )
        
        return re.sub(pattern, replace_var, value)
    
    def _validate_config(self) -> None:
        """
        Validate that required configuration fields are present.
        
        Raises:
            ConfigError: If required fields are missing
        """
        required_fields = [
            'aws.region',
            'aws.bedrock.model_id',
            'aws.redshift.workgroup_name',
            'aws.redshift.database',
            'aws.glue.database',
            'aws.lambda.inventory_function',
            'aws.lambda.logistics_function',
            'aws.lambda.supplier_function',
            'app.name',
            'cache.enabled',
            'conversation.max_history',
            'cost.enabled',
            'logging.level',
            'auth.users_file'
        ]
        
        for field in required_fields:
            if self._get_nested(field) is None:
                raise ConfigError(f"Missing required configuration field: {field}")
    
    def _get_nested(self, path: str) -> Optional[Any]:
        """
        Get nested configuration value using dot notation.
        
        Args:
            path: Dot-separated path (e.g., 'aws.bedrock.model_id')
            
        Returns:
            Configuration value or None if not found
        """
        keys = path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            path: Dot-separated path (e.g., 'aws.bedrock.model_id')
            default: Default value if path not found
            
        Returns:
            Configuration value or default
        """
        value = self._get_nested(path)
        return value if value is not None else default
    
    def get_aws_region(self) -> str:
        """Get AWS region."""
        return self.get('aws.region')
    
    def get_bedrock_config(self) -> Dict[str, Any]:
        """Get Bedrock configuration."""
        return self.get('aws.bedrock', {})
    
    def get_redshift_config(self) -> Dict[str, Any]:
        """Get Redshift configuration."""
        return self.get('aws.redshift', {})
    
    def get_glue_config(self) -> Dict[str, Any]:
        """Get Glue configuration."""
        return self.get('aws.glue', {})
    
    def get_lambda_config(self) -> Dict[str, Any]:
        """Get Lambda configuration."""
        return self.get('aws.lambda', {})
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration."""
        return self.get('cache', {})
    
    def get_conversation_config(self) -> Dict[str, Any]:
        """Get conversation configuration."""
        return self.get('conversation', {})
    
    def get_cost_config(self) -> Dict[str, Any]:
        """Get cost tracking configuration."""
        return self.get('cost', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return self.get('logging', {})
    
    def get_auth_config(self) -> Dict[str, Any]:
        """Get authentication configuration."""
        return self.get('auth', {})
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self.config = self._load_config()
        self._validate_config()
