#!/usr/bin/env python3
"""Setup local environment variables from configuration

This script generates a .env file for local development based on the
configuration file. This allows running the application locally without
AWS Secrets Manager/Parameter Store.

Usage:
    python scripts/setup-local-env.py --environment dev
    
    # Output to specific file
    python scripts/setup-local-env.py --environment dev --output .env.dev
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_manager import ConfigurationManager, ResourceNamer


def generate_env_file(
    config: ConfigurationManager,
    namer: ResourceNamer,
    output_file: str = '.env'
) -> bool:
    """Generate .env file from configuration
    
    Args:
        config: ConfigurationManager instance
        namer: ResourceNamer instance
        output_file: Path to output .env file
        
    Returns:
        True if successful
    """
    env_vars = {
        # AWS Configuration
        'AWS_REGION': config.get('environment.region'),
        'ENVIRONMENT': config.get('environment.name'),
        'SC_AGENT_PREFIX': config.get('project.prefix'),
        
        # Athena Configuration
        'ATHENA_DATABASE': config.get('data.athena_database', 'supply_chain_db'),
        'ATHENA_CATALOG': config.get('data.glue_catalog', 'AwsDataCatalog'),
        'ATHENA_OUTPUT_LOCATION': f"s3://{namer.s3_bucket('athena-results')}/",
        
        # DynamoDB Tables
        'DYNAMODB_SESSION_TABLE': namer.dynamodb_table('sessions'),
        'DYNAMODB_MEMORY_TABLE': namer.dynamodb_table('memory'),
        
        # Lambda Functions
        'LAMBDA_SQL_EXECUTOR': namer.lambda_function('sql-executor'),
        'LAMBDA_INVENTORY_OPTIMIZER': namer.lambda_function('inventory-optimizer'),
        'LAMBDA_LOGISTICS_OPTIMIZER': namer.lambda_function('logistics-optimizer'),
        'LAMBDA_SUPPLIER_ANALYZER': namer.lambda_function('supplier-analyzer'),
        
        # Bedrock Configuration
        'BEDROCK_MODEL_ID': config.get('agents.default_model'),
        
        # Cognito Configuration (if available)
        'USER_POOL_ID': config.get('auth.user_pool_id', 'PLACEHOLDER'),
        'USER_POOL_CLIENT_ID': config.get('auth.client_id', 'PLACEHOLDER'),
    }
    
    # Add parameter store paths as environment variables
    # These will be used by SecretsManager as fallbacks
    param_vars = {
        'PARAM_ATHENA_DATABASE': config.get('data.athena_database', 'supply_chain_db'),
        'PARAM_ATHENA_OUTPUT_LOCATION': f"s3://{namer.s3_bucket('athena-results')}/",
    }
    
    env_vars.update(param_vars)
    
    try:
        with open(output_file, 'w') as f:
            f.write("# Auto-generated environment variables\n")
            f.write(f"# Environment: {config.environment}\n")
            f.write(f"# Generated: {Path(__file__).name}\n")
            f.write("#\n")
            f.write("# IMPORTANT: This file contains configuration for local development.\n")
            f.write("# Do NOT commit this file to version control if it contains secrets.\n")
            f.write("#\n\n")
            
            # Write AWS configuration
            f.write("# AWS Configuration\n")
            for key in ['AWS_REGION', 'ENVIRONMENT', 'SC_AGENT_PREFIX']:
                f.write(f"{key}={env_vars[key]}\n")
            f.write("\n")
            
            # Write Athena configuration
            f.write("# Athena Configuration\n")
            for key in ['ATHENA_DATABASE', 'ATHENA_CATALOG', 'ATHENA_OUTPUT_LOCATION']:
                f.write(f"{key}={env_vars[key]}\n")
            f.write("\n")
            
            # Write DynamoDB configuration
            f.write("# DynamoDB Tables\n")
            for key in ['DYNAMODB_SESSION_TABLE', 'DYNAMODB_MEMORY_TABLE']:
                f.write(f"{key}={env_vars[key]}\n")
            f.write("\n")
            
            # Write Lambda configuration
            f.write("# Lambda Functions\n")
            for key in ['LAMBDA_SQL_EXECUTOR', 'LAMBDA_INVENTORY_OPTIMIZER',
                       'LAMBDA_LOGISTICS_OPTIMIZER', 'LAMBDA_SUPPLIER_ANALYZER']:
                f.write(f"{key}={env_vars[key]}\n")
            f.write("\n")
            
            # Write Bedrock configuration
            f.write("# Bedrock Configuration\n")
            f.write(f"BEDROCK_MODEL_ID={env_vars['BEDROCK_MODEL_ID']}\n")
            f.write("\n")
            
            # Write Cognito configuration
            f.write("# Cognito Configuration\n")
            f.write(f"USER_POOL_ID={env_vars['USER_POOL_ID']}\n")
            f.write(f"USER_POOL_CLIENT_ID={env_vars['USER_POOL_CLIENT_ID']}\n")
            f.write("\n")
            
            # Write parameter store fallbacks
            f.write("# Parameter Store Fallbacks (for local development)\n")
            for key, value in param_vars.items():
                f.write(f"{key}={value}\n")
            f.write("\n")
            
            # Write placeholder secrets
            f.write("# Secrets (PLACEHOLDER - Update with actual values)\n")
            f.write("# SECRET_DATABASE_CONNECTION_STRING=postgresql://...\n")
            f.write("# SECRET_API_EXTERNAL_API_KEY=your-api-key\n")
            f.write("\n")
        
        return True
        
    except Exception as e:
        print(f"Error writing .env file: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Generate .env file for local development',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate .env file for dev environment
  python scripts/setup-local-env.py --environment dev
  
  # Generate to specific file
  python scripts/setup-local-env.py --environment dev --output .env.dev
  
After generating the .env file:
  1. Review the file and update any PLACEHOLDER values
  2. Add actual secrets if needed
  3. Load the file: source .env (Linux/Mac) or use python-dotenv
        """
    )
    
    parser.add_argument(
        '--environment',
        required=True,
        help='Environment name (dev, staging, prod)'
    )
    
    parser.add_argument(
        '--output',
        default='.env',
        help='Output file path (default: .env)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Setup Local Environment")
    print("=" * 70)
    print()
    
    # Load configuration
    try:
        print(f"Loading configuration for environment: {args.environment}")
        config = ConfigurationManager(environment=args.environment)
        namer = ResourceNamer(config)
        
        print(f"✓ Configuration loaded")
        print(f"  Environment: {config.environment}")
        print(f"  Region: {config.get('environment.region')}")
        print(f"  Prefix: {config.get('project.prefix')}")
        print()
        
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return 1
    
    # Generate .env file
    print(f"Generating .env file: {args.output}")
    if generate_env_file(config, namer, args.output):
        print(f"✓ Successfully created {args.output}")
        print()
        print("Next steps:")
        print(f"  1. Review {args.output} and update PLACEHOLDER values")
        print("  2. Add actual secrets if needed")
        print("  3. Load environment variables:")
        print(f"     - Linux/Mac: source {args.output}")
        print(f"     - Windows: Use python-dotenv or set variables manually")
        print()
        print("IMPORTANT: Do NOT commit .env files with secrets to version control!")
        print("           Add .env to your .gitignore file")
    else:
        print(f"✗ Failed to create {args.output}")
        return 1
    
    print("=" * 70)
    return 0


if __name__ == '__main__':
    sys.exit(main())
