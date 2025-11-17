#!/usr/bin/env python3
"""Configuration Validation Script

Validates configuration files before deployment to catch errors early.
Checks:
- YAML syntax
- JSON schema compliance
- AWS connectivity
- Required permissions
- Resource naming conflicts
"""

import sys
import argparse
import yaml
import json
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_manager import ConfigurationManager, ConfigurationError, ResourceNamer


class ValidationResult:
    """Validation result container"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
    
    def add_error(self, message: str):
        """Add error message"""
        self.errors.append(f"❌ ERROR: {message}")
    
    def add_warning(self, message: str):
        """Add warning message"""
        self.warnings.append(f"⚠️  WARNING: {message}")
    
    def add_info(self, message: str):
        """Add info message"""
        self.info.append(f"ℹ️  INFO: {message}")
    
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)"""
        return len(self.errors) == 0
    
    def print_results(self):
        """Print validation results"""
        print("\n" + "="*70)
        print("CONFIGURATION VALIDATION RESULTS")
        print("="*70 + "\n")
        
        if self.info:
            for msg in self.info:
                print(msg)
            print()
        
        if self.warnings:
            for msg in self.warnings:
                print(msg)
            print()
        
        if self.errors:
            for msg in self.errors:
                print(msg)
            print()
        
        if self.is_valid():
            print("✅ Configuration validation PASSED")
        else:
            print(f"❌ Configuration validation FAILED with {len(self.errors)} error(s)")
        
        print("="*70 + "\n")


def validate_yaml_syntax(config_file: Path, result: ValidationResult):
    """Validate YAML syntax"""
    try:
        with open(config_file, 'r') as f:
            yaml.safe_load(f)
        result.add_info(f"YAML syntax valid: {config_file}")
    except yaml.YAMLError as e:
        result.add_error(f"Invalid YAML syntax in {config_file}: {str(e)}")
    except FileNotFoundError:
        result.add_error(f"Configuration file not found: {config_file}")


def validate_schema(environment: str, result: ValidationResult):
    """Validate configuration against JSON schema"""
    try:
        config = ConfigurationManager(environment=environment)
        result.add_info(f"Schema validation passed for environment: {environment}")
        return config
    except ConfigurationError as e:
        result.add_error(f"Schema validation failed: {str(e)}")
        return None
    except Exception as e:
        result.add_error(f"Unexpected error during validation: {str(e)}")
        return None


def validate_aws_connectivity(config: ConfigurationManager, result: ValidationResult):
    """Validate AWS connectivity and credentials"""
    try:
        import boto3
        
        # Test STS connectivity
        sts = boto3.client('sts', region_name=config.get('environment.region'))
        identity = sts.get_caller_identity()
        
        result.add_info(f"AWS Account: {identity['Account']}")
        result.add_info(f"AWS User/Role: {identity['Arn']}")
        
        # Verify account ID matches if not auto
        config_account = config.get('environment.account_id')
        if config_account != 'auto' and config_account != identity['Account']:
            result.add_warning(
                f"Account ID mismatch: config={config_account}, actual={identity['Account']}"
            )
        
    except Exception as e:
        result.add_error(f"AWS connectivity check failed: {str(e)}")


def validate_bedrock_access(config: ConfigurationManager, result: ValidationResult):
    """Validate Amazon Bedrock model access"""
    try:
        import boto3
        
        bedrock = boto3.client('bedrock', region_name=config.get('environment.region'))
        
        # List foundation models to verify access
        response = bedrock.list_foundation_models()
        
        # Check if configured model is available
        default_model = config.get('agents.default_model')
        available_models = [m['modelId'] for m in response.get('modelSummaries', [])]
        
        if default_model in available_models:
            result.add_info(f"Bedrock model access verified: {default_model}")
        else:
            result.add_warning(
                f"Configured model may not be available: {default_model}\n"
                f"  Available models: {len(available_models)}"
            )
        
    except Exception as e:
        result.add_warning(f"Bedrock access check failed: {str(e)}")


def validate_resource_names(config: ConfigurationManager, result: ValidationResult):
    """Validate resource naming conventions"""
    try:
        namer = ResourceNamer(config)
        
        # Test various resource names
        test_names = {
            'S3 Bucket (data)': namer.s3_bucket('data'),
            'S3 Bucket (logs)': namer.s3_bucket('logs'),
            'DynamoDB Table (sessions)': namer.dynamodb_table('sessions'),
            'Lambda Function (sql-executor)': namer.lambda_function('sql-executor'),
            'IAM Role (lambda-exec)': namer.iam_role('lambda-exec'),
        }
        
        result.add_info("Resource naming examples:")
        for resource_type, name in test_names.items():
            result.add_info(f"  {resource_type}: {name}")
        
        # Validate S3 bucket name constraints
        s3_bucket = namer.s3_bucket('data')
        if len(s3_bucket) > 63:
            result.add_error(f"S3 bucket name too long: {s3_bucket} ({len(s3_bucket)} chars)")
        if not s3_bucket.replace('-', '').replace('.', '').isalnum():
            result.add_error(f"S3 bucket name contains invalid characters: {s3_bucket}")
        
    except Exception as e:
        result.add_error(f"Resource naming validation failed: {str(e)}")


def validate_feature_flags(config: ConfigurationManager, result: ValidationResult):
    """Validate feature flag combinations"""
    vpc_enabled = config.get('features.vpc_enabled', False)
    multi_az = config.get('features.multi_az', False)
    
    if multi_az and not vpc_enabled:
        result.add_warning("Multi-AZ enabled but VPC disabled - multi-AZ requires VPC")
    
    waf_enabled = config.get('features.waf_enabled', False)
    environment = config.get('environment.name')
    
    if environment == 'prod' and not waf_enabled:
        result.add_warning("WAF disabled in production environment - consider enabling for security")
    
    if environment == 'dev' and waf_enabled:
        result.add_info("WAF enabled in dev environment - may increase costs")


def validate_resource_sizing(config: ConfigurationManager, result: ValidationResult):
    """Validate resource sizing is appropriate for environment"""
    environment = config.get('environment.name')
    lambda_memory = config.get('resources.lambda.memory_mb')
    lambda_concurrency = config.get('resources.lambda.reserved_concurrency')
    
    if environment == 'prod':
        if lambda_memory < 1024:
            result.add_warning(f"Lambda memory ({lambda_memory}MB) may be low for production")
        if lambda_concurrency < 50:
            result.add_warning(f"Lambda concurrency ({lambda_concurrency}) may be low for production")
    
    if environment == 'dev':
        if lambda_memory > 1024:
            result.add_info(f"Lambda memory ({lambda_memory}MB) is high for dev - consider reducing for cost savings")
        if lambda_concurrency > 20:
            result.add_info(f"Lambda concurrency ({lambda_concurrency}) is high for dev - consider reducing")


def validate_tags(config: ConfigurationManager, result: ValidationResult):
    """Validate resource tags"""
    tags = config.get_tags()
    
    required_tags = ['Project', 'Environment', 'ManagedBy', 'Owner', 'CostCenter']
    missing_tags = [tag for tag in required_tags if tag not in tags]
    
    if missing_tags:
        result.add_warning(f"Missing recommended tags: {', '.join(missing_tags)}")
    
    result.add_info(f"Resource tags configured: {len(tags)} tags")


def main():
    """Main validation function"""
    parser = argparse.ArgumentParser(
        description='Validate configuration before deployment',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate dev environment
  python validate-config.py --environment dev
  
  # Validate with AWS checks
  python validate-config.py --environment prod --check-aws
  
  # Validate all environments
  python validate-config.py --all
        """
    )
    
    parser.add_argument(
        '--environment', '-e',
        help='Environment to validate (dev, staging, prod)',
        default=None
    )
    
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Validate all environments'
    )
    
    parser.add_argument(
        '--check-aws',
        action='store_true',
        help='Perform AWS connectivity and permission checks'
    )
    
    parser.add_argument(
        '--config-path',
        default='config',
        help='Path to configuration directory (default: config)'
    )
    
    args = parser.parse_args()
    
    # Determine which environments to validate
    if args.all:
        environments = ['dev', 'staging', 'prod']
    elif args.environment:
        environments = [args.environment]
    else:
        # Try to detect from environment variable
        import os
        env = os.getenv('ENVIRONMENT', 'dev')
        environments = [env]
        print(f"No environment specified, using: {env}")
    
    # Validate each environment
    all_valid = True
    
    for env in environments:
        print(f"\n{'='*70}")
        print(f"Validating environment: {env}")
        print(f"{'='*70}")
        
        result = ValidationResult()
        config_file = Path(args.config_path) / f"{env}.yaml"
        
        # Step 1: Validate YAML syntax
        validate_yaml_syntax(config_file, result)
        
        # Step 2: Validate against schema
        config = validate_schema(env, result)
        
        if config:
            # Step 3: Validate resource naming
            validate_resource_names(config, result)
            
            # Step 4: Validate feature flags
            validate_feature_flags(config, result)
            
            # Step 5: Validate resource sizing
            validate_resource_sizing(config, result)
            
            # Step 6: Validate tags
            validate_tags(config, result)
            
            # Step 7: AWS checks (optional)
            if args.check_aws:
                validate_aws_connectivity(config, result)
                validate_bedrock_access(config, result)
        
        # Print results
        result.print_results()
        
        if not result.is_valid():
            all_valid = False
    
    # Exit with appropriate code
    sys.exit(0 if all_valid else 1)


if __name__ == '__main__':
    main()
