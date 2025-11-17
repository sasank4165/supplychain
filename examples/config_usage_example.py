#!/usr/bin/env python3
"""Example: Using the Configuration Management System

This example demonstrates how to use ConfigurationManager and ResourceNamer
in your application code.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_manager import ConfigurationManager, ResourceNamer, load_config


def example_basic_usage():
    """Example: Basic configuration loading"""
    print("="*70)
    print("Example 1: Basic Configuration Loading")
    print("="*70)
    
    # Load configuration for dev environment
    config = ConfigurationManager(environment='dev')
    
    # Access configuration values using dot notation
    environment = config.get('environment.name')
    region = config.get('environment.region')
    lambda_memory = config.get('resources.lambda.memory_mb')
    
    print(f"Environment: {environment}")
    print(f"Region: {region}")
    print(f"Lambda Memory: {lambda_memory} MB")
    print()


def example_resource_naming():
    """Example: Dynamic resource naming"""
    print("="*70)
    print("Example 2: Dynamic Resource Naming")
    print("="*70)
    
    config = ConfigurationManager(environment='dev')
    namer = ResourceNamer(config)
    
    # Generate various resource names
    print("Generated Resource Names:")
    print(f"  S3 Bucket (data):           {namer.s3_bucket('data')}")
    print(f"  S3 Bucket (logs):           {namer.s3_bucket('logs')}")
    print(f"  DynamoDB Table (sessions):  {namer.dynamodb_table('sessions')}")
    print(f"  Lambda Function:            {namer.lambda_function('sql-executor')}")
    print(f"  IAM Role:                   {namer.iam_role('lambda-exec')}")
    print(f"  Log Group:                  {namer.cloudwatch_log_group('lambda/sql-executor')}")
    print(f"  Parameter Store:            {namer.parameter_store_path('database-url')}")
    print(f"  Secrets Manager:            {namer.secrets_manager_name('api-key')}")
    print()


def example_tags():
    """Example: Getting resource tags"""
    print("="*70)
    print("Example 3: Resource Tags")
    print("="*70)
    
    config = ConfigurationManager(environment='dev')
    tags = config.get_tags()
    
    print("Resource Tags:")
    for key, value in tags.items():
        print(f"  {key}: {value}")
    print()


def example_feature_flags():
    """Example: Checking feature flags"""
    print("="*70)
    print("Example 4: Feature Flags")
    print("="*70)
    
    config = ConfigurationManager(environment='dev')
    
    # Check feature flags
    vpc_enabled = config.get('features.vpc_enabled', False)
    waf_enabled = config.get('features.waf_enabled', False)
    xray_enabled = config.get('features.xray_tracing', False)
    
    print("Feature Flags:")
    print(f"  VPC Enabled:    {vpc_enabled}")
    print(f"  WAF Enabled:    {waf_enabled}")
    print(f"  X-Ray Tracing:  {xray_enabled}")
    print()


def example_agent_config():
    """Example: Agent configuration"""
    print("="*70)
    print("Example 5: Agent Configuration")
    print("="*70)
    
    config = ConfigurationManager(environment='dev')
    
    # Get agent configuration
    default_model = config.get('agents.default_model')
    context_window = config.get('agents.context_window_size')
    
    print("Agent Configuration:")
    print(f"  Default Model:      {default_model}")
    print(f"  Context Window:     {context_window}")
    
    # Get specific agent config
    sql_agent_enabled = config.get('agents.sql_agent.enabled', True)
    sql_agent_model = config.get('agents.sql_agent.model')
    
    print(f"\nSQL Agent:")
    print(f"  Enabled:  {sql_agent_enabled}")
    print(f"  Model:    {sql_agent_model}")
    print()


def example_environment_comparison():
    """Example: Compare configurations across environments"""
    print("="*70)
    print("Example 6: Environment Comparison")
    print("="*70)
    
    environments = ['dev', 'staging', 'prod']
    
    print(f"{'Setting':<30} {'Dev':<15} {'Staging':<15} {'Prod':<15}")
    print("-" * 75)
    
    for env in environments:
        config = ConfigurationManager(environment=env)
        
        if env == 'dev':
            settings = {
                'Lambda Memory (MB)': config.get('resources.lambda.memory_mb'),
                'Lambda Concurrency': config.get('resources.lambda.reserved_concurrency'),
                'Log Retention (days)': config.get('resources.logs.retention_days'),
                'VPC Enabled': config.get('features.vpc_enabled'),
                'WAF Enabled': config.get('features.waf_enabled'),
                'Multi-AZ': config.get('features.multi_az'),
            }
    
    # Print comparison table
    for setting in settings.keys():
        values = []
        for env in environments:
            config = ConfigurationManager(environment=env)
            if setting == 'Lambda Memory (MB)':
                values.append(str(config.get('resources.lambda.memory_mb')))
            elif setting == 'Lambda Concurrency':
                values.append(str(config.get('resources.lambda.reserved_concurrency')))
            elif setting == 'Log Retention (days)':
                values.append(str(config.get('resources.logs.retention_days')))
            elif setting == 'VPC Enabled':
                values.append(str(config.get('features.vpc_enabled')))
            elif setting == 'WAF Enabled':
                values.append(str(config.get('features.waf_enabled')))
            elif setting == 'Multi-AZ':
                values.append(str(config.get('features.multi_az')))
        
        print(f"{setting:<30} {values[0]:<15} {values[1]:<15} {values[2]:<15}")
    
    print()


def example_convenience_function():
    """Example: Using convenience function"""
    print("="*70)
    print("Example 7: Convenience Function")
    print("="*70)
    
    # Quick way to load config
    config = load_config('dev')
    
    print(f"Loaded configuration: {config}")
    print(f"Environment: {config.get('environment.name')}")
    print()


def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("CONFIGURATION MANAGEMENT SYSTEM - USAGE EXAMPLES")
    print("="*70 + "\n")
    
    try:
        example_basic_usage()
        example_resource_naming()
        example_tags()
        example_feature_flags()
        example_agent_config()
        example_environment_comparison()
        example_convenience_function()
        
        print("="*70)
        print("All examples completed successfully!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
