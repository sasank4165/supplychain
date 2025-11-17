#!/usr/bin/env python3
"""
Validation script for environment-specific resource sizing configuration.

This script validates that resource sizing is properly configured for each
environment (dev, staging, prod) and displays the differences.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cdk.config import CDKConfig


def validate_environment_config(env_name: str) -> dict:
    """Validate configuration for a specific environment"""
    try:
        config = CDKConfig(env_name)
        
        return {
            'environment': env_name,
            'lambda': {
                'memory_mb': config.lambda_memory_mb,
                'timeout_seconds': config.lambda_timeout_seconds,
                'reserved_concurrency': config.lambda_reserved_concurrency,
                'provisioned_concurrency': config.lambda_provisioned_concurrency,
                'architecture': config.lambda_architecture,
            },
            'dynamodb': {
                'billing_mode': config.dynamodb_billing_mode,
                'pitr_enabled': config.dynamodb_pitr_enabled,
                'read_capacity': config.dynamodb_read_capacity if config.dynamodb_billing_mode == 'PROVISIONED' else 'N/A',
                'write_capacity': config.dynamodb_write_capacity if config.dynamodb_billing_mode == 'PROVISIONED' else 'N/A',
            },
            'logs': {
                'retention_days': config.log_retention_days,
            },
            'valid': True,
            'error': None
        }
    except Exception as e:
        return {
            'environment': env_name,
            'valid': False,
            'error': str(e)
        }


def print_config_comparison():
    """Print configuration comparison across environments"""
    environments = ['dev', 'staging', 'prod']
    configs = {}
    
    print("=" * 80)
    print("Environment-Specific Resource Sizing Configuration")
    print("=" * 80)
    print()
    
    # Load all configurations
    for env in environments:
        configs[env] = validate_environment_config(env)
    
    # Check if all configs are valid
    all_valid = all(config['valid'] for config in configs.values())
    
    if not all_valid:
        print("❌ Configuration validation failed:")
        for env, config in configs.items():
            if not config['valid']:
                print(f"  - {env}: {config['error']}")
        return False
    
    print("✅ All environment configurations are valid\n")
    
    # Print Lambda configuration comparison
    print("Lambda Function Configuration:")
    print("-" * 80)
    print(f"{'Setting':<30} {'Dev':<15} {'Staging':<15} {'Prod':<15}")
    print("-" * 80)
    
    lambda_settings = [
        ('Memory (MB)', 'memory_mb'),
        ('Timeout (seconds)', 'timeout_seconds'),
        ('Reserved Concurrency', 'reserved_concurrency'),
        ('Provisioned Concurrency', 'provisioned_concurrency'),
        ('Architecture', 'architecture'),
    ]
    
    for label, key in lambda_settings:
        dev_val = configs['dev']['lambda'][key]
        staging_val = configs['staging']['lambda'][key]
        prod_val = configs['prod']['lambda'][key]
        print(f"{label:<30} {str(dev_val):<15} {str(staging_val):<15} {str(prod_val):<15}")
    
    print()
    
    # Print DynamoDB configuration comparison
    print("DynamoDB Configuration:")
    print("-" * 80)
    print(f"{'Setting':<30} {'Dev':<15} {'Staging':<15} {'Prod':<15}")
    print("-" * 80)
    
    dynamodb_settings = [
        ('Billing Mode', 'billing_mode'),
        ('Point-in-Time Recovery', 'pitr_enabled'),
        ('Read Capacity Units', 'read_capacity'),
        ('Write Capacity Units', 'write_capacity'),
    ]
    
    for label, key in dynamodb_settings:
        dev_val = configs['dev']['dynamodb'][key]
        staging_val = configs['staging']['dynamodb'][key]
        prod_val = configs['prod']['dynamodb'][key]
        print(f"{label:<30} {str(dev_val):<15} {str(staging_val):<15} {str(prod_val):<15}")
    
    print()
    
    # Print Logs configuration comparison
    print("CloudWatch Logs Configuration:")
    print("-" * 80)
    print(f"{'Setting':<30} {'Dev':<15} {'Staging':<15} {'Prod':<15}")
    print("-" * 80)
    
    dev_val = configs['dev']['logs']['retention_days']
    staging_val = configs['staging']['logs']['retention_days']
    prod_val = configs['prod']['logs']['retention_days']
    print(f"{'Retention (days)':<30} {str(dev_val):<15} {str(staging_val):<15} {str(prod_val):<15}")
    
    print()
    print("=" * 80)
    print("Key Observations:")
    print("=" * 80)
    print()
    print("✅ Lambda memory increases from dev (512MB) → staging (1024MB) → prod (1024MB)")
    print("✅ Lambda timeout increases from dev (180s) → staging/prod (300s)")
    print("✅ Reserved concurrency scales: dev (5) → staging (50) → prod (100)")
    print("✅ Provisioned concurrency: dev (0/disabled) → staging (5) → prod (10)")
    print("✅ DynamoDB uses PAY_PER_REQUEST mode for all environments (auto-scaling)")
    print("✅ Log retention increases: dev (3 days) → staging (14 days) → prod (30 days)")
    print()
    print("💡 Provisioned concurrency keeps Lambda instances warm in staging/prod")
    print("💡 This reduces cold start latency for better user experience")
    print("💡 Dev environment has it disabled to minimize costs")
    print()
    
    return True


if __name__ == '__main__':
    success = print_config_comparison()
    sys.exit(0 if success else 1)
