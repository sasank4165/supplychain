#!/bin/bash
# Quick verification script for Supply Chain MVP setup

echo "============================================================"
echo "Supply Chain MVP - Setup Verification"
echo "============================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "config.example.yaml" ]; then
    echo "✗ Error: Must run from the mvp directory"
    echo "  cd /home/ec2-user/SageMaker/supplychain/mvp"
    exit 1
fi

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo "⚠ config.yaml not found"
    echo "  Creating from config.example.yaml..."
    cp config.example.yaml config.yaml
    echo "✓ Created config.yaml"
else
    echo "✓ config.yaml exists"
fi

# Test configuration loading
echo ""
echo "Testing configuration..."
python scripts/test_config.py

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================================"
    echo "✓ Setup verification complete!"
    echo "============================================================"
    echo ""
    echo "You're ready to start the application:"
    echo "  streamlit run app.py --server.port 8501 --server.address 0.0.0.0"
    echo ""
else
    echo ""
    echo "============================================================"
    echo "✗ Setup verification failed"
    echo "============================================================"
    echo ""
    echo "Please check the errors above and try again."
    exit 1
fi
