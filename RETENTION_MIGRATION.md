# Migration Guide: Advanced Retention Policy

This guide explains how to migrate from the simple retention policy to the new advanced multi-level retention policy.

## What's New

The new retention system provides:
- **Multi-level retention**: Different periods for daily, weekly, and monthly backups
- **Separate policies**: Different settings for local and remote storage
- **Automatic classification**: Backups are automatically categorized by age
- **Enhanced cleanup**: More intelligent cleanup with detailed statistics

## Migration Steps

### 1. Update Configuration Files

#### Old Configuration (Legacy)
```yaml
backup:
  retention_days: 30
```

#### New Configuration (Advanced)
```yaml
backup:
  retention:
    local:
      daily: 20
      weekly: 60
      monthly: 540
      max_age: 540
    remote:
      daily: 30
      weekly: 90
      monthly: 730
      max_age: 730
  
  # Legacy setting (for backward compatibility)
  retention_days: 30
```

### 2. Configuration Migration

The system automatically falls back to legacy settings if advanced retention is not configured:

- If `retention` section is missing, uses `retention_days` for all periods
- If `local` or `remote` sections are missing, uses `retention_days`
- If specific periods are missing, uses `max_age` as fallback

### 3. Test New Configuration

```bash
# Activate virtual environment
source venv/bin/activate

# Validate retention configuration
python src/kma_pg_backup.py --validate-retention

# Test cleanup without creating backups
python src/kma_pg_backup.py --cleanup-only --cleanup-storage local
```

### 4. Update Cron Jobs

If you have cron jobs for cleanup, you can now use more specific commands:

#### Old Cron Job
```bash
# Old: Simple cleanup
0 2 * * * /path/to/backup_manager.py
```

#### New Cron Job
```bash
# New: Separate cleanup for different storages
0 2 * * * /path/to/backup_manager.py --cleanup-only --cleanup-storage local
0 3 * * * /path/to/backup_manager.py --cleanup-only --cleanup-storage remote
```

## Configuration Examples

### Production Database
```yaml
retention:
  local:
    daily: 30      # Keep daily backups for 30 days
    weekly: 90     # Keep weekly backups for 90 days
    monthly: 365   # Keep monthly backups for 1 year
    max_age: 365   # Delete everything older than 1 year
  remote:
    daily: 60      # Keep daily backups for 60 days
    weekly: 180    # Keep weekly backups for 6 months
    monthly: 1095  # Keep monthly backups for 3 years
    max_age: 1095  # Delete everything older than 3 years
```

### Staging Database
```yaml
retention:
  local:
    daily: 7       # Keep daily backups for 7 days
    weekly: 30     # Keep weekly backups for 30 days
    monthly: 90    # Keep monthly backups for 3 months
    max_age: 90    # Delete everything older than 3 months
  remote:
    daily: 14      # Keep daily backups for 14 days
    weekly: 60     # Keep weekly backups for 60 days
    monthly: 180   # Keep monthly backups for 6 months
    max_age: 180   # Delete everything older than 6 months
```

## Backup Type Classification

The system automatically classifies backups based on their age:

- **Daily backups**: Files less than 30 days old
- **Weekly backups**: Files 30-90 days old  
- **Monthly backups**: Files 90-365 days old
- **Unknown**: Files older than 365 days (use max_age)

## New Commands

### Cleanup Commands
```bash
# Clean up all storages
python src/kma_pg_backup.py --cleanup-only

# Clean up only local storage
python src/kma_pg_backup.py --cleanup-only --cleanup-storage local

# Clean up only remote storage
python src/kma_pg_backup.py --cleanup-only --cleanup-storage remote
```

### Validation Commands
```bash
# Validate retention configuration
python src/kma_pg_backup.py --validate-retention
```

## Troubleshooting

### Common Issues

1. **Configuration not found**: Make sure `retention` section is properly indented in YAML
2. **Invalid values**: Ensure all retention values are positive integers
3. **Missing sections**: The system will use fallback values, but it's better to be explicit

### Validation

Always validate your configuration before deploying:

```bash
python src/kma_pg_backup.py --validate-retention
```

This will check for:
- Missing required fields
- Invalid values
- Logical consistency (daily ≤ weekly ≤ monthly ≤ max_age)

## Rollback

If you need to rollback to the old system:

1. Remove the `retention` section from your configuration
2. Keep only the `retention_days` setting
3. The system will automatically use the legacy cleanup method

## Support

For questions or issues with the new retention system, please check the logs and use the validation command to identify configuration problems.
