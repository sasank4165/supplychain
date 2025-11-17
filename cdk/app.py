#!/usr/bin/env python3
"""CDK app for Supply Chain Agentic AI infrastructure - Production Ready"""
import os
import aws_cdk as cdk
from supply_chain_stack import (
    NetworkStack,
    SecurityStack,
    DataStack,
    SupplyChainAgentStack,
    MonitoringStack,
    BackupStack
)
from config import load_cdk_config

app = cdk.App()

# Load configuration from YAML files
environment = app.node.try_get_context("environment") or os.getenv("ENVIRONMENT", "dev")
config = load_cdk_config(environment)

# CDK environment
env = cdk.Environment(
    account=config.account_id,
    region=config.region
)

# Get tags from configuration using TagManager
base_tags = config.get_tags()

# Helper function to apply tags to a stack with optional additional tags
def apply_tags_to_stack(stack, additional_tags=None):
    """Apply tags to a CDK stack with inheritance support"""
    stack_tags = config.get_tags(additional_tags)
    for key, value in stack_tags.items():
        cdk.Tags.of(stack).add(key, value)

# Conditionally create Network Stack (only if VPC is enabled)
network_stack = None
if config.vpc_enabled:
    network_stack = NetworkStack(
        app,
        f"SupplyChainNetwork-{config.environment_name}",
        config=config,
        env=env,
        description="Network infrastructure for Supply Chain Agent"
    )
    
    apply_tags_to_stack(network_stack, {'Component': 'Network', 'backup': 'true'})

# Security Stack (KMS, Secrets Manager)
security_stack = SecurityStack(
    app,
    f"SupplyChainSecurity-{config.environment_name}",
    config=config,
    env=env,
    description="Security infrastructure for Supply Chain Agent"
)

apply_tags_to_stack(security_stack, {'Component': 'Security', 'backup': 'true'})

# Data Stack (S3, Glue, Athena)
data_stack = DataStack(
    app,
    f"SupplyChainData-{config.environment_name}",
    config=config,
    kms_key=security_stack.data_key,
    env=env,
    description="Data infrastructure for Supply Chain Agent"
)

data_stack.add_dependency(security_stack)

apply_tags_to_stack(data_stack, {'Component': 'Data', 'backup': 'true'})

# Main Application Stack (Lambda, DynamoDB, API Gateway, Cognito)
app_stack = SupplyChainAgentStack(
    app,
    f"SupplyChainApp-{config.environment_name}",
    config=config,
    vpc=network_stack.vpc if network_stack else None,
    lambda_sg=network_stack.lambda_sg if network_stack else None,
    kms_key=security_stack.data_key,
    data_bucket=data_stack.data_bucket,
    athena_results_bucket=data_stack.athena_results_bucket,
    db_config_secret=security_stack.db_config_secret,
    env=env,
    description="Application infrastructure for Supply Chain Agent"
)

if network_stack:
    app_stack.add_dependency(network_stack)
app_stack.add_dependency(security_stack)
app_stack.add_dependency(data_stack)

apply_tags_to_stack(app_stack, {'Component': 'Application', 'backup': 'true'})

# Monitoring Stack (CloudWatch, SNS)
if config.dashboard_enabled:
    monitoring_stack = MonitoringStack(
        app,
        f"SupplyChainMonitoring-{config.environment_name}",
        config=config,
        env=env,
        description="Monitoring infrastructure for Supply Chain Agent"
    )
    
    monitoring_stack.add_dependency(app_stack)
    
    apply_tags_to_stack(monitoring_stack, {'Component': 'Monitoring'})

# Backup Stack (AWS Backup) - only if backups are enabled
if config.backup_enabled:
    backup_stack = BackupStack(
        app,
        f"SupplyChainBackup-{config.environment_name}",
        config=config,
        env=env,
        description="Backup infrastructure for Supply Chain Agent"
    )
    
    backup_stack.add_dependency(app_stack)
    
    apply_tags_to_stack(backup_stack, {'Component': 'Backup', 'backup': 'true'})

app.synth()
