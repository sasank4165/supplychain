#!/usr/bin/env python3
"""
Quick Setup Script for Supply Chain MVP on SageMaker

This script automates the initial setup:
1. Creates config.yaml from config.example.yaml
2. Auto-detects AWS account ID
3. Verifies AWS connectivity
4. Creates necessary directories

Usage:
    python scripts/quick_setup.py
"""

import sys
import os
from pathlib import Path
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def print_step(step_num, text):
    """Print a step header."""
    print(f"\nStep {step_num}: {text}")
    print("-" * 60)


def get_aws_account_id():
    """Get AWS account ID using boto3."""
    try:
        import boto3
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        return identity['Account']
    except Exception as e:
        print(f"⚠ Warning: Could not auto-detect AWS account ID: {e}")
        return None


def verify_aws_connectivity():
    """Verify AWS connectivity and permissions."""
    try:
        import boto3
        
        # Test STS (basic AWS connectivity)
        print("  Testing AWS connectivity...")
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"  ✓ Connected as: {identity['Arn']}")
        print(f"  ✓ Account ID: {identity['Account']}")
        
        # Test Bedrock access
        print("\n  Testing Bedrock access...")
        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        print("  ✓ Bedrock client initialized")
        
        # Test Redshift Data API access
        print("\n  Testing Redshift Data API access...")
        redshift_data = boto3.client('redshift-data', region_name='us-east-1')
        print("  ✓ Redshift Data API client initialized")
        
        # Test Glue access
        print("\n  Testing Glue access...")
        glue = boto3.client('glue', region_name='us-east-1')
        print("  ✓ Glue client initialized")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def create_config_file():
    """Create config.yaml from config.example.yaml."""
    config_example = Path("config.example.yaml")
    config_file = Path("config.yaml")
    
    if config_file.exists():
        response = input(f"  config.yaml already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("  ⚠ Skipping config.yaml creation")
            return False
    
    if not config_example.exists():
        print(f"  ✗ Error: {config_example} not found")
        return False
    
    try:
        shutil.copy(config_example, config_file)
        print(f"  ✓ Created {config_file}")
        return True
    except Exception as e:
        print(f"  ✗ Error creating config file: {e}")
        return False


def create_directories():
    """Create necessary directories."""
    directories = [
        'logs',
        'auth',
        'sample_data'
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"  ✓ Created directory: {directory}")
            except Exception as e:
                print(f"  ✗ Error creating {directory}: {e}")
        else:
            print(f"  ✓ Directory exists: {directory}")


def check_dependencies():
    """Check if required Python packages are installed."""
    required_packages = [
        'boto3',
        'streamlit',
        'yaml',
        'bcrypt'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n  ⚠ Missing packages: {', '.join(missing_packages)}")
        print("  Install with: pip install -r requirements.txt")
        return False
    
    return True


def main():
    """Main setup function."""
    print_header("Supply Chain MVP - Quick Setup")
    print("This script will set up your MVP environment on SageMaker")
    
    # Check we're in the right directory
    if not Path("config.example.yaml").exists():
        print("\n✗ Error: Must run from the mvp directory")
        print("  cd /home/ec2-user/SageMaker/supplychain/mvp")
        sys.exit(1)
    
    # Step 1: Check dependencies
    print_step(1, "Checking Dependencies")
    if not check_dependencies():
        print("\n⚠ Please install missing dependencies first")
        sys.exit(1)
    
    # Step 2: Verify AWS connectivity
    print_step(2, "Verifying AWS Connectivity")
    if not verify_aws_connectivity():
        print("\n⚠ AWS connectivity issues detected")
        print("  Please check your IAM role permissions")
        sys.exit(1)
    
    # Step 3: Get AWS account ID
    print_step(3, "Detecting AWS Account ID")
    account_id = get_aws_account_id()
    if account_id:
        print(f"  ✓ AWS Account ID: {account_id}")
        print("  ✓ This will be auto-detected in config.yaml")
    else:
        print("  ⚠ Could not auto-detect account ID")
        print("  You may need to set it manually in config.yaml")
    
    # Step 4: Create config file
    print_step(4, "Creating Configuration File")
    create_config_file()
    
    # Step 5: Create directories
    print_step(5, "Creating Directories")
    create_directories()
    
    # Summary
    print_header("Setup Complete!")
    print("\nNext steps:")
    print("  1. Load sample data into Redshift:")
    print("     python scripts/generate_sample_data.py --load-redshift \\")
    print("       --workgroup supply-chain-mvp --database supply_chain_db")
    print()
    print("  2. Setup Glue Catalog (optional):")
    print("     python scripts/setup_glue_catalog.py")
    print()
    print("  3. Create users:")
    print("     python scripts/create_user.py")
    print()
    print("  4. Start the application:")
    print("     streamlit run app.py --server.port 8501 --server.address 0.0.0.0")
    print()
    print("Configuration file: config.yaml")
    print("  - AWS Account ID will be auto-detected")
    print("  - Review and adjust settings as needed")
    print()


if __name__ == '__main__':
    main()
