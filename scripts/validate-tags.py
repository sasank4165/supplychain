#!/usr/bin/env python3
"""Tag Validation Script for CDK Deployment

This script validates that all resources will be tagged correctly
before deployment. It checks:
- All required tags are present
- Tag keys and values meet AWS requirements
- No reserved tag prefixes are used
- Tag count doesn't exceed limits
"""

import sys
import os
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_manager import ConfigurationManager, TagManager


class TagValidator:
    """Validate tags for CDK deployment"""
    
    def __init__(self, environment: str):
        """Initialize tag validator
        
        Args:
            environment: Environment name (dev, staging, prod)
        """
        self.environment = environment
        self.config = ConfigurationManager(environment=environment)
        self.tag_manager = TagManager(self.config)
        self.errors = []
        self.warnings = []
    
    def validate(self) -> bool:
        """Run all validation checks
        
        Returns:
            True if validation passes, False otherwise
        """
        print(f"Validating tags for environment: {self.environment}")
        print("=" * 60)
        
        # Get all tags
        tags = self.tag_manager.get_tags()
        
        # Run validation checks
        self._validate_required_tags(tags)
        self._validate_tag_count(tags)
        self._validate_tag_format(tags)
        self._validate_cost_allocation_tags(tags)
        
        # Print results
        self._print_results(tags)
        
        return len(self.errors) == 0
    
    def _validate_required_tags(self, tags: dict):
        """Validate that all required tags are present"""
        is_valid, missing_tags = self.tag_manager.validate_required_tags(tags)
        
        if not is_valid:
            self.errors.append(
                f"Missing required tags: {', '.join(missing_tags)}"
            )
        else:
            print("✓ All required tags are present")
    
    def _validate_tag_count(self, tags: dict):
        """Validate tag count doesn't exceed limits"""
        max_tags = self.config.get('tags.validation.max_tags', 50)
        tag_count = len(tags)
        
        if tag_count > max_tags:
            self.errors.append(
                f"Tag count ({tag_count}) exceeds maximum ({max_tags})"
            )
        elif tag_count > 40:
            self.warnings.append(
                f"Tag count ({tag_count}) is approaching maximum ({max_tags})"
            )
        else:
            print(f"✓ Tag count ({tag_count}) is within limits")
    
    def _validate_tag_format(self, tags: dict):
        """Validate tag keys and values meet AWS requirements"""
        invalid_tags = []
        
        for key, value in tags.items():
            if not self.tag_manager._validate_tag(key, value):
                invalid_tags.append(f"{key}={value}")
        
        if invalid_tags:
            self.errors.append(
                f"Invalid tag format: {', '.join(invalid_tags)}"
            )
        else:
            print("✓ All tags meet AWS format requirements")
    
    def _validate_cost_allocation_tags(self, tags: dict):
        """Validate cost allocation tags are present"""
        cost_tags = ['CostCenter', 'Environment', 'Project', 'Owner']
        missing_cost_tags = [tag for tag in cost_tags if tag not in tags]
        
        if missing_cost_tags:
            self.warnings.append(
                f"Missing recommended cost allocation tags: {', '.join(missing_cost_tags)}"
            )
        else:
            print("✓ All cost allocation tags are present")
    
    def _print_results(self, tags: dict):
        """Print validation results"""
        print("\n" + "=" * 60)
        print("Tag Validation Results")
        print("=" * 60)
        
        # Print tag summary
        print(f"\nTotal tags: {len(tags)}")
        print(f"Standard tags: {len(self.tag_manager.get_standard_tags())}")
        print(f"Custom tags: {len(self.tag_manager.get_custom_tags())}")
        
        # Print all tags
        print("\nAll tags:")
        for key, value in sorted(tags.items()):
            print(f"  {key}: {value}")
        
        # Print warnings
        if self.warnings:
            print("\n⚠ Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        # Print errors
        if self.errors:
            print("\n✗ Errors:")
            for error in self.errors:
                print(f"  - {error}")
            print("\nValidation FAILED")
        else:
            print("\n✓ Validation PASSED")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Validate tags for CDK deployment"
    )
    parser.add_argument(
        "--environment",
        "-e",
        required=True,
        choices=["dev", "staging", "prod"],
        help="Environment to validate"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors"
    )
    
    args = parser.parse_args()
    
    # Run validation
    validator = TagValidator(args.environment)
    is_valid = validator.validate()
    
    # Check if we should treat warnings as errors
    if args.strict and validator.warnings:
        print("\n✗ Strict mode: Warnings treated as errors")
        is_valid = False
    
    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
