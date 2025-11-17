# Git Quick Start Guide

## Initial Setup (One-Time)

Since you're using Git for the first time, follow these steps in **Git Bash**:

### 1. Open Git Bash
- Right-click in your project folder
- Select "Git Bash Here"
- Or navigate to your project: `cd /c/Users/sasan/Supply_Chain/supplychain`

### 2. Run the Setup Script
```bash
bash git-setup.sh
```

This will:
- Configure your Git username and email
- Initialize the repository
- Create your first commit with all current files

### 3. Manual Setup (Alternative)

If you prefer to do it manually:

```bash
# Configure your identity
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Configure settings
git config --global init.defaultBranch main
git config --global core.autocrlf true

# Initialize repository
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit: Supply Chain Agent project"
```

## Daily Git Workflow

### Check Status
```bash
git status
```

### Stage Changes
```bash
# Stage specific files
git add cdk/supply_chain_stack.py
git add config/prod.yaml

# Stage all changes
git add .

# Stage all Python files
git add *.py
```

### Commit Changes
```bash
# Commit with message
git commit -m "Add environment-specific resource sizing"

# Commit with detailed message
git commit -m "Add Lambda provisioned concurrency

- Added provisioned_concurrency configuration
- Updated CDK stack to support warm instances
- Configured dev (0), staging (5), prod (10)"
```

### View History
```bash
# View commit log
git log

# View compact log
git log --oneline

# View last 5 commits
git log --oneline -5

# View changes in a commit
git show <commit-hash>
```

### View Changes
```bash
# See unstaged changes
git diff

# See staged changes
git diff --staged

# See changes in specific file
git diff cdk/config.py
```

### Undo Changes
```bash
# Discard changes in working directory
git checkout -- <file>

# Unstage a file (keep changes)
git reset HEAD <file>

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes) - CAREFUL!
git reset --hard HEAD~1
```

## Working with Branches

### Create and Switch Branches
```bash
# Create new branch
git branch feature/new-feature

# Switch to branch
git checkout feature/new-feature

# Create and switch in one command
git checkout -b feature/new-feature

# List all branches
git branch

# Delete branch
git branch -d feature/new-feature
```

### Merge Branches
```bash
# Switch to main branch
git checkout main

# Merge feature branch into main
git merge feature/new-feature
```

## Working with Remote Repository (GitHub/GitLab)

### First Time Setup
```bash
# Add remote repository
git remote add origin https://github.com/yourusername/supplychain.git

# Verify remote
git remote -v

# Push to remote (first time)
git push -u origin main
```

### Regular Push/Pull
```bash
# Push changes to remote
git push

# Pull changes from remote
git pull

# Fetch changes without merging
git fetch
```

## Common Scenarios

### Scenario 1: Save Your Current Work
```bash
git add .
git commit -m "Implement task 17.1: environment-specific resource sizing"
git push
```

### Scenario 2: Create Feature Branch
```bash
# Create branch for new feature
git checkout -b feature/task-17.2

# Make changes...
git add .
git commit -m "Work in progress on task 17.2"

# Switch back to main
git checkout main
```

### Scenario 3: View What Changed
```bash
# See what files changed
git status

# See actual changes
git diff

# See changes in last commit
git show
```

### Scenario 4: Fix a Mistake
```bash
# Oops, forgot to add a file to last commit
git add forgotten-file.py
git commit --amend --no-edit

# Oops, wrong commit message
git commit --amend -m "Correct message"
```

## Git Best Practices

1. **Commit Often**: Make small, focused commits
2. **Write Good Messages**: Describe what and why, not how
3. **Use Branches**: Keep main branch stable
4. **Pull Before Push**: Always pull latest changes first
5. **Review Before Commit**: Use `git status` and `git diff`

## Commit Message Format

Good commit messages follow this pattern:

```
Short summary (50 chars or less)

More detailed explanation if needed. Wrap at 72 characters.
Explain what changed and why, not how.

- Bullet points are okay
- Use present tense: "Add feature" not "Added feature"
- Reference issues: "Fixes #123"
```

Example:
```bash
git commit -m "Add Lambda provisioned concurrency support

Implements environment-specific provisioned concurrency for Lambda
functions to reduce cold start latency in production environments.

- Dev: 0 instances (disabled)
- Staging: 5 instances
- Prod: 10 instances

Addresses requirement 6.1 from design document."
```

## Useful Git Aliases

Add these to make Git easier:

```bash
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.unstage 'reset HEAD --'
git config --global alias.last 'log -1 HEAD'
git config --global alias.visual 'log --oneline --graph --decorate --all'
```

Now you can use:
```bash
git st          # instead of git status
git co main     # instead of git checkout main
git br          # instead of git branch
git ci -m "msg" # instead of git commit -m "msg"
git visual      # pretty commit graph
```

## Getting Help

```bash
# General help
git help

# Help for specific command
git help commit
git help branch

# Quick reference
git <command> --help
```

## Next Steps

1. ✅ Run `bash git-setup.sh` to initialize your repository
2. ✅ Make your first commit
3. 📝 Create a GitHub/GitLab account (if you don't have one)
4. 🔗 Create a remote repository
5. 🚀 Push your code: `git push -u origin main`

## Troubleshooting

### "Git is not recognized"
- Make sure you're using Git Bash, not PowerShell/CMD
- Or add Git to your PATH environment variable

### "Permission denied (publickey)"
- Set up SSH keys for GitHub/GitLab
- Or use HTTPS with personal access token

### "Merge conflict"
```bash
# View conflicted files
git status

# Edit files to resolve conflicts
# Look for <<<<<<< HEAD markers

# After resolving
git add <resolved-files>
git commit
```

### "Detached HEAD state"
```bash
# Create a branch from current state
git checkout -b recovery-branch

# Or discard and go back to main
git checkout main
```

## Resources

- [Git Documentation](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)
- [Interactive Git Tutorial](https://learngitbranching.js.org/)

---

**Remember**: Git is a safety net. Don't be afraid to experiment - you can always undo changes!
