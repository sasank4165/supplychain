#!/bin/bash
# Quick commit and push script

echo "=========================================="
echo "Git Commit and Push"
echo "=========================================="
echo ""

# Check if there are changes
if git diff-index --quiet HEAD --; then
    echo "⚠️  No changes to commit"
    echo ""
    echo "Current status:"
    git status
    exit 0
fi

# Show what will be committed
echo "Files to be committed:"
echo "----------------------------------------"
git status --short
echo ""

# Add all changes
echo "Adding all changes..."
git add .
echo "✅ Changes staged"
echo ""

# Commit with message
echo "Creating commit..."
git commit -m "Add environment-specific resource sizing (Task 17.1)

- Added Lambda provisioned concurrency configuration
- Added DynamoDB capacity mode configuration  
- Updated CDK stack to use config values
- Configured dev (0), staging (5), prod (10) provisioned concurrency
- Created validation script and documentation
- Added Git setup files and quick start guide"

if [ $? -eq 0 ]; then
    echo "✅ Commit created successfully"
else
    echo "❌ Commit failed"
    exit 1
fi
echo ""

# Show the commit
echo "Latest commit:"
git log --oneline -1
echo ""

# Check if remote exists
if git remote | grep -q 'origin'; then
    echo "Remote repository found: $(git remote get-url origin)"
    echo ""
    
    # Ask to push
    read -p "Push to remote? (y/n): " push_confirm
    
    if [ "$push_confirm" = "y" ]; then
        echo "Pushing to remote..."
        git push
        
        if [ $? -eq 0 ]; then
            echo "✅ Successfully pushed to remote"
        else
            echo "❌ Push failed"
            echo ""
            echo "Common issues:"
            echo "1. No upstream branch set - try: git push -u origin main"
            echo "2. Authentication required - check your credentials"
            echo "3. Remote branch diverged - try: git pull first"
        fi
    else
        echo "Skipping push"
    fi
else
    echo "⚠️  No remote repository configured"
    echo ""
    echo "To add a remote repository:"
    echo "  git remote add origin <your-repo-url>"
    echo ""
    echo "Example:"
    echo "  git remote add origin https://github.com/yourusername/supplychain.git"
    echo "  git push -u origin main"
fi

echo ""
echo "=========================================="
echo "Done!"
echo "=========================================="
