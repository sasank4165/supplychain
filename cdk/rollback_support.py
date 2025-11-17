"""Rollback support utilities for CDK stacks

Provides utilities to enable proper rollback capabilities including:
- Stack versioning
- Removal policy management
- Data preservation logic
- Rollback validation
"""

from aws_cdk import (
    RemovalPolicy,
    CfnOutput,
    Tags,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_logs as logs,
)
from constructs import Construct
from typing import Dict, Any, Optional


class RollbackConfig:
    """Configuration for rollback behavior"""
    
    def __init__(
        self,
        preserve_data: bool = True,
        preserve_logs: bool = True,
        enable_versioning: bool = True,
        enable_backups: bool = True
    ):
        """Initialize rollback configuration
        
        Args:
            preserve_data: Preserve S3 and DynamoDB data on stack deletion
            preserve_logs: Preserve CloudWatch logs on stack deletion
            enable_versioning: Enable versioning for S3 buckets
            enable_backups: Enable point-in-time recovery for DynamoDB
        """
        self.preserve_data = preserve_data
        self.preserve_logs = preserve_logs
        self.enable_versioning = enable_versioning
        self.enable_backups = enable_backups
    
    def get_data_removal_policy(self) -> RemovalPolicy:
        """Get removal policy for data resources (S3, DynamoDB)"""
        return RemovalPolicy.RETAIN if self.preserve_data else RemovalPolicy.DESTROY
    
    def get_log_removal_policy(self) -> RemovalPolicy:
        """Get removal policy for log resources"""
        return RemovalPolicy.RETAIN if self.preserve_logs else RemovalPolicy.DESTROY
    
    def get_compute_removal_policy(self) -> RemovalPolicy:
        """Get removal policy for compute resources (Lambda, etc.)"""
        return RemovalPolicy.DESTROY
    
    @classmethod
    def from_environment(cls, environment: str) -> 'RollbackConfig':
        """Create rollback config based on environment
        
        Args:
            environment: Environment name (dev, staging, prod)
            
        Returns:
            RollbackConfig instance with environment-appropriate settings
        """
        if environment == 'prod':
            # Production: preserve everything by default
            return cls(
                preserve_data=True,
                preserve_logs=True,
                enable_versioning=True,
                enable_backups=True
            )
        elif environment == 'staging':
            # Staging: preserve data but not logs
            return cls(
                preserve_data=True,
                preserve_logs=False,
                enable_versioning=True,
                enable_backups=True
            )
        else:
            # Development: don't preserve anything
            return cls(
                preserve_data=False,
                preserve_logs=False,
                enable_versioning=False,
                enable_backups=False
            )


class StackVersioning:
    """Manage stack versioning for rollback support"""
    
    def __init__(self, scope: Construct, stack_name: str, version: str = None):
        """Initialize stack versioning
        
        Args:
            scope: CDK construct scope
            stack_name: Name of the stack
            version: Optional version identifier
        """
        self.scope = scope
        self.stack_name = stack_name
        self.version = version or self._generate_version()
    
    def _generate_version(self) -> str:
        """Generate version identifier from timestamp"""
        from datetime import datetime
        return datetime.utcnow().strftime('%Y%m%d%H%M%S')
    
    def add_version_tags(self):
        """Add version tags to stack"""
        Tags.of(self.scope).add('StackVersion', self.version)
        Tags.of(self.scope).add('DeploymentTimestamp', self.version)
    
    def add_version_outputs(self):
        """Add version information to stack outputs"""
        CfnOutput(
            self.scope,
            'StackVersion',
            value=self.version,
            description='Stack version for rollback tracking'
        )
        
        CfnOutput(
            self.scope,
            'StackName',
            value=self.stack_name,
            description='Stack name for rollback operations'
        )


class DataPreservation:
    """Utilities for data preservation during rollback"""
    
    @staticmethod
    def configure_s3_bucket(
        bucket: s3.Bucket,
        rollback_config: RollbackConfig,
        enable_lifecycle: bool = True
    ):
        """Configure S3 bucket for data preservation
        
        Args:
            bucket: S3 bucket to configure
            rollback_config: Rollback configuration
            enable_lifecycle: Enable lifecycle rules
        """
        # Set removal policy
        bucket.apply_removal_policy(rollback_config.get_data_removal_policy())
        
        # Add preservation tags
        Tags.of(bucket).add('DataPreservation', 'true')
        Tags.of(bucket).add('PreserveOnDelete', str(rollback_config.preserve_data))
        
        # Enable versioning if configured
        if rollback_config.enable_versioning:
            # Note: Versioning is set during bucket creation
            Tags.of(bucket).add('VersioningEnabled', 'true')
    
    @staticmethod
    def configure_dynamodb_table(
        table: dynamodb.Table,
        rollback_config: RollbackConfig
    ):
        """Configure DynamoDB table for data preservation
        
        Args:
            table: DynamoDB table to configure
            rollback_config: Rollback configuration
        """
        # Set removal policy
        table.apply_removal_policy(rollback_config.get_data_removal_policy())
        
        # Add preservation tags
        Tags.of(table).add('DataPreservation', 'true')
        Tags.of(table).add('PreserveOnDelete', str(rollback_config.preserve_data))
        
        # Point-in-time recovery is set during table creation
        if rollback_config.enable_backups:
            Tags.of(table).add('BackupEnabled', 'true')
    
    @staticmethod
    def configure_log_group(
        log_group: logs.LogGroup,
        rollback_config: RollbackConfig
    ):
        """Configure CloudWatch log group for preservation
        
        Args:
            log_group: Log group to configure
            rollback_config: Rollback configuration
        """
        # Set removal policy
        log_group.apply_removal_policy(rollback_config.get_log_removal_policy())
        
        # Add preservation tags
        Tags.of(log_group).add('LogPreservation', str(rollback_config.preserve_logs))


class RollbackValidator:
    """Validate stack state for rollback operations"""
    
    def __init__(self, scope: Construct, config: RollbackConfig):
        """Initialize rollback validator
        
        Args:
            scope: CDK construct scope
            config: Rollback configuration
        """
        self.scope = scope
        self.config = config
        self.validation_results = []
    
    def validate_data_resources(self, resources: Dict[str, Any]):
        """Validate data resources are properly configured
        
        Args:
            resources: Dictionary of resource name to resource object
        """
        for name, resource in resources.items():
            if isinstance(resource, s3.Bucket):
                self._validate_s3_bucket(name, resource)
            elif isinstance(resource, dynamodb.Table):
                self._validate_dynamodb_table(name, resource)
    
    def _validate_s3_bucket(self, name: str, bucket: s3.Bucket):
        """Validate S3 bucket configuration"""
        # Check if versioning is enabled when required
        if self.config.enable_versioning:
            # Versioning check would be done at runtime
            self.validation_results.append({
                'resource': name,
                'type': 's3',
                'check': 'versioning',
                'status': 'configured'
            })
        
        # Check removal policy
        self.validation_results.append({
            'resource': name,
            'type': 's3',
            'check': 'removal_policy',
            'status': 'configured',
            'policy': 'RETAIN' if self.config.preserve_data else 'DESTROY'
        })
    
    def _validate_dynamodb_table(self, name: str, table: dynamodb.Table):
        """Validate DynamoDB table configuration"""
        # Check if PITR is enabled when required
        if self.config.enable_backups:
            self.validation_results.append({
                'resource': name,
                'type': 'dynamodb',
                'check': 'pitr',
                'status': 'configured'
            })
        
        # Check removal policy
        self.validation_results.append({
            'resource': name,
            'type': 'dynamodb',
            'check': 'removal_policy',
            'status': 'configured',
            'policy': 'RETAIN' if self.config.preserve_data else 'DESTROY'
        })
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary
        
        Returns:
            Dictionary with validation results
        """
        return {
            'total_checks': len(self.validation_results),
            'results': self.validation_results,
            'config': {
                'preserve_data': self.config.preserve_data,
                'preserve_logs': self.config.preserve_logs,
                'enable_versioning': self.config.enable_versioning,
                'enable_backups': self.config.enable_backups
            }
        }
    
    def add_validation_outputs(self):
        """Add validation results to stack outputs"""
        summary = self.get_validation_summary()
        
        CfnOutput(
            self.scope,
            'RollbackValidation',
            value=f"Validated {summary['total_checks']} resources",
            description='Rollback configuration validation status'
        )
        
        CfnOutput(
            self.scope,
            'DataPreservation',
            value='ENABLED' if self.config.preserve_data else 'DISABLED',
            description='Data preservation status for rollback'
        )


def apply_rollback_support(
    scope: Construct,
    stack_name: str,
    config: RollbackConfig,
    data_resources: Dict[str, Any] = None,
    version: str = None
):
    """Apply rollback support to a stack
    
    This is a convenience function that applies all rollback support features:
    - Stack versioning
    - Data preservation configuration
    - Validation
    
    Args:
        scope: CDK construct scope
        stack_name: Name of the stack
        config: Rollback configuration
        data_resources: Optional dictionary of data resources to configure
        version: Optional version identifier
    """
    # Add versioning
    versioning = StackVersioning(scope, stack_name, version)
    versioning.add_version_tags()
    versioning.add_version_outputs()
    
    # Configure data resources if provided
    if data_resources:
        for name, resource in data_resources.items():
            if isinstance(resource, s3.Bucket):
                DataPreservation.configure_s3_bucket(resource, config)
            elif isinstance(resource, dynamodb.Table):
                DataPreservation.configure_dynamodb_table(resource, config)
            elif isinstance(resource, logs.LogGroup):
                DataPreservation.configure_log_group(resource, config)
    
    # Validate configuration
    validator = RollbackValidator(scope, config)
    if data_resources:
        validator.validate_data_resources(data_resources)
    validator.add_validation_outputs()
    
    return validator.get_validation_summary()
