#!/usr/bin/env python3
"""Initialize secrets and parameters for a new environment

This script sets up all required secrets in AWS Secrets Manager and
parameters in AWS Systems Manager Parameter Store for a new environment.

Usage:
    python scripts/init-secrets.py --environment dev --config config/dev.yaml
    
    # Dry run (show what would be created)
    python scripts/init-secrets.py --environment dev --config config/dev.yaml --dry-run
    
    # Force overwrite existing secrets/parameters
    python scripts/init-secrets.py --environment dev --config config/dev.yaml --force
"""

import argparse
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_manager import ConfigurationManager, ResourceNamer
from secrets_manager import SecretsManager


def init_parameters(
    secrets_mgr: SecretsManager,
    config: ConfigurationManager,
    namer: ResourceNamer,
    dry_run: bool = False,
    force: bool = False
) -> int:
    """Initialize parameters in Parameter Store
    
    Args:
        secrets_mgr: SecretsManager instance
        config: ConfigurationManager instance
        namer: ResourceNamer instance
        dry_run: If True, only show what would be created
        force: If True, overwrite existing parameters
        
    Returns:
        Number of parameters created/updated
    """
    parameters = {
        # Athena configuration
        'athena/database': config.get('data.athena_database', 'supply_chain_db'),
        'athena/catalog': config.get('data.glue_catalog', 'AwsDataCatalog'),
        'athena/output-location': f"s3://{namer.s3_bucket('athena-results')}/",
        
        # DynamoDB tables
        'dynamodb/session-table': namer.dynamodb_table('sessions'),
        'dynamodb/memory-table': namer.dynamodb_table('memory'),
        
        # Lambda functions
        'lambda/sql-executor': namer.lambda_function('sql-executor'),
        'lambda/inventory-optimizer': namer.lambda_function('inventory-optimizer'),
        'lambda/logistics-optimizer': namer.lambda_function('logistics-optimizer'),
        'lambda/supplier-analyzer': namer.lambda_function('supplier-analyzer'),
        
        # Bedrock configuration
        'bedrock/model-id': config.get('agents.default_model'),
        
        # Application configuration
        'app/environment': config.get('environment.name'),
        'app/region': config.get('environment.region'),
        'app/prefix': config.get('project.prefix'),
    }
    
    count = 0
    for param_name, param_value in parameters.items():
        if dry_run:
            print(f"[DRY RUN] Would create parameter: {param_name} = {param_value}")
            count += 1
        else:
            try:
                secrets_mgr.put_parameter(
                    name=param_name,
                    value=str(param_value),
                    description=f"Auto-generated for {config.environment} environment",
                    overwrite=force
                )
                print(f"✓ Created parameter: {param_name}")
                count += 1
            except Exception as e:
                print(f"✗ Failed to create parameter {param_name}: {e}")
    
    return count


def init_secrets(
    secrets_mgr: SecretsManager,
    config: ConfigurationManager,
    dry_run: bool = False,
    force: bool = False
) -> int:
    """Initialize secrets in Secrets Manager
    
    Note: This creates placeholder secrets. You should update them with
    actual values after creation.
    
    Args:
        secrets_mgr: SecretsManager instance
        config: ConfigurationManager instance
        dry_run: If True, only show what would be created
        force: If True, overwrite existing secrets
        
    Returns:
        Number of secrets created/updated
    """
    # These are placeholder secrets - should be updated with real values
    secrets = {
        'database/connection-string': 'PLACEHOLDER - Update with actual database connection string',
        'api/external-api-key': 'PLACEHOLDER - Update with actual API key',
        'cognito/user-pool-id': config.get('auth.user_pool_id', 'PLACEHOLDER'),
        'cognito/client-id': config.get('auth.client_id', 'PLACEHOLDER'),
    }
    
    count = 0
    for secret_name, secret_value in secrets.items():
        if dry_run:
            print(f"[DRY RUN] Would create secret: {secret_name}")
            count += 1
        else:
            try:
                if not force:
                    # Check if secret exists
                    try:
                        secrets_mgr.get_secret(secret_name, use_cache=False)
                        print(f"⊘ Secret already exists (use --force to overwrite): {secret_name}")
                        continue
                    except:
                        pass  # Secret doesn't exist, create it
                
                secrets_mgr.put_secret(
                    name=secret_name,
                    value=secret_value,
                    description=f"Auto-generated for {config.environment} environment"
                )
                print(f"✓ Created secret: {secret_name}")
                count += 1
            except Exception as e:
                print(f"✗ Failed to create secret {secret_name}: {e}")
    
    return count


def validate_aws_credentials():
    """Validate AWS credentials are configured"""
    import boto3
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✓ AWS credentials valid")
        print(f"  Account: {identity['Account']}")
        print(f"  User/Role: {identity['Arn']}")
        return True
    except Exception as e:
        print(f"✗ AWS credentials not configured or invalid: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Initialize secrets and parameters for a new environment',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize dev environment
  python scripts/init-secrets.py --environment dev --config config/dev.yaml
  
  # Dry run to see what would be created
  python scripts/init-secrets.py --environment dev --config config/dev.yaml --dry-run
  
  # Force overwrite existing values
  python scripts/init-secrets.py --environment dev --config config/dev.yaml --force
        """
    )
    
    parser.add_argument(
        '--environment',
        required=True,
        help='Environment name (dev, staging, prod)'
    )
    
    parser.add_argument(
        '--config',
        help='Path to configuration file (default: config/{environment}.yaml)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be created without actually creating'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing secrets and parameters'
    )
    
    parser.add_argument(
        '--skip-secrets',
        action='store_true',
        help='Skip creating secrets (only create parameters)'
    )
    
    parser.add_argument(
        '--skip-parameters',
        action='store_true',
        help='Skip creating parameters (only create secrets)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Initialize Secrets and Parameters")
    print("=" * 70)
    print()
    
    # Validate AWS credentials
    if not args.dry_run:
        if not validate_aws_credentials():
            print("\nPlease configure AWS credentials and try again.")
            return 1
        print()
    
    # Load configuration
    try:
        config_path = args.config or f"config/{args.environment}.yaml"
        print(f"Loading configuration from: {config_path}")
        
        config = ConfigurationManager(environment=args.environment)
        namer = ResourceNamer(config)
        secrets_mgr = SecretsManager(
            region=config.get('environment.region'),
            prefix=config.get('project.prefix')
        )
        
        print(f"✓ Configuration loaded")
        print(f"  Environment: {config.environment}")
        print(f"  Region: {config.get('environment.region')}")
        print(f"  Prefix: {config.get('project.prefix')}")
        print()
        
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return 1
    
    # Initialize parameters
    if not args.skip_parameters:
        print("-" * 70)
        print("Creating Parameters in Parameter Store")
        print("-" * 70)
        param_count = init_parameters(secrets_mgr, config, namer, args.dry_run, args.force)
        print(f"\n{'Would create' if args.dry_run else 'Created'} {param_count} parameters\n")
    
    # Initialize secrets
    if not args.skip_secrets:
        print("-" * 70)
        print("Creating Secrets in Secrets Manager")
        print("-" * 70)
        secret_count = init_secrets(secrets_mgr, config, args.dry_run, args.force)
        print(f"\n{'Would create' if args.dry_run else 'Created'} {secret_count} secrets\n")
    
    # Summary
    print("=" * 70)
    if args.dry_run:
        print("Dry run complete. No changes were made.")
    else:
        print("Initialization complete!")
        print()
        print("IMPORTANT: Update placeholder secrets with actual values:")
        print(f"  aws secretsmanager list-secrets --filters Key=name,Values={config.get('project.prefix')}")
        print()
        print("To update a secret:")
        print(f"  aws secretsmanager update-secret --secret-id <secret-name> --secret-string '<value>'")
    print("=" * 70)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
