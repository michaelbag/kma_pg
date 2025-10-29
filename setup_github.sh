#!/bin/bash

# PostgreSQL Backup Manager - GitHub Setup Script
# This script helps set up the GitHub repository

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "VERSION" ]; then
    print_error "This script must be run from the project root directory"
    exit 1
fi

# Get current version
VERSION=$(cat VERSION)
print_status "Setting up GitHub repository for version $VERSION"

# Check if git is initialized
if [ ! -d ".git" ]; then
    print_error "Git repository not initialized. Run 'git init' first."
    exit 1
fi

# Check if we have commits
if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
    print_error "No commits found. Make at least one commit first."
    exit 1
fi

# Get GitHub username
read -p "Enter your GitHub username: " GITHUB_USERNAME
if [ -z "$GITHUB_USERNAME" ]; then
    print_error "GitHub username is required"
    exit 1
fi

# Get repository name
read -p "Enter repository name (default: kma-pg-backup-manager): " REPO_NAME
REPO_NAME=${REPO_NAME:-kma-pg-backup-manager}

# Check if remote already exists
if git remote get-url origin >/dev/null 2>&1; then
    print_warning "Remote 'origin' already exists:"
    git remote get-url origin
    read -p "Do you want to update it? (y/N): " UPDATE_REMOTE
    if [[ $UPDATE_REMOTE =~ ^[Yy]$ ]]; then
        git remote set-url origin "git@github.com:$GITHUB_USERNAME/$REPO_NAME.git"
        print_success "Updated remote origin"
    fi
else
    # Add remote origin
    git remote add origin "git@github.com:$GITHUB_USERNAME/$REPO_NAME.git"
    print_success "Added remote origin"
fi

# Check SSH key
print_status "Checking SSH key..."
if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    print_success "SSH authentication successful"
    USE_SSH=true
else
    print_warning "SSH authentication failed. Will use HTTPS."
    USE_SSH=false
    git remote set-url origin "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
fi

# Show current status
print_status "Current git status:"
git status --short

# Show remote configuration
print_status "Remote configuration:"
git remote -v

# Ask if user wants to push
read -p "Do you want to push to GitHub now? (y/N): " PUSH_NOW
if [[ $PUSH_NOW =~ ^[Yy]$ ]]; then
    print_status "Pushing to GitHub..."
    
    # Push main branch
    git push -u origin main
    print_success "Pushed main branch"
    
    # Push tags
    git push origin --tags
    print_success "Pushed tags"
    
    print_success "Repository is now available at: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
else
    print_status "Skipping push. You can push later with:"
    echo "  git push -u origin main"
    echo "  git push origin --tags"
fi

# Create release archive if it doesn't exist
if [ ! -f "../kma_pg_v$VERSION.tar.gz" ]; then
    print_status "Creating release archive..."
    tar -czf "../kma_pg_v$VERSION.tar.gz" \
        --exclude='venv' \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='backups' \
        --exclude='logs' \
        .
    print_success "Created release archive: ../kma_pg_v$VERSION.tar.gz"
fi

print_success "GitHub setup completed!"
print_status "Next steps:"
echo "1. Go to https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo "2. Create a new release with tag v$VERSION"
echo "3. Upload the archive file: kma_pg_v$VERSION.tar.gz"
echo "4. Add release notes from CHANGELOG.md"
