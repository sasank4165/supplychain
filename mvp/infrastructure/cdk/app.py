#!/usr/bin/env python3
"""CDK app entry point for Supply Chain MVP infrastructure."""

import os
import aws_cdk as cdk
from mvp_stack import SupplyChainMVPStack

app = cdk.App()

# Get environment configuration
account = os.environ.get("CDK_DEFAULT_ACCOUNT")
region = os.environ.get("CDK_DEFAULT_REGION", "us-east-1")

# Create the MVP stack
SupplyChainMVPStack(
    app,
    "SupplyChainMVPStack",
    env=cdk.Environment(account=account, region=region),
    description="Cost-optimized MVP infrastructure for Supply Chain AI Assistant"
)

app.synth()
