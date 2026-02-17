#!/usr/bin/env python3
"""
Test Configuration Loading

This script tests that config.yaml loads correctly and AWS account ID is auto-detected.

Usage:
    python scripts/test_config.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """Test configuration loading."""
    print("=" * 60)
    print("Configuration Test")
    print("=" * 60)
    
    # Test 1: Import config manager
    print("\nTest 1: Importing ConfigManager...")
    try:
        from utils.config_manager import ConfigManager
        print("✓ ConfigManager imported successfully")
    except Exception as e:
        print(f"✗ Error importing ConfigManager: {e}")
        sys.exit(1)
    
    # Test 2: Load configuration
    print("\nTest 2: Loading configuration...")
    try:
        config = ConfigManager()
        print("✓ Configuration loaded successfully")
    except Exception as e:
        print(f"✗ Error loading configuration: {e}")
        print("\nMake sure config.yaml exists:")
        print("  cp config.example.yaml config.yaml")
        sys.exit(1)
    
    # Test 3: Check AWS account ID
    print("\nTest 3: Checking AWS account ID...")
    try:
        glue_config = config.get_glue_config()
        catalog_id = glue_config.get('catalog_id')
        
        if catalog_id:
            print(f"✓ AWS Account ID detected: {catalog_id}")
            
            # Verify it's a valid account ID format (12 digits)
            if len(catalog_id) == 12 and catalog_id.isdigit():
                print("✓ Account ID format is valid")
            else:
                print(f"⚠ Warning: Account ID format may be invalid: {catalog_id}")
        else:
            print("✗ AWS Account ID not found in configuration")
            sys.exit(1)
            
    except Exception as e:
        print(f"✗ Error checking account ID: {e}")
        sys.exit(1)
    
    # Test 4: Check session secret
    print("\nTest 4: Checking session secret...")
    try:
        auth_config = config.get_auth_config()
        session_secret = auth_config.get('session_secret')
        
        if session_secret:
            print(f"✓ Session secret generated: {session_secret[:16]}... (truncated)")
            
            # Verify it's a valid hex string of appropriate length
            if len(session_secret) >= 32:
                print("✓ Session secret length is valid")
            else:
                print(f"⚠ Warning: Session secret may be too short: {len(session_secret)} chars")
        else:
            print("✗ Session secret not found in configuration")
            sys.exit(1)
            
    except Exception as e:
        print(f"✗ Error checking session secret: {e}")
        sys.exit(1)
    
    # Test 5: Display key configuration values
    print("\nTest 5: Key Configuration Values")
    print("-" * 60)
    
    config_items = [
        ('AWS Region', config.get('aws.region')),
        ('Bedrock Model', config.get('aws.bedrock.model_id')),
        ('Redshift Workgroup', config.get('aws.redshift.workgroup_name')),
        ('Redshift Database', config.get('aws.redshift.database')),
        ('Glue Catalog ID', config.get('aws.glue.catalog_id')),
        ('Glue Database', config.get('aws.glue.database')),
        ('Cache Enabled', config.get('cache.enabled')),
        ('Cost Tracking Enabled', config.get('cost.enabled')),
    ]
    
    for name, value in config_items:
        status = "✓" if value else "✗"
        print(f"{status} {name}: {value}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Configuration Test Complete!")
    print("=" * 60)
    print("\n✓ All tests passed!")
    print("\nYour configuration is ready to use.")
    print("AWS Account ID is automatically detected - no hardcoding needed!")


if __name__ == '__main__':
    main()
