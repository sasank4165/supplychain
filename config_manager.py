"""Configuration Management System for Supply Chain Agentic AI Application

This module provides centralized configuration management with:
- YAML configuration file loading
- JSON Schema validation
- Environment variable support
- Dynamic resource naming
- Configuration inheritance and defaults
- Integration with AWS Secrets Manager and Parameter Store
"""

import os
import json
import yaml
import boto3
from typing import Dict, Any, Optional, List
from pathlib import Path
from copy import deepcopy

# Try to import SecretsManager (optional dependency)
try:
    from secrets_manager import SecretsManager
    SECRETS_MANAGER_AVAILABLE = True
except ImportError:
    SECRETS_MANAGER_AVAILABLE = False


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing"""
    pass


class ConfigurationManager:
    """Centralized configuration management
    
    Loads and validates environment-specific configuration from YAML files,
    supports environment variable overrides, and provides convenient access
    to configuration values.
    """
    
    def __init__(self, environment: str = None, config_path: str = "config", use_secrets: bool = True):
        """Initialize configuration manager
        
        Args:
            environment: Environment name (dev, staging, prod). 
                        If None, reads from ENVIRONMENT env var or defaults to 'dev'
            config_path: Path to configuration directory
            use_secrets: Whether to enable SecretsManager integration
        """
        self.environment = environment or os.getenv("ENVIRONMENT", "dev")
        self.config_path = Path(config_path)
        self.schema = self._load_schema()
        self.config = self._load_config()
        self._validate_config()
        self._resolve_auto_values()
        
        # Initialize SecretsManager if available and enabled
        self.secrets_manager = None
        if use_secrets and SECRETS_MANAGER_AVAILABLE:
            try:
                self.secrets_manager = SecretsManager(
                    region=self.get('environment.region'),
                    prefix=self.get('project.prefix')
                )
            except Exception as e:
                print(f"Warning: Failed to initialize SecretsManager: {e}")
    
    def _load_schema(self) -> Dict:
        """Load JSON schema for validation"""
        schema_file = self.config_path / "schema.json"
        if not schema_file.exists():
            raise ConfigurationError(f"Schema file not found: {schema_file}")
        
        with open(schema_file, 'r') as f:
            return json.load(f)
    
    def _load_config(self) -> Dict:
        """Load and merge configuration files
        
        Loads base configuration and environment-specific overrides.
        """
        config_file = self.config_path / f"{self.environment}.yaml"
        
        if not config_file.exists():
            raise ConfigurationError(
                f"Configuration file not found: {config_file}\n"
                f"Available environments: {self._list_available_environments()}"
            )
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Apply environment variable overrides
        config = self._apply_env_overrides(config)
        
        return config
    
    def _list_available_environments(self) -> List[str]:
        """List available environment configurations"""
        if not self.config_path.exists():
            return []
        
        env_files = self.config_path.glob("*.yaml")
        return [f.stem for f in env_files if f.stem != "base"]
    
    def _apply_env_overrides(self, config: Dict) -> Dict:
        """Apply environment variable overrides to configuration
        
        Supports overrides in the format: SC_AGENT_<SECTION>_<KEY>=value
        Example: SC_AGENT_RESOURCES_LAMBDA_MEMORY_MB=1024
        """
        prefix = "SC_AGENT_"
        
        for env_key, env_value in os.environ.items():
            if not env_key.startswith(prefix):
                continue
            
            # Parse the key path
            key_path = env_key[len(prefix):].lower().split('_')
            
            # Navigate to the correct location in config
            current = config
            for key in key_path[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            # Set the value (attempt type conversion)
            final_key = key_path[-1]
            current[final_key] = self._convert_env_value(env_value)
        
        return config
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type"""
        # Boolean conversion
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False
        
        # Integer conversion
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _validate_config(self):
        """Validate configuration against JSON schema"""
        try:
            from jsonschema import validate, ValidationError
            validate(instance=self.config, schema=self.schema)
        except ImportError:
            # jsonschema not installed, skip validation
            print("Warning: jsonschema not installed, skipping validation")
        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed: {str(e)}")
    
    def _resolve_auto_values(self):
        """Resolve 'auto' values like account_id"""
        account_id = self.config.get('environment', {}).get('account_id')
        
        if account_id == 'auto':
            try:
                sts = boto3.client('sts')
                identity = sts.get_caller_identity()
                self.config['environment']['account_id'] = identity['Account']
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to auto-detect AWS account ID: {str(e)}\n"
                    "Ensure AWS credentials are configured or set account_id explicitly"
                )
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value by dot notation path
        
        Args:
            key_path: Dot-separated path to config value (e.g., 'resources.lambda.memory_mb')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Example:
            >>> config.get('resources.lambda.memory_mb')
            512
        """
        keys = key_path.split('.')
        current = self.config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def get_required(self, key_path: str) -> Any:
        """Get required configuration value, raise error if missing
        
        Args:
            key_path: Dot-separated path to config value
            
        Returns:
            Configuration value
            
        Raises:
            ConfigurationError: If key not found
        """
        value = self.get(key_path)
        if value is None:
            raise ConfigurationError(f"Required configuration key not found: {key_path}")
        return value
    
    def get_tags(self) -> Dict[str, str]:
        """Get all tags for resources
        
        Returns standard tags plus custom tags from configuration.
        """
        tags = {
            'Project': self.get('project.name', 'supply-chain-agent'),
            'Environment': self.get('environment.name'),
            'ManagedBy': 'CDK',
            'Owner': self.get('project.owner', 'platform-team'),
            'CostCenter': self.get('project.cost_center', 'supply-chain')
        }
        
        # Add custom tags
        custom_tags = self.get('tags.custom', {})
        tags.update(custom_tags)
        
        return tags
    
    def get_all(self) -> Dict:
        """Get complete configuration dictionary"""
        return deepcopy(self.config)
    
    def get_secret(self, name: str) -> Optional[str]:
        """Get secret from Secrets Manager
        
        Args:
            name: Secret name (without prefix)
            
        Returns:
            Secret value or None if not available
            
        Example:
            >>> config.get_secret('api-key')
        """
        if not self.secrets_manager:
            return None
        
        try:
            return self.secrets_manager.get_secret(name)
        except Exception as e:
            print(f"Warning: Failed to retrieve secret '{name}': {e}")
            return None
    
    def get_parameter(self, name: str) -> Optional[str]:
        """Get parameter from Parameter Store
        
        Args:
            name: Parameter name (without prefix)
            
        Returns:
            Parameter value or None if not available
            
        Example:
            >>> config.get_parameter('database-name')
        """
        if not self.secrets_manager:
            return None
        
        try:
            return self.secrets_manager.get_parameter(name)
        except Exception as e:
            print(f"Warning: Failed to retrieve parameter '{name}': {e}")
            return None
    
    def __repr__(self) -> str:
        return f"ConfigurationManager(environment='{self.environment}')"


class ResourceNamer:
    """Generate consistent resource names following naming conventions
    
    Naming patterns:
    - S3 Bucket: {prefix}-{purpose}-{account_id}-{region}
    - DynamoDB Table: {prefix}-{name}-{environment}
    - Lambda Function: {prefix}-{name}-{environment}
    - IAM Role: {prefix}-{purpose}-{environment}
    """
    
    def __init__(self, config: ConfigurationManager):
        """Initialize resource namer
        
        Args:
            config: ConfigurationManager instance
        """
        self.config = config
        self.prefix = config.get_required('project.prefix')
        self.environment = config.get_required('environment.name')
        self.account_id = config.get_required('environment.account_id')
        self.region = config.get_required('environment.region')
    
    def s3_bucket(self, purpose: str) -> str:
        """Generate S3 bucket name (globally unique)
        
        Args:
            purpose: Bucket purpose (e.g., 'data', 'logs', 'athena-results')
            
        Returns:
            S3 bucket name
            
        Example:
            >>> namer.s3_bucket('data')
            'sc-agent-dev-data-123456789012-us-east-1'
        """
        name = f"{self.prefix}-{purpose}-{self.account_id}-{self.region}"
        return self._truncate_name(name, 63)  # S3 bucket name limit
    
    def dynamodb_table(self, name: str) -> str:
        """Generate DynamoDB table name
        
        Args:
            name: Table name (e.g., 'sessions', 'memory')
            
        Returns:
            DynamoDB table name
            
        Example:
            >>> namer.dynamodb_table('sessions')
            'sc-agent-dev-sessions'
        """
        return f"{self.prefix}-{name}"
    
    def lambda_function(self, name: str) -> str:
        """Generate Lambda function name
        
        Args:
            name: Function name (e.g., 'sql-executor', 'inventory-optimizer')
            
        Returns:
            Lambda function name
            
        Example:
            >>> namer.lambda_function('sql-executor')
            'sc-agent-dev-sql-executor'
        """
        return f"{self.prefix}-{name}"
    
    def iam_role(self, purpose: str) -> str:
        """Generate IAM role name
        
        Args:
            purpose: Role purpose (e.g., 'lambda-exec', 'api-gateway')
            
        Returns:
            IAM role name
            
        Example:
            >>> namer.iam_role('lambda-exec')
            'sc-agent-dev-lambda-exec'
        """
        return f"{self.prefix}-{purpose}"
    
    def api_gateway(self, name: str) -> str:
        """Generate API Gateway name
        
        Args:
            name: API name
            
        Returns:
            API Gateway name
        """
        return f"{self.prefix}-{name}"
    
    def cloudwatch_log_group(self, service: str) -> str:
        """Generate CloudWatch log group name
        
        Args:
            service: Service name (e.g., 'lambda/sql-executor')
            
        Returns:
            Log group name
            
        Example:
            >>> namer.cloudwatch_log_group('lambda/sql-executor')
            '/aws/lambda/sc-agent-dev-sql-executor'
        """
        if service.startswith('lambda/'):
            function_name = service[7:]  # Remove 'lambda/' prefix
            return f"/aws/lambda/{self.lambda_function(function_name)}"
        return f"/aws/{self.prefix}/{service}"
    
    def parameter_store_path(self, parameter: str) -> str:
        """Generate Parameter Store parameter path
        
        Args:
            parameter: Parameter name
            
        Returns:
            Parameter Store path
            
        Example:
            >>> namer.parameter_store_path('database-url')
            '/sc-agent-dev/database-url'
        """
        return f"/{self.prefix}/{parameter}"
    
    def secrets_manager_name(self, secret: str) -> str:
        """Generate Secrets Manager secret name
        
        Args:
            secret: Secret name
            
        Returns:
            Secrets Manager secret name
            
        Example:
            >>> namer.secrets_manager_name('api-key')
            'sc-agent-dev/api-key'
        """
        return f"{self.prefix}/{secret}"
    
    def _truncate_name(self, name: str, max_length: int) -> str:
        """Truncate name to max length while maintaining uniqueness
        
        If truncation is needed, adds a hash suffix to ensure uniqueness.
        """
        if len(name) <= max_length:
            return name
        
        # Calculate hash of full name
        import hashlib
        name_hash = hashlib.md5(name.encode()).hexdigest()[:8]
        
        # Truncate and add hash
        available_length = max_length - len(name_hash) - 1  # -1 for separator
        truncated = name[:available_length]
        
        return f"{truncated}-{name_hash}"
    
    def __repr__(self) -> str:
        return f"ResourceNamer(prefix='{self.prefix}', environment='{self.environment}')"


class TagManager:
    """Manage consistent resource tagging across all AWS resources
    
    Generates standard tags and validates custom tags according to
    organizational policies and AWS best practices.
    """
    
    def __init__(self, config: ConfigurationManager):
        """Initialize tag manager
        
        Args:
            config: ConfigurationManager instance
        """
        self.config = config
        self._standard_tags = self._generate_standard_tags()
        self._custom_tags = self._load_custom_tags()
        self._all_tags = {**self._standard_tags, **self._custom_tags}
    
    def _generate_standard_tags(self) -> Dict[str, str]:
        """Generate standard tags required for all resources
        
        Returns:
            Dictionary of standard tags
        """
        return {
            'Project': self.config.get('project.name', 'supply-chain-agent'),
            'Environment': self.config.get('environment.name'),
            'ManagedBy': 'CDK',
            'Owner': self.config.get('project.owner', 'platform-team'),
            'CostCenter': self.config.get('project.cost_center', 'supply-chain'),
            'Region': self.config.get('environment.region'),
            'AccountId': self.config.get('environment.account_id')
        }
    
    def _load_custom_tags(self) -> Dict[str, str]:
        """Load custom tags from configuration
        
        Returns:
            Dictionary of custom tags
        """
        custom_tags = self.config.get('tags.custom', {})
        
        # Validate custom tags
        validated_tags = {}
        for key, value in custom_tags.items():
            if self._validate_tag(key, value):
                validated_tags[key] = str(value)
            else:
                print(f"Warning: Invalid tag '{key}={value}' - skipping")
        
        return validated_tags
    
    def _validate_tag(self, key: str, value: str) -> bool:
        """Validate tag key and value according to AWS requirements
        
        AWS Tag Requirements:
        - Keys: 1-128 characters, case-sensitive
        - Values: 0-256 characters
        - Allowed characters: letters, numbers, spaces, and +-=._:/@
        
        Args:
            key: Tag key
            value: Tag value
            
        Returns:
            True if valid, False otherwise
        """
        import re
        
        # Check key length
        if not key or len(key) > 128:
            return False
        
        # Check value length
        if len(str(value)) > 256:
            return False
        
        # Check allowed characters (AWS tag pattern)
        tag_pattern = re.compile(r'^[\w\s\+\-=\._:/@]*$')
        
        if not tag_pattern.match(key):
            return False
        
        if not tag_pattern.match(str(value)):
            return False
        
        # Check for reserved prefixes
        reserved_prefixes = ['aws:', 'AWS:']
        for prefix in reserved_prefixes:
            if key.startswith(prefix):
                return False
        
        return True
    
    def get_tags(self, additional_tags: Dict[str, str] = None) -> Dict[str, str]:
        """Get all tags with optional additional tags
        
        Args:
            additional_tags: Optional dictionary of additional tags to merge
            
        Returns:
            Complete dictionary of tags
            
        Example:
            >>> tag_manager.get_tags({'Component': 'Lambda'})
            {'Project': 'supply-chain-agent', 'Environment': 'dev', ..., 'Component': 'Lambda'}
        """
        tags = self._all_tags.copy()
        
        if additional_tags:
            # Validate and merge additional tags
            for key, value in additional_tags.items():
                if self._validate_tag(key, value):
                    tags[key] = str(value)
                else:
                    print(f"Warning: Invalid additional tag '{key}={value}' - skipping")
        
        return tags
    
    def get_standard_tags(self) -> Dict[str, str]:
        """Get only standard tags
        
        Returns:
            Dictionary of standard tags
        """
        return self._standard_tags.copy()
    
    def get_custom_tags(self) -> Dict[str, str]:
        """Get only custom tags from configuration
        
        Returns:
            Dictionary of custom tags
        """
        return self._custom_tags.copy()
    
    def get_cdk_tags(self, additional_tags: Dict[str, str] = None) -> Dict[str, str]:
        """Get tags formatted for CDK Tags.of() usage
        
        Args:
            additional_tags: Optional dictionary of additional tags
            
        Returns:
            Dictionary of tags ready for CDK
        """
        return self.get_tags(additional_tags)
    
    def validate_required_tags(self, tags: Dict[str, str]) -> tuple[bool, List[str]]:
        """Validate that all required tags are present
        
        Args:
            tags: Dictionary of tags to validate
            
        Returns:
            Tuple of (is_valid, list_of_missing_tags)
        """
        required_tag_keys = self.config.get('tags.required', [
            'Project', 'Environment', 'ManagedBy', 'Owner', 'CostCenter'
        ])
        
        missing_tags = []
        for required_key in required_tag_keys:
            if required_key not in tags:
                missing_tags.append(required_key)
        
        return (len(missing_tags) == 0, missing_tags)
    
    def format_tags_for_cloudformation(self, additional_tags: Dict[str, str] = None) -> List[Dict[str, str]]:
        """Format tags for CloudFormation template
        
        Args:
            additional_tags: Optional dictionary of additional tags
            
        Returns:
            List of tag dictionaries in CloudFormation format
            
        Example:
            >>> tag_manager.format_tags_for_cloudformation()
            [{'Key': 'Project', 'Value': 'supply-chain-agent'}, ...]
        """
        tags = self.get_tags(additional_tags)
        return [{'Key': k, 'Value': v} for k, v in tags.items()]
    
    def get_cost_allocation_tags(self) -> Dict[str, str]:
        """Get tags specifically for cost allocation
        
        Returns:
            Dictionary of cost allocation tags
        """
        cost_tags = {
            'CostCenter': self._standard_tags.get('CostCenter'),
            'Environment': self._standard_tags.get('Environment'),
            'Project': self._standard_tags.get('Project'),
            'Owner': self._standard_tags.get('Owner')
        }
        
        # Add any custom cost-related tags
        for key, value in self._custom_tags.items():
            if 'cost' in key.lower() or 'billing' in key.lower():
                cost_tags[key] = value
        
        return cost_tags
    
    def __repr__(self) -> str:
        return f"TagManager(tags={len(self._all_tags)})"


# Convenience function for quick access
def load_config(environment: str = None) -> ConfigurationManager:
    """Load configuration for specified environment
    
    Args:
        environment: Environment name (dev, staging, prod)
        
    Returns:
        ConfigurationManager instance
    """
    return ConfigurationManager(environment=environment)
