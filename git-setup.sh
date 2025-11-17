#!/bin/bash
# Git Setup Script for Supply Chain Agent Project
# Run this in Git Bash

echo "=========================================="
echo "Git Setup for Supply Chain Agent Project"
echo "=========================================="
echo ""

# Step 1: Configure Git user (replace with your details)
echo "Step 1: Configuring Git user..."
read -p "Enter your name: " git_name
read -p "Enter your email: " git_email

git config --global user.name "$git_name"
git config --global user.email "$git_email"

echo "✅ Git user configured:"
echo "   Name: $(git config --global user.name)"
echo "   Email: $(git config --global user.email)"
echo ""

# Step 2: Configure Git settings
echo "Step 2: Configuring Git settings..."
git config --global init.defaultBranch main
git config --global core.autocrlf true  # Windows line endings
git config --global pull.rebase false   # Merge strategy
git config --global core.editor "code --wait"  # VS Code as editor (optional)

echo "✅ Git settings configured"
echo ""

# Step 3: Check if already a git repository
if [ -d .git ]; then
    echo "⚠️  Git repository already exists"
    read -p "Do you want to reinitialize? (y/n): " reinit
    if [ "$reinit" != "y" ]; then
        echo "Skipping initialization"
        exit 0
    fi
fi

# Step 4: Initialize repository
echo "Step 3: Initializing Git repository..."
git init
echo "✅ Repository initialized"
echo ""

# Step 5: Check status
echo "Step 4: Checking repository status..."
git status
echo ""

# Step 6: Add all files
echo "Step 5: Adding files to staging..."
git add .
echo "✅ Files staged for commit"
echo ""

# Step 7: Create initial commit
echo "Step 6: Creating initial commit..."
git commit -m "Initial commit: Supply Chain Agent with environment-specific resource sizing

- Implemented CDK infrastructure with multi-environment support
- Added Lambda provisioned concurrency configuration
- Added DynamoDB capacity mode configuration
- Created validation scripts and documentation
- Configured dev, staging, and prod environments"

echo "✅ Initial commit created"
echo ""

# Step 8: Show commit log
echo "Step 7: Commit history..."
git log --oneline -5
echo ""

echo "=========================================="
echo "✅ Git setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Create a GitHub/GitLab repository (if needed)"
echo "2. Add remote: git remote add origin <your-repo-url>"
echo "3. Push code: git push -u origin main"
echo ""
echo "Common Git commands:"
echo "  git status          - Check current status"
echo "  git add <file>      - Stage specific file"
echo "  git add .           - Stage all changes"
echo "  git commit -m 'msg' - Commit staged changes"
echo "  git log             - View commit history"
echo "  git branch          - List branches"
echo "  git checkout -b <name> - Create new branch"
echo ""
