#!/usr/bin/env python3
"""CDK app for Supply Chain Agentic AI infrastructure - Production Ready"""
import aws_cdk as cdk
from supply_chain_stack import (
    NetworkStack,
    SecurityStack,
    DataStack,
    SupplyChainAgentStack,
    MonitoringStack,
    BackupStack
)

app = cdk.App()

# Get configuration from context
env = cdk.Environment(
    account=app.node.try_get_context("account") or app.node.try_get_context("CDK_DEFAULT_ACCOUNT"),
    region=app.node.try_get_context("region") or app.node.try_get_context("CDK_DEFAULT_REGION") or "us-east-1"
)

alarm_email = app.node.try_get_context("alarm_email") or "admin@example.com"
environment = app.node.try_get_context("environment") or "prod"

# Tags for all resources
tags = {
    "Project": "SupplyChainAgent",
    "Environment": environment,
    "ManagedBy": "CDK",
    "CostCenter": "SupplyChain",
    "backup": "true"  # For AWS Backup
}

# Network Stack (VPC, Subnets, Security Groups)
network_stack = NetworkStack(
    app,
    f"SupplyChainNetwork-{environment}",
    env=env,
    description="Network infrastructure for Supply Chain Agent"
)

for key, value in tags.items():
    cdk.Tags.of(network_stack).add(key, value)

# Security Stack (KMS, Secrets Manager)
security_stack = SecurityStack(
    app,
    f"SupplyChainSecurity-{environment}",
    env=env,
    description="Security infrastructure for Supply Chain Agent"
)

for key, value in tags.items():
    cdk.Tags.of(security_stack).add(key, value)

# Data Stack (S3, Glue, Athena)
data_stack = DataStack(
    app,
    f"SupplyChainData-{environment}",
    kms_key=security_stack.data_key,
    env=env,
    description="Data infrastructure for Supply Chain Agent"
)

data_stack.add_dependency(security_stack)

for key, value in tags.items():
    cdk.Tags.of(data_stack).add(key, value)

# Main Application Stack (Lambda, DynamoDB, API Gateway, Cognito)
app_stack = SupplyChainAgentStack(
    app,
    f"SupplyChainApp-{environment}",
    vpc=network_stack.vpc,
    lambda_sg=network_stack.lambda_sg,
    kms_key=security_stack.data_key,
    data_bucket=data_stack.data_bucket,
    athena_results_bucket=data_stack.athena_results_bucket,
    db_config_secret=security_stack.db_config_secret,
    env=env,
    description="Application infrastructure for Supply Chain Agent"
)

app_stack.add_dependency(network_stack)
app_stack.add_dependency(security_stack)
app_stack.add_dependency(data_stack)

for key, value in tags.items():
    cdk.Tags.of(app_stack).add(key, value)

# Monitoring Stack (CloudWatch, SNS)
monitoring_stack = MonitoringStack(
    app,
    f"SupplyChainMonitoring-{environment}",
    alarm_email=alarm_email,
    env=env,
    description="Monitoring infrastructure for Supply Chain Agent"
)

monitoring_stack.add_dependency(app_stack)

for key, value in tags.items():
    cdk.Tags.of(monitoring_stack).add(key, value)

# Backup Stack (AWS Backup)
backup_stack = BackupStack(
    app,
    f"SupplyChainBackup-{environment}",
    env=env,
    description="Backup infrastructure for Supply Chain Agent"
)

backup_stack.add_dependency(app_stack)

for key, value in tags.items():
    cdk.Tags.of(backup_stack).add(key, value)

app.synth()
