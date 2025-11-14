"""Configuration for CDK deployment"""
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class EnvironmentConfig:
    """Configuration for different environments"""
    name: str
    account: str
    region: str
    alarm_email: str
    enable_waf: bool
    enable_multi_az: bool
    lambda_memory: int
    lambda_timeout: int
    lambda_reserved_concurrency: int
    api_throttle_rate: int
    api_throttle_burst: int
    log_retention_days: int
    backup_retention_days: int
    enable_xray: bool
    enable_vpc: bool
    nat_gateways: int

# Development environment
DEV_CONFIG = EnvironmentConfig(
    name="dev",
    account="123456789012",  # Replace with your account
    region="us-east-1",
    alarm_email="dev-team@example.com",
    enable_waf=False,
    enable_multi_az=False,
    lambda_memory=512,
    lambda_timeout=180,
    lambda_reserved_concurrency=10,
    api_throttle_rate=50,
    api_throttle_burst=100,
    log_retention_days=7,
    backup_retention_days=7,
    enable_xray=False,
    enable_vpc=False,
    nat_gateways=1
)

# Staging environment
STAGING_CONFIG = EnvironmentConfig(
    name="staging",
    account="123456789012",  # Replace with your account
    region="us-east-1",
    alarm_email="staging-team@example.com",
    enable_waf=True,
    enable_multi_az=True,
    lambda_memory=1024,
    lambda_timeout=300,
    lambda_reserved_concurrency=50,
    api_throttle_rate=100,
    api_throttle_burst=200,
    log_retention_days=14,
    backup_retention_days=14,
    enable_xray=True,
    enable_vpc=True,
    nat_gateways=2
)

# Production environment
PROD_CONFIG = EnvironmentConfig(
    name="prod",
    account="123456789012",  # Replace with your account
    region="us-east-1",
    alarm_email="ops-team@example.com",
    enable_waf=True,
    enable_multi_az=True,
    lambda_memory=1024,
    lambda_timeout=300,
    lambda_reserved_concurrency=100,
    api_throttle_rate=100,
    api_throttle_burst=200,
    log_retention_days=30,
    backup_retention_days=30,
    enable_xray=True,
    enable_vpc=True,
    nat_gateways=3
)

# Map environment names to configs
CONFIGS: Dict[str, EnvironmentConfig] = {
    "dev": DEV_CONFIG,
    "staging": STAGING_CONFIG,
    "prod": PROD_CONFIG
}

def get_config(environment: str) -> EnvironmentConfig:
    """Get configuration for environment"""
    return CONFIGS.get(environment, PROD_CONFIG)
