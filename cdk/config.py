"""Configuration for CDK deployment - Loads from YAML files"""
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path to import config_manager
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_manager import ConfigurationManager, ResourceNamer, TagManager


class CDKConfig:
    """CDK-specific configuration wrapper
    
    Provides convenient access to configuration values for CDK stacks.
    """
    
    def __init__(self, environment: str = None):
        """Initialize CDK configuration
        
        Args:
            environment: Environment name (dev, staging, prod)
        """
        # Determine config path relative to this file
        config_path = Path(__file__).parent.parent / "config"
        
        self.config_manager = ConfigurationManager(
            environment=environment,
            config_path=str(config_path),
            use_secrets=False  # Don't use secrets during CDK synthesis
        )
        self.resource_namer = ResourceNamer(self.config_manager)
        self.tag_manager = TagManager(self.config_manager)
    
    @property
    def environment_name(self) -> str:
        """Get environment name"""
        return self.config_manager.get_required('environment.name')
    
    @property
    def account_id(self) -> str:
        """Get AWS account ID"""
        return self.config_manager.get_required('environment.account_id')
    
    @property
    def region(self) -> str:
        """Get AWS region"""
        return self.config_manager.get_required('environment.region')
    
    @property
    def project_prefix(self) -> str:
        """Get project prefix for resource naming"""
        return self.config_manager.get_required('project.prefix')
    
    # Feature flags
    @property
    def vpc_enabled(self) -> bool:
        """Check if VPC deployment is enabled"""
        return self.config_manager.get('features.vpc_enabled', False)
    
    @property
    def waf_enabled(self) -> bool:
        """Check if WAF is enabled"""
        return self.config_manager.get('features.waf_enabled', False)
    
    @property
    def multi_az(self) -> bool:
        """Check if multi-AZ deployment is enabled"""
        return self.config_manager.get('features.multi_az', False)
    
    @property
    def xray_tracing(self) -> bool:
        """Check if X-Ray tracing is enabled"""
        return self.config_manager.get('features.xray_tracing', False)
    
    @property
    def backup_enabled(self) -> bool:
        """Check if backups are enabled"""
        return self.config_manager.get('features.backup_enabled', True)
    
    # Resource configuration
    @property
    def lambda_memory_mb(self) -> int:
        """Get Lambda memory size in MB"""
        return self.config_manager.get('resources.lambda.memory_mb', 512)
    
    @property
    def lambda_timeout_seconds(self) -> int:
        """Get Lambda timeout in seconds"""
        return self.config_manager.get('resources.lambda.timeout_seconds', 180)
    
    @property
    def lambda_reserved_concurrency(self) -> int:
        """Get Lambda reserved concurrency"""
        return self.config_manager.get('resources.lambda.reserved_concurrency', 10)
    
    @property
    def lambda_architecture(self) -> str:
        """Get Lambda architecture (arm64 or x86_64)"""
        return self.config_manager.get('resources.lambda.architecture', 'arm64')
    
    @property
    def lambda_provisioned_concurrency(self) -> int:
        """Get Lambda provisioned concurrency (0 means disabled)"""
        return self.config_manager.get('resources.lambda.provisioned_concurrency', 0)
    
    @property
    def dynamodb_billing_mode(self) -> str:
        """Get DynamoDB billing mode"""
        return self.config_manager.get('resources.dynamodb.billing_mode', 'PAY_PER_REQUEST')
    
    @property
    def dynamodb_pitr_enabled(self) -> bool:
        """Check if DynamoDB point-in-time recovery is enabled"""
        return self.config_manager.get('resources.dynamodb.point_in_time_recovery', True)
    
    @property
    def dynamodb_read_capacity(self) -> int:
        """Get DynamoDB read capacity units (only used if billing_mode is PROVISIONED)"""
        return self.config_manager.get('resources.dynamodb.read_capacity_units', 5)
    
    @property
    def dynamodb_write_capacity(self) -> int:
        """Get DynamoDB write capacity units (only used if billing_mode is PROVISIONED)"""
        return self.config_manager.get('resources.dynamodb.write_capacity_units', 5)
    
    @property
    def log_retention_days(self) -> int:
        """Get CloudWatch Logs retention in days"""
        return self.config_manager.get('resources.logs.retention_days', 7)
    
    @property
    def backup_retention_days(self) -> int:
        """Get backup retention in days"""
        return self.config_manager.get('resources.backup.retention_days', 7)
    
    # Networking configuration
    @property
    def vpc_cidr(self) -> str:
        """Get VPC CIDR block"""
        return self.config_manager.get('networking.vpc_cidr', '10.0.0.0/16')
    
    @property
    def nat_gateways(self) -> int:
        """Get number of NAT gateways"""
        return self.config_manager.get('networking.nat_gateways', 1)
    
    @property
    def max_azs(self) -> int:
        """Get maximum number of availability zones"""
        return 3 if self.multi_az else 2
    
    # API configuration
    @property
    def api_throttle_rate_limit(self) -> int:
        """Get API Gateway throttle rate limit"""
        return self.config_manager.get('api.throttle_rate_limit', 50)
    
    @property
    def api_throttle_burst_limit(self) -> int:
        """Get API Gateway throttle burst limit"""
        return self.config_manager.get('api.throttle_burst_limit', 100)
    
    @property
    def cors_origins(self) -> list:
        """Get CORS allowed origins"""
        return self.config_manager.get('api.cors_origins', ['http://localhost:8501'])
    
    # Monitoring configuration
    @property
    def alarm_email(self) -> str:
        """Get alarm notification email"""
        return self.config_manager.get('monitoring.alarm_email', 'admin@example.com')
    
    @property
    def dashboard_enabled(self) -> bool:
        """Check if CloudWatch dashboard is enabled"""
        return self.config_manager.get('monitoring.dashboard_enabled', True)
    
    # Data configuration
    @property
    def athena_database(self) -> str:
        """Get Athena database name"""
        return self.config_manager.get('data.athena_database', 'supply_chain_db')
    
    @property
    def glue_catalog(self) -> str:
        """Get Glue catalog name"""
        return self.config_manager.get('data.glue_catalog', 'AwsDataCatalog')
    
    def get_tags(self, additional_tags: Dict[str, str] = None) -> Dict[str, str]:
        """Get all resource tags with optional additional tags
        
        Args:
            additional_tags: Optional dictionary of additional tags to merge
            
        Returns:
            Complete dictionary of tags
        """
        return self.tag_manager.get_tags(additional_tags)
    
    def get_standard_tags(self) -> Dict[str, str]:
        """Get only standard tags"""
        return self.tag_manager.get_standard_tags()
    
    def get_custom_tags(self) -> Dict[str, str]:
        """Get only custom tags"""
        return self.tag_manager.get_custom_tags()
    
    def validate_tags(self, tags: Dict[str, str]) -> tuple:
        """Validate that all required tags are present
        
        Args:
            tags: Dictionary of tags to validate
            
        Returns:
            Tuple of (is_valid, list_of_missing_tags)
        """
        return self.tag_manager.validate_required_tags(tags)
    
    def get_resource_name(self, resource_type: str, name: str = None) -> str:
        """Get standardized resource name
        
        Args:
            resource_type: Type of resource (s3, dynamodb, lambda, etc.)
            name: Optional name component
            
        Returns:
            Standardized resource name
        """
        if resource_type == 's3':
            return self.resource_namer.s3_bucket(name or 'data')
        elif resource_type == 'dynamodb':
            return self.resource_namer.dynamodb_table(name or 'table')
        elif resource_type == 'lambda':
            return self.resource_namer.lambda_function(name or 'function')
        elif resource_type == 'iam':
            return self.resource_namer.iam_role(name or 'role')
        elif resource_type == 'api':
            return self.resource_namer.api_gateway(name or 'api')
        else:
            return f"{self.project_prefix}-{name}" if name else self.project_prefix
    
    def get_all(self) -> Dict[str, Any]:
        """Get complete configuration"""
        return self.config_manager.get_all()


def load_cdk_config(environment: str = None) -> CDKConfig:
    """Load CDK configuration for specified environment
    
    Args:
        environment: Environment name (dev, staging, prod).
                    If None, reads from ENVIRONMENT env var or defaults to 'dev'
    
    Returns:
        CDKConfig instance
    """
    return CDKConfig(environment=environment)
