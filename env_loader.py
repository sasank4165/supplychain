"""Environment variable loader with .env file support

This module provides utilities for loading environment variables from .env files
for local development. In production, environment variables should be set by the
deployment system or loaded from AWS Secrets Manager/Parameter Store.
"""

import os
from pathlib import Path
from typing import Optional


def load_env_file(env_file: str = '.env', override: bool = False) -> bool:
    """Load environment variables from .env file
    
    Args:
        env_file: Path to .env file
        override: If True, override existing environment variables
        
    Returns:
        True if file was loaded successfully
        
    Example:
        >>> load_env_file('.env.dev')
        >>> database = os.getenv('ATHENA_DATABASE')
    """
    env_path = Path(env_file)
    
    if not env_path.exists():
        return False
    
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path, override=override)
        return True
    except ImportError:
        print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")
        return False
    except Exception as e:
        print(f"Warning: Failed to load {env_file}: {e}")
        return False


def load_env_auto(environment: Optional[str] = None, override: bool = False) -> bool:
    """Automatically load .env file based on environment
    
    Tries to load .env files in this order:
    1. .env.{environment} (if environment specified)
    2. .env.{ENVIRONMENT env var}
    3. .env
    
    Args:
        environment: Environment name (dev, staging, prod)
        override: If True, override existing environment variables
        
    Returns:
        True if any file was loaded successfully
        
    Example:
        >>> load_env_auto('dev')  # Loads .env.dev or .env
    """
    # Determine environment
    env = environment or os.getenv('ENVIRONMENT')
    
    # Try environment-specific file first
    if env:
        env_file = f".env.{env}"
        if load_env_file(env_file, override):
            print(f"Loaded environment from: {env_file}")
            return True
    
    # Fall back to .env
    if load_env_file('.env', override):
        print("Loaded environment from: .env")
        return True
    
    return False


def validate_required_env_vars(required_vars: list) -> tuple[bool, list]:
    """Validate that required environment variables are set
    
    Args:
        required_vars: List of required environment variable names
        
    Returns:
        Tuple of (all_present, missing_vars)
        
    Example:
        >>> valid, missing = validate_required_env_vars(['AWS_REGION', 'ATHENA_DATABASE'])
        >>> if not valid:
        ...     print(f"Missing: {missing}")
    """
    missing = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    return len(missing) == 0, missing


def print_env_summary(prefix: str = 'SC_AGENT'):
    """Print summary of environment variables with given prefix
    
    Args:
        prefix: Prefix to filter environment variables
        
    Example:
        >>> print_env_summary('SC_AGENT')
    """
    print(f"Environment variables with prefix '{prefix}':")
    print("-" * 60)
    
    found = False
    for key, value in sorted(os.environ.items()):
        if key.startswith(prefix):
            # Mask sensitive values
            if any(sensitive in key.upper() for sensitive in ['SECRET', 'PASSWORD', 'KEY', 'TOKEN']):
                display_value = '***MASKED***'
            else:
                display_value = value
            
            print(f"  {key} = {display_value}")
            found = True
    
    if not found:
        print(f"  (none found)")
    
    print("-" * 60)


# Auto-load .env file when module is imported (for convenience)
# This can be disabled by setting SC_AGENT_NO_AUTO_LOAD=1
if not os.getenv('SC_AGENT_NO_AUTO_LOAD'):
    load_env_auto()
