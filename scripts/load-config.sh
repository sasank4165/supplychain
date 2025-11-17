#!/bin/bash
# Configuration loader script
# Loads configuration from YAML and exports as environment variables

set -e

# Default values
ENVIRONMENT="dev"
CONFIG_FILE=""
OUTPUT_FILE=".env"
EXPORT_MODE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --environment|-e)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --config|-c)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --output|-o)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --export)
            EXPORT_MODE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --environment, -e ENV    Environment name (dev, staging, prod)"
            echo "  --config, -c FILE        Path to config file (default: config/ENV.yaml)"
            echo "  --output, -o FILE        Output file for environment variables (default: .env)"
            echo "  --export                 Export variables to current shell"
            echo "  --help, -h               Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set config file if not specified
if [ -z "$CONFIG_FILE" ]; then
    CONFIG_FILE="config/${ENVIRONMENT}.yaml"
fi

echo "📦 Loading Configuration"
echo "Environment: $ENVIRONMENT"
echo "Config File: $CONFIG_FILE"
echo "Output File: $OUTPUT_FILE"
echo ""


# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Check if Python and PyYAML are available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Create a Python script to parse YAML and generate env vars
python3 << 'EOF' > /tmp/config_env_vars.sh
import yaml
import sys
import os

config_file = sys.argv[1]
environment = sys.argv[2]

try:
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Export core configuration
    print(f"export ENVIRONMENT={environment}")
    print(f"export AWS_REGION={config.get('environment', {}).get('region', 'us-east-1')}")
    print(f"export AWS_ACCOUNT_ID={config.get('environment', {}).get('account_id', 'auto')}")
    
    # Export project configuration
    print(f"export PROJECT_NAME={config.get('project', {}).get('name', 'supply-chain-agent')}")
    print(f"export PROJECT_PREFIX={config.get('project', {}).get('prefix', 'sc-agent')}")
    print(f"export PROJECT_OWNER={config.get('project', {}).get('owner', 'platform-team')}")
    print(f"export COST_CENTER={config.get('project', {}).get('cost_center', 'supply-chain')}")
    
    # Export feature flags
    features = config.get('features', {})
    print(f"export VPC_ENABLED={str(features.get('vpc_enabled', False)).lower()}")
    print(f"export WAF_ENABLED={str(features.get('waf_enabled', False)).lower()}")
    print(f"export MULTI_AZ={str(features.get('multi_az', False)).lower()}")
    print(f"export XRAY_TRACING={str(features.get('xray_tracing', False)).lower()}")
    print(f"export BACKUP_ENABLED={str(features.get('backup_enabled', True)).lower()}")
    
    # Export resource configuration
    resources = config.get('resources', {})
    lambda_config = resources.get('lambda', {})
    print(f"export LAMBDA_MEMORY_MB={lambda_config.get('memory_mb', 512)}")
    print(f"export LAMBDA_TIMEOUT_SECONDS={lambda_config.get('timeout_seconds', 180)}")
    print(f"export LAMBDA_RESERVED_CONCURRENCY={lambda_config.get('reserved_concurrency', 10)}")
    print(f"export LAMBDA_ARCHITECTURE={lambda_config.get('architecture', 'arm64')}")
    
    dynamodb_config = resources.get('dynamodb', {})
    print(f"export DYNAMODB_BILLING_MODE={dynamodb_config.get('billing_mode', 'PAY_PER_REQUEST')}")
    print(f"export DYNAMODB_PITR={str(dynamodb_config.get('point_in_time_recovery', True)).lower()}")
    
    logs_config = resources.get('logs', {})
    print(f"export LOG_RETENTION_DAYS={logs_config.get('retention_days', 7)}")
    
    # Export agent configuration
    agents = config.get('agents', {})
    print(f"export DEFAULT_MODEL={agents.get('default_model', 'anthropic.claude-3-5-sonnet-20241022-v2:0')}")
    print(f"export CONTEXT_WINDOW_SIZE={agents.get('context_window_size', 10)}")
    print(f"export CONVERSATION_RETENTION_DAYS={agents.get('conversation_retention_days', 30)}")
    
    # Export data configuration
    data = config.get('data', {})
    print(f"export ATHENA_DATABASE={data.get('athena_database', 'supply_chain_db')}")
    print(f"export GLUE_CATALOG={data.get('glue_catalog', 'AwsDataCatalog')}")
    
    print("# Configuration loaded successfully")
    
except Exception as e:
    print(f"echo 'Error loading configuration: {e}'", file=sys.stderr)
    sys.exit(1)
EOF

# Run the Python script
python3 /tmp/config_env_vars.sh "$CONFIG_FILE" "$ENVIRONMENT" > "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Configuration loaded successfully"
    echo "📝 Environment variables written to: $OUTPUT_FILE"
    
    # If export mode, source the file
    if [ "$EXPORT_MODE" = true ]; then
        source "$OUTPUT_FILE"
        echo "✅ Variables exported to current shell"
    fi
    
    echo ""
    echo "To use these variables in your shell, run:"
    echo "  source $OUTPUT_FILE"
else
    echo "❌ Failed to load configuration"
    exit 1
fi

# Cleanup
rm -f /tmp/config_env_vars.sh
