#!/bin/bash
# SageMaker Lifecycle Configuration Script
# This script runs automatically when the SageMaker Notebook Instance starts
# 
# To use this script:
# 1. Create a Lifecycle Configuration in SageMaker Console
# 2. Add this script to the "Start notebook" section
# 3. Attach the Lifecycle Configuration to your Notebook Instance

set -e

# Log file for lifecycle configuration
LOG_FILE="/home/ec2-user/SageMaker/lifecycle_config.log"

echo "=========================================="  | tee -a "$LOG_FILE"
echo "SageMaker Lifecycle Configuration - Start" | tee -a "$LOG_FILE"
echo "Timestamp: $(date)" | tee -a "$LOG_FILE"
echo "=========================================="  | tee -a "$LOG_FILE"

# Configuration
APP_DIR="/home/ec2-user/SageMaker/supply-chain-mvp"
VENV_DIR="$APP_DIR/venv"

# Check if application directory exists
if [ ! -d "$APP_DIR" ]; then
    echo "Application directory not found. Run setup_notebook.sh first." | tee -a "$LOG_FILE"
    exit 0
fi

# Change to application directory
cd "$APP_DIR"

# Activate virtual environment
if [ -d "$VENV_DIR" ]; then
    echo "Activating virtual environment..." | tee -a "$LOG_FILE"
    source "$VENV_DIR/bin/activate"
else
    echo "Virtual environment not found. Run setup_notebook.sh first." | tee -a "$LOG_FILE"
    exit 0
fi

# Update dependencies (optional - comment out if not needed)
# echo "Updating dependencies..." | tee -a "$LOG_FILE"
# pip install --upgrade -r requirements.txt >> "$LOG_FILE" 2>&1

# Pull latest code from repository (if using git)
# Uncomment if you want to auto-update from git on startup
# if [ -d ".git" ]; then
#     echo "Pulling latest code..." | tee -a "$LOG_FILE"
#     git pull >> "$LOG_FILE" 2>&1
# fi

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo "WARNING: config.yaml not found. Application may not start correctly." | tee -a "$LOG_FILE"
fi

# Check if users.json exists
if [ ! -f "auth/users.json" ]; then
    echo "WARNING: auth/users.json not found. Authentication will not work." | tee -a "$LOG_FILE"
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Stop any existing Streamlit processes
echo "Stopping any existing Streamlit processes..." | tee -a "$LOG_FILE"
pkill -f "streamlit run app.py" || true
sleep 2

# Start the Streamlit application in the background
echo "Starting Streamlit application..." | tee -a "$LOG_FILE"
nohup streamlit run app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection true \
    >> logs/streamlit.log 2>&1 &

# Wait a few seconds and check if the process started
sleep 5
if pgrep -f "streamlit run app.py" > /dev/null; then
    echo "Streamlit application started successfully!" | tee -a "$LOG_FILE"
    echo "Access URL: https://<notebook-instance-name>.notebook.<region>.sagemaker.aws/proxy/8501/" | tee -a "$LOG_FILE"
else
    echo "ERROR: Failed to start Streamlit application. Check logs/streamlit.log" | tee -a "$LOG_FILE"
    exit 1
fi

# Display resource information
echo "" | tee -a "$LOG_FILE"
echo "Resource Information:" | tee -a "$LOG_FILE"
echo "  Instance Type: $(ec2-metadata --instance-type | cut -d ' ' -f 2)" | tee -a "$LOG_FILE"
echo "  Availability Zone: $(ec2-metadata --availability-zone | cut -d ' ' -f 2)" | tee -a "$LOG_FILE"
echo "  IAM Role: $(ec2-metadata --iam-info | jq -r '.InstanceProfileArn' 2>/dev/null || echo 'N/A')" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "=========================================="  | tee -a "$LOG_FILE"
echo "Lifecycle Configuration Complete" | tee -a "$LOG_FILE"
echo "=========================================="  | tee -a "$LOG_FILE"

# Exit successfully
exit 0
