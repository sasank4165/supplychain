#!/bin/bash
# Build Lambda Layer with dependencies

echo "Building Lambda Layer..."

# Create python directory if it doesn't exist
mkdir -p python

# Install dependencies into python/ directory
pip install -r requirements.txt -t python/

echo "Lambda layer built successfully in python/ directory"
