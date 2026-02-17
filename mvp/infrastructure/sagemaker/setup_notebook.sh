#!/bin/bash
# SageMaker Notebook Instance Setup Script
# This script sets up the Supply Chain AI Assistant on a SageMaker Notebook Instance

set -e

echo "=========================================="
echo "Supply Chain AI Assistant - SageMaker Setup"
echo "=========================================="

# Configuration
APP_DIR="/home/ec2-user/SageMaker/supply-chain-mvp"
VENV_DIR="$APP_DIR/venv"
LOG_FILE="$APP_DIR/setup.log"

# Create application directory
echo "Creating application directory..."
mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Clone or update repository (if using git)
# Uncomment and modify if deploying from git repository
# if [ -d ".git" ]; then
#     echo "Updating repository..."
#     git pull
# else
#     echo "Cloning repository..."
#     git clone <YOUR_REPO_URL> .
# fi

# Create Python virtual environment
echo "Creating Python virtual environment..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "ERROR: requirements.txt not found!"
    exit 1
fi

# Create necessary directories
echo "Creating directory structure..."
mkdir -p logs
mkdir -p auth
mkdir -p config

# Copy example configuration files
echo "Setting up configuration files..."
if [ -f "config.example.yaml" ] && [ ! -f "config.yaml" ]; then
    cp config.example.yaml config.yaml
    echo "Created config.yaml from template. Please update with your settings."
fi

if [ -f "auth/users.json.example" ] && [ ! -f "auth/users.json" ]; then
    cp auth/users.json.example auth/users.json
    echo "Created auth/users.json from template."
fi

if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env from template. Please update with your settings."
fi

# Set up AWS credentials (SageMaker uses IAM role by default)
echo "Configuring AWS credentials..."
echo "SageMaker Notebook will use the attached IAM role for AWS service access."
echo "Ensure the IAM role has permissions for:"
echo "  - Amazon Bedrock (bedrock:InvokeModel)"
echo "  - Redshift Data API (redshift-data:*)"
echo "  - AWS Lambda (lambda:InvokeFunction)"
echo "  - AWS Glue (glue:GetTable, glue:GetDatabase)"

# Create startup script
echo "Creating startup script..."
cat > "$APP_DIR/start_app.sh" << 'EOF'
#!/bin/bash
cd /home/ec2-user/SageMaker/supply-chain-mvp
source venv/bin/activate
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
EOF
chmod +x "$APP_DIR/start_app.sh"

# Create systemd service file (optional - for automatic startup)
echo "Creating systemd service file..."
sudo tee /etc/systemd/system/supply-chain-mvp.service > /dev/null << EOF
[Unit]
Description=Supply Chain AI Assistant
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/start_app.sh
Restart=on-failure
RestartSec=10
StandardOutput=append:$APP_DIR/logs/app.log
StandardError=append:$APP_DIR/logs/error.log

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Update config.yaml with your AWS resource details"
echo "2. Update auth/users.json with user credentials"
echo "3. Start the application:"
echo "   Manual: ./start_app.sh"
echo "   Service: sudo systemctl start supply-chain-mvp"
echo "   Auto-start: sudo systemctl enable supply-chain-mvp"
echo ""
echo "4. Access the application:"
echo "   - Use SageMaker Proxy: https://<notebook-instance-name>.notebook.<region>.sagemaker.aws/proxy/8501/"
echo "   - Or port forward: ssh -L 8501:localhost:8501 ec2-user@<notebook-instance>"
echo ""
echo "5. View logs:"
echo "   Application: tail -f $APP_DIR/logs/app.log"
echo "   Service: sudo journalctl -u supply-chain-mvp -f"
echo ""
echo "For troubleshooting, see: $APP_DIR/README.md"
echo "=========================================="
