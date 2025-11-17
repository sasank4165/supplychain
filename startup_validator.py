"""Startup validation for Supply Chain Agentic AI Application

This module validates that all required environment variables and configurations
are properly set before the application starts. It provides clear error messages
to help developers and operators quickly identify configuration issues.
"""

import os
import sys
from typing import List, Dict, Tuple, Optional
from pathlib import Path


class StartupValidationError(Exception):
    """Raised when startup validation fails"""
    pass


def validate_environment_variables(required_vars: List[str], optional_vars: List[str] = None) -> Tuple[bool, List[str], List[str]]:
    """Validate that required environment variables are set
    
    Args:
        required_vars: List of required environment variable names
        optional_vars: List of optional environment variable names (for warnings)
        
    Returns:
        Tuple of (all_required_present, missing_required, missing_optional)
    """
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
    
    if optional_vars:
        for var in optional_vars:
            if not os.getenv(var):
                missing_optional.append(var)
    
    return len(missing_required) == 0, missing_required, missing_optional


def validate_aws_credentials() -> Tuple[bool, Optional[str]]:
    """Validate that AWS credentials are configured
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        import boto3
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        return True, None
    except Exception as e:
        return False, f"AWS credentials not configured or invalid: {str(e)}"


def validate_configuration_file(environment: str = None) -> Tuple[bool, Optional[str]]:
    """Validate that configuration file exists and is valid
    
    Args:
        environment: Environment name (if None, uses ENVIRONMENT env var)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    env = environment or os.getenv('ENVIRONMENT', 'dev')
    config_file = Path('config') / f"{env}.yaml"
    
    if not config_file.exists():
        return False, f"Configuration file not found: {config_file}"
    
    try:
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Basic validation
        if not isinstance(config, dict):
            return False, f"Configuration file is not a valid YAML dictionary: {config_file}"
        
        # Check for required top-level keys
        required_keys = ['environment', 'project', 'resources']
        missing_keys = [key for key in required_keys if key not in config]
        
        if missing_keys:
            return False, f"Configuration file missing required keys: {', '.join(missing_keys)}"
        
        return True, None
    except Exception as e:
        return False, f"Failed to load configuration file: {str(e)}"


def validate_dynamodb_tables(table_names: List[str]) -> Tuple[bool, List[str]]:
    """Validate that DynamoDB tables exist (optional check)
    
    Args:
        table_names: List of table names to check
        
    Returns:
        Tuple of (all_exist, missing_tables)
    """
    try:
        import boto3
        dynamodb = boto3.client('dynamodb')
        
        missing_tables = []
        for table_name in table_names:
            if not table_name:  # Skip empty table names
                continue
            try:
                dynamodb.describe_table(TableName=table_name)
            except dynamodb.exceptions.ResourceNotFoundException:
                missing_tables.append(table_name)
            except Exception:
                # Other errors (permissions, etc.) - skip validation
                pass
        
        return len(missing_tables) == 0, missing_tables
    except Exception:
        # If we can't check, assume valid (might not have permissions)
        return True, []


def validate_lambda_functions(function_names: List[str]) -> Tuple[bool, List[str]]:
    """Validate that Lambda functions exist (optional check)
    
    Args:
        function_names: List of function names to check
        
    Returns:
        Tuple of (all_exist, missing_functions)
    """
    try:
        import boto3
        lambda_client = boto3.client('lambda')
        
        missing_functions = []
        for function_name in function_names:
            if not function_name:  # Skip empty function names
                continue
            try:
                lambda_client.get_function(FunctionName=function_name)
            except lambda_client.exceptions.ResourceNotFoundException:
                missing_functions.append(function_name)
            except Exception:
                # Other errors (permissions, etc.) - skip validation
                pass
        
        return len(missing_functions) == 0, missing_functions
    except Exception:
        # If we can't check, assume valid (might not have permissions)
        return True, []


def run_startup_validation(
    check_aws: bool = True,
    check_config: bool = True,
    check_resources: bool = False,
    verbose: bool = True
) -> bool:
    """Run comprehensive startup validation
    
    Args:
        check_aws: Whether to validate AWS credentials
        check_config: Whether to validate configuration file
        check_resources: Whether to validate AWS resources exist
        verbose: Whether to print detailed messages
        
    Returns:
        True if all validations pass, False otherwise
        
    Raises:
        StartupValidationError: If critical validation fails
    """
    errors = []
    warnings = []
    
    if verbose:
        print("=" * 70)
        print("Supply Chain Agentic AI - Startup Validation")
        print("=" * 70)
    
    # 1. Validate required environment variables
    if verbose:
        print("\n[1/5] Validating environment variables...")
    
    required_vars = [
        'AWS_REGION'
    ]
    
    optional_vars = [
        'ENVIRONMENT',
        'SC_AGENT_PREFIX',
        'ATHENA_DATABASE',
        'ATHENA_OUTPUT_LOCATION',
        'DYNAMODB_SESSION_TABLE',
        'DYNAMODB_MEMORY_TABLE',
        'DYNAMODB_CONVERSATION_TABLE',
        'LAMBDA_INVENTORY_OPTIMIZER',
        'LAMBDA_LOGISTICS_OPTIMIZER',
        'LAMBDA_SUPPLIER_ANALYZER',
        'BEDROCK_MODEL_ID',
        'USER_POOL_ID',
        'USER_POOL_CLIENT_ID'
    ]
    
    valid, missing_required, missing_optional = validate_environment_variables(required_vars, optional_vars)
    
    if not valid:
        errors.append(f"Missing required environment variables: {', '.join(missing_required)}")
    elif verbose:
        print("  ✓ Required environment variables present")
    
    if missing_optional and verbose:
        warnings.append(f"Missing optional environment variables: {', '.join(missing_optional)}")
        print(f"  ⚠ Missing optional variables: {', '.join(missing_optional)}")
    
    # 2. Validate AWS credentials
    if check_aws:
        if verbose:
            print("\n[2/5] Validating AWS credentials...")
        
        valid, error = validate_aws_credentials()
        if not valid:
            errors.append(error)
        elif verbose:
            print("  ✓ AWS credentials valid")
    else:
        if verbose:
            print("\n[2/5] Skipping AWS credentials validation")
    
    # 3. Validate configuration file
    if check_config:
        if verbose:
            print("\n[3/5] Validating configuration file...")
        
        valid, error = validate_configuration_file()
        if not valid:
            warnings.append(error)
            if verbose:
                print(f"  ⚠ {error}")
                print("  → Will use environment variables only")
        elif verbose:
            print("  ✓ Configuration file valid")
    else:
        if verbose:
            print("\n[3/5] Skipping configuration file validation")
    
    # 4. Validate DynamoDB tables (optional)
    if check_resources:
        if verbose:
            print("\n[4/5] Validating DynamoDB tables...")
        
        table_names = [
            os.getenv('DYNAMODB_SESSION_TABLE'),
            os.getenv('DYNAMODB_MEMORY_TABLE'),
            os.getenv('DYNAMODB_CONVERSATION_TABLE')
        ]
        
        valid, missing = validate_dynamodb_tables(table_names)
        if not valid:
            warnings.append(f"DynamoDB tables not found: {', '.join(missing)}")
            if verbose:
                print(f"  ⚠ Missing tables: {', '.join(missing)}")
        elif verbose:
            print("  ✓ DynamoDB tables exist")
    else:
        if verbose:
            print("\n[4/5] Skipping DynamoDB table validation")
    
    # 5. Validate Lambda functions (optional)
    if check_resources:
        if verbose:
            print("\n[5/5] Validating Lambda functions...")
        
        function_names = [
            os.getenv('LAMBDA_INVENTORY_OPTIMIZER'),
            os.getenv('LAMBDA_LOGISTICS_OPTIMIZER'),
            os.getenv('LAMBDA_SUPPLIER_ANALYZER')
        ]
        
        valid, missing = validate_lambda_functions(function_names)
        if not valid:
            warnings.append(f"Lambda functions not found: {', '.join(missing)}")
            if verbose:
                print(f"  ⚠ Missing functions: {', '.join(missing)}")
        elif verbose:
            print("  ✓ Lambda functions exist")
    else:
        if verbose:
            print("\n[5/5] Skipping Lambda function validation")
    
    # Summary
    if verbose:
        print("\n" + "=" * 70)
        print("Validation Summary")
        print("=" * 70)
        
        if errors:
            print(f"\n❌ ERRORS ({len(errors)}):")
            for error in errors:
                print(f"  • {error}")
        
        if warnings:
            print(f"\n⚠ WARNINGS ({len(warnings)}):")
            for warning in warnings:
                print(f"  • {warning}")
        
        if not errors and not warnings:
            print("\n✓ All validations passed!")
        elif not errors:
            print("\n✓ No critical errors (warnings can be ignored)")
        
        print("=" * 70)
    
    # Raise error if critical validation failed
    if errors:
        error_msg = "\n".join(errors)
        raise StartupValidationError(
            f"Startup validation failed:\n{error_msg}\n\n"
            "Please fix these issues before starting the application."
        )
    
    return True


def validate_or_exit(
    check_aws: bool = True,
    check_config: bool = True,
    check_resources: bool = False,
    verbose: bool = True
):
    """Run startup validation and exit if it fails
    
    This is a convenience function for use in application entry points.
    
    Args:
        check_aws: Whether to validate AWS credentials
        check_config: Whether to validate configuration file
        check_resources: Whether to validate AWS resources exist
        verbose: Whether to print detailed messages
    """
    try:
        run_startup_validation(
            check_aws=check_aws,
            check_config=check_config,
            check_resources=check_resources,
            verbose=verbose
        )
    except StartupValidationError as e:
        print(f"\n❌ {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    """Run validation when executed as a script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate application startup configuration")
    parser.add_argument('--no-aws', action='store_true', help="Skip AWS credentials validation")
    parser.add_argument('--no-config', action='store_true', help="Skip configuration file validation")
    parser.add_argument('--check-resources', action='store_true', help="Check that AWS resources exist")
    parser.add_argument('--quiet', action='store_true', help="Suppress output (only show errors)")
    
    args = parser.parse_args()
    
    validate_or_exit(
        check_aws=not args.no_aws,
        check_config=not args.no_config,
        check_resources=args.check_resources,
        verbose=not args.quiet
    )
