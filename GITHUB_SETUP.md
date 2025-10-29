# GitHub Repository Setup

This guide explains how to set up a GitHub repository for the PostgreSQL Backup Manager project.

## Prerequisites

- Git installed on your system
- GitHub account
- SSH key configured (recommended) or HTTPS access

## Step 1: Create GitHub Repository

1. Go to [GitHub.com](https://github.com) and sign in
2. Click the "+" icon in the top right corner
3. Select "New repository"
4. Fill in the repository details:
   - **Repository name**: `kma-pg-backup-manager`
   - **Description**: `PostgreSQL Backup Manager with Advanced Multi-Level Retention Policy`
   - **Visibility**: Public (recommended) or Private
   - **Initialize repository**: Leave unchecked (we already have files)
5. Click "Create repository"

## Step 2: Connect Local Repository to GitHub

After creating the repository on GitHub, run these commands:

```bash
# Navigate to project directory
cd /Users/mihailkudravcev/Projects/kma_pg

# Add remote origin (replace USERNAME with your GitHub username)
git remote add origin git@github.com:USERNAME/kma-pg-backup-manager.git

# Or use HTTPS if you prefer:
# git remote add origin https://github.com/USERNAME/kma-pg-backup-manager.git

# Push the main branch
git push -u origin main

# Push tags
git push origin --tags
```

## Step 3: Verify Setup

Check that everything is connected properly:

```bash
# Check remote repositories
git remote -v

# Check branch status
git branch -a

# Check tags
git tag -l
```

## Step 4: Create Release on GitHub

1. Go to your repository on GitHub
2. Click "Releases" in the right sidebar
3. Click "Create a new release"
4. Fill in the release details:
   - **Tag version**: `v1.1.0`
   - **Release title**: `PostgreSQL Backup Manager v1.1.0`
   - **Description**: Copy from `CHANGELOG.md`
5. Upload the release archive: `kma_pg_v1.1.0.tar.gz`
6. Click "Publish release"

## Project Structure

The repository contains:

```
kma-pg-backup-manager/
├── src/                          # Python source code
│   ├── kma_pg_backup.py         # Main backup script
│   ├── kma_pg_retention.py      # Advanced retention manager
│   ├── kma_pg_storage.py        # Remote storage manager
│   ├── kma_pg_restore.py        # Database restore script
│   ├── kma_pg_config_setup.py   # Interactive configuration
│   └── kma_pg_config_manager.py # Multi-database config manager
├── config/                       # Configuration examples
│   ├── config.example.yaml      # Main configuration example
│   └── databases/               # Database-specific examples
├── scripts/                      # Utility scripts
├── docs/                        # Documentation
├── README.md                    # Main documentation
├── CHANGELOG.md                 # Version history
├── RETENTION_MIGRATION.md       # Migration guide
├── VERSION                      # Current version
└── requirements.txt             # Python dependencies
```

## Features in v1.1.0

- ✅ Advanced multi-level retention policy
- ✅ Separate local/remote storage policies
- ✅ Automatic backup classification
- ✅ Remote storage cleanup
- ✅ Retention policy validation
- ✅ Enhanced CLI commands
- ✅ Comprehensive documentation
- ✅ Backward compatibility

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes
4. Commit with descriptive messages
5. Push to your fork
6. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Author**: Michael BAG
- **Email**: mk@remark.pro
- **Telegram**: https://t.me/michaelbag
- **Issues**: Use GitHub Issues for bug reports and feature requests