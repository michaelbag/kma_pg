# Changelog

All notable changes to this project will be documented in this file.

> 🚧 **Project Status:** In Development  
> 📅 **Last Updated:** October 29, 2025

## [2.0.0] - 2025-10-29

### Added
- **Dual-Level Versioning System**: Project and script version management
- **Interactive Configuration Builder**: GUI-like configuration creation with value suggestions
- **Advanced Version Management**: Centralized version control with automatic project updates
- **Comprehensive Status Documentation**: Detailed development status and progress tracking

### New Features
- `kma_pg_version.py`: Version management CLI tool
- `kma_pg_config_builder.py`: Interactive configuration builder
- `STATUS.md`: Detailed project status and development progress
- `VERSIONING.md`: Complete versioning system documentation
- Version display in all CLI tools
- Automatic project version synchronization

### Changed
- **Version Format**: Now uses `project_version/script_version` format
- **All Scripts**: Updated to use new versioning system
- **Documentation**: Enhanced with versioning and status information
- **README**: Updated with development status and new features

### Technical Improvements
- Centralized version storage in JSON format
- Semantic versioning support (major.minor.patch)
- CLI tools for version management
- Integration with all project scripts
- Developer-friendly version management workflow

## [1.1.0] - 2025-10-29

### Added
- **Advanced Multi-Level Retention Policy**: Support for separate retention periods for daily, weekly, and monthly backups
- **Separate Local/Remote Storage Policies**: Different retention settings for local and remote storage
- **Automatic Backup Classification**: System automatically categorizes backups by age and applies appropriate retention
- **Remote Storage Cleanup**: Automatic cleanup of old backups from remote storage (WebDAV, CIFS/Samba, FTP)
- **Retention Policy Validation**: New command to validate retention configuration
- **Enhanced Cleanup Commands**: New CLI options for targeted cleanup operations
- **Comprehensive Logging**: Detailed statistics for cleanup operations

### New Features
- `--cleanup-only`: Perform cleanup without creating new backups
- `--cleanup-storage`: Choose which storage to clean up (local, remote, all)
- `--validate-retention`: Validate retention policy configuration
- Multi-level retention configuration in YAML
- Automatic fallback to legacy retention settings for backward compatibility

### Configuration Changes
- New `retention` section in configuration files
- Support for `daily`, `weekly`, `monthly`, and `max_age` retention periods
- Separate `local` and `remote` retention policies
- Backward compatibility with existing `retention_days` setting

### Documentation
- Updated README with advanced retention policy documentation
- Added migration guide for existing configurations
- Comprehensive examples for different use cases
- New command reference for retention management

### Technical Improvements
- New `RetentionManager` class for advanced retention logic
- Enhanced `RemoteStorageManager` with cleanup capabilities
- Improved error handling and logging
- Better configuration validation

### Example Configuration
```yaml
backup:
  retention:
    local:
      daily: 20      # Keep daily backups for 20 days
      weekly: 60     # Keep weekly backups for 60 days
      monthly: 540   # Keep monthly backups for 18 months
      max_age: 540   # Delete everything older than 18 months
    remote:
      daily: 30      # Keep daily backups for 30 days
      weekly: 90     # Keep weekly backups for 90 days
      monthly: 730   # Keep monthly backups for 2 years
      max_age: 730   # Delete everything older than 2 years
```

## [1.0.0] - 2025-10-28

### Initial Release
- Basic PostgreSQL backup functionality
- Support for custom and plain backup formats
- Backup compression
- Simple retention policy (single retention_days setting)
- Remote storage support (WebDAV, CIFS/Samba, FTP)
- Multi-database configuration support
- Interactive configuration setup
- Database and remote storage connection testing
- Comprehensive logging
- Cross-platform support (Windows, Linux, macOS)
