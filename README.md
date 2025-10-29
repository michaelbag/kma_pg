# PostgreSQL Backup Manager

[![Development Status](https://img.shields.io/badge/status-in%20development-orange.svg)](https://github.com/michaelbag/kma_pg)
[![Testing Status](https://img.shields.io/badge/testing-in%20progress-yellow.svg)](https://github.com/michaelbag/kma_pg)
[![License](https://img.shields.io/badge/license-GPL%20v3.0-blue.svg)](https://github.com/michaelbag/kma_pg/blob/main/LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](https://github.com/michaelbag/kma_pg)

**Version:** 1.0.0  
**Author:** Michael BAG  
**Email:** mk@remark.pro  
**Telegram:** https://t.me/michaelbag  
**Status:** 🚧 In Development & Testing

Script application for automatic backup of PostgreSQL databases.

## 🚧 Development Status

**Current Status:** In Development & Testing  
**Version:** 1.0.0 (Beta)  
**Stability:** Under active development  

### Development Roadmap:
- ✅ Core backup functionality implemented
- ✅ Remote storage support (FTP, WebDAV, CIFS/Samba)
- ✅ Multi-database configuration
- ✅ Interactive setup wizard
- 🔄 **Currently testing:** Production environment compatibility
- 🔄 **Currently testing:** Remote storage reliability
- 🔄 **Currently testing:** Error handling and recovery
- 📋 **Planned:** Performance optimization
- 📋 **Planned:** Additional storage providers
- 📋 **Planned:** Web interface for management

### Testing Status:
- 🧪 **Unit tests:** In progress
- 🧪 **Integration tests:** In progress  
- 🧪 **Production testing:** In progress
- 🧪 **Cross-platform testing:** Planned

## Features

- Automatic creation of PostgreSQL database backups
- Support for various backup formats (custom, plain)
- Backup compression
- **Advanced multi-level retention policy for backup cleanup**
- **Separate retention settings for local and remote storage**
- **Support for daily, weekly, and monthly backup retention**
- **Remote storage support (FTP, WebDAV and CIFS/Samba)**
- **Automatic cleanup of remote storage with separate policies**
- Flexible configuration via YAML/JSON file
- Detailed logging
- Database connection testing
- Remote storage connection testing
- **Retention policy validation**

## Installation

> ⚠️ **Warning:** This software is currently in development and testing phase. Use with caution in production environments. Always test thoroughly before deploying.

### Quick Setup

**For Windows users:**
```cmd
# Run the Windows initialization script
init_project_windows.bat
```

**For Linux users:**
```bash
# Run the Linux initialization script
./init_project.sh
```

**For Ubuntu Server 18.04/20.04:**
```bash
# Run the Ubuntu Server specific script
./init_ubuntu_server.sh
```

### Manual Setup

1. Clone or download the project
2. Create and activate virtual environment:

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Windows PowerShell:**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. **Install PostgreSQL and ensure utilities are available in PATH**

   The backup manager requires PostgreSQL client utilities to be installed and accessible:
   - `pg_dump` - for creating database backups
   - `pg_restore` - for restoring database backups  
   - `psql` - for database connections and plain text restore

   **Installation instructions:**
   
   **macOS (using Homebrew):**
   ```bash
   brew install postgresql
   # Add to PATH if needed
   echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```
   
   **Ubuntu/Debian:**
   ```bash
   sudo apt update
   sudo apt install postgresql-client
   ```
   
   **CentOS/RHEL:**
   ```bash
   sudo yum install postgresql
   # or for newer versions
   sudo dnf install postgresql
   ```
   
**Windows:**
- Download and install PostgreSQL from https://www.postgresql.org/download/windows/
- Add PostgreSQL bin directory to system PATH
- **Detailed Windows setup guide:** See [WINDOWS_SETUP.md](WINDOWS_SETUP.md)
   
   **Verify installation:**
   ```bash
   pg_dump --version
   pg_restore --version
   psql --version
   ```

## Configuration

### Advanced Retention Policy

The backup manager now supports advanced multi-level retention policies with separate settings for local and remote storage:

#### Retention Policy Structure

```yaml
backup:
  retention:
    # Local storage retention policy
    local:
      daily: 20      # Keep daily backups for 20 days
      weekly: 60     # Keep weekly backups for 60 days
      monthly: 540   # Keep monthly backups for 18 months
      max_age: 540   # Delete everything older than 18 months
    
    # Remote storage retention policy (can be different)
    remote:
      daily: 30      # Keep daily backups for 30 days
      weekly: 90     # Keep weekly backups for 90 days
      monthly: 730   # Keep monthly backups for 2 years
      max_age: 730   # Delete everything older than 2 years
```

#### Backup Type Classification

The system automatically classifies backups based on:
- **Daily backups**: Files less than 30 days old
- **Weekly backups**: Files 30-90 days old
- **Monthly backups**: Files 90-365 days old
- **Unknown**: Files older than 365 days (use max_age)

#### Retention Policy Benefits

- **Space optimization**: Different retention periods for different backup types
- **Flexible storage**: Separate policies for local and remote storage
- **Cost control**: Shorter retention on expensive local storage
- **Compliance**: Longer retention on remote storage for audit purposes

#### Example Configurations

**Production Database:**
```yaml
retention:
  local:
    daily: 30
    weekly: 90
    monthly: 365
    max_age: 365
  remote:
    daily: 60
    weekly: 180
    monthly: 1095
    max_age: 1095
```

**Staging Database:**
```yaml
retention:
  local:
    daily: 7
    weekly: 30
    monthly: 90
    max_age: 90
  remote:
    daily: 14
    weekly: 60
    monthly: 180
    max_age: 180
```

### Interactive Configuration Setup

Use the interactive configuration wizard to create a new configuration:

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create configuration interactively
python src/kma_pg_config_setup.py

# Or specify output file
python src/kma_pg_config_setup.py -o config/my_config.yaml

# Test existing configuration
python src/kma_pg_config_setup.py -t config/config.yaml
```

The wizard supports two modes:
1. **Single configuration file** (legacy mode)
2. **Multi-database configuration** (recommended for security)

#### Multi-Database Configuration Mode

This mode creates separate configuration files for each database, providing:
- **Individual credentials** for each database
- **Separate remote storage** settings per database
- **Enhanced security** through credential isolation
- **Flexible backup policies** per database

The wizard will guide you through:
- Main configuration settings
- Individual database configurations
- Database-specific backup settings
- Database-specific remote storage setup
- Database-specific logging configuration

All parameters have sensible defaults - just press Enter to use them.

### Using Example Configurations

The project includes example configuration files that you can copy and customize:

```bash
# Copy main configuration example
cp config/config.example.yaml config/config.yaml

# Copy database configuration examples
cp config/databases/example_production.yaml config/databases/production.yaml
cp config/databases/example_staging.yaml config/databases/staging.yaml
cp config/databases/example_development.yaml config/databases/development.yaml
cp config/databases/example_analytics.yaml config/databases/analytics.yaml

# Edit the copied files with your actual settings
nano config/config.yaml
nano config/databases/production.yaml
```

### Database Activity Management

The backup manager supports fine-grained control over database backup activity:

#### Database Configuration Structure
```yaml
databases:
  - name: production_db
    enabled: true          # Database is enabled for backup
    auto_backup: true      # Included in automatic backup
  - name: staging_db
    enabled: true          # Database is enabled for backup
    auto_backup: false     # Manual backup only
  - name: test_db
    enabled: false         # Database is disabled
    auto_backup: false     # Not included in any backup
```

#### Activity Flags
- **`enabled`**: Controls whether the database is included in backup operations
- **`auto_backup`**: Controls whether the database is included in automatic backup (cron jobs)

#### Use Cases
- **Production databases**: `enabled: true, auto_backup: true`
- **Staging databases**: `enabled: true, auto_backup: false` (manual backup only)
- **Test databases**: `enabled: false, auto_backup: false` (excluded from backup)
- **Development databases**: `enabled: true, auto_backup: false` (backup on demand)

### Multi-Database Configuration Structure

When using multi-database mode, the configuration is split into:

```
config/
├── config.yaml              # Main configuration
└── databases/               # Individual database configurations
    ├── production.yaml      # Production database config
    ├── staging.yaml         # Staging database config
    ├── development.yaml     # Development database config
    └── analytics.yaml       # Analytics database config
```

#### Main Configuration (`config/config.yaml`)
```yaml
backup:
  output_dir: backups
  format: custom
  compress: true
  retention_days: 30
  remote_storage:
    enabled: false  # Individual databases can override

logging:
  level: INFO
  file: logs/backup.log
```

#### Database Configuration (`config/databases/production.yaml`)
```yaml
database:
  name: production
  host: prod-db-server.company.com
  port: 5432
  username: backup_user
  password: "secure_production_password"
  enabled: true
  auto_backup: true

backup:
  output_dir: /var/backups/postgresql/production
  format: custom
  compress: true
  retention_days: 90
  remote_storage:
    enabled: true
    type: "webdav"
    webdav:
      url: "https://secure-backup.company.com/backups"
      username: "backup_service"
      password: "webdav_password"
      verify_ssl: true

logging:
  level: INFO
  file: /var/log/postgresql_backup_production.log
```

### Manual Configuration

Edit the `config/config.yaml` file:

```yaml
database:
  host: localhost
  port: 5432
  username: postgres
  password: your_password
  databases:
    - database1
    - database2

backup:
  output_dir: backups
  format: custom
  compress: true
  retention_days: 30

logging:
  level: INFO
  file: logs/backup.log
```

### Configuration Parameters

#### database
- `host` - PostgreSQL server host
- `port` - PostgreSQL server port
- `username` - username
- `password` - user password
- `databases` - list of database configurations:
  - `name` - database name
  - `enabled` - whether database is enabled for backup (default: true)
  - `auto_backup` - whether database is included in automatic backup (default: true)

#### backup
- `output_dir` - directory for saving backups
- `format` - backup format (`custom` or `plain`)
- `compress` - backup compression
- `retention_days` - number of days to keep backups

#### logging
- `level` - logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- `file` - path to log file

## Usage

### Backup all databases
```bash
# Activate virtual environment first
source venv/bin/activate  # On Windows: venv\Scripts\activate

python src/kma_pg_backup.py
```

### Backup specific database
```bash
python src/kma_pg_backup.py --database my_database
# or using short parameter
python src/kma_pg_backup.py -d my_database
```

### Test database connection
```bash
python src/kma_pg_backup.py --test-connection
# or using short parameter
python src/kma_pg_backup.py -t
```

### Test remote storage connection
```bash
python src/kma_pg_backup.py --test-remote-storage
# or using short parameter
python src/kma_pg_backup.py -r
```

### Use custom configuration file
```bash
python src/kma_pg_backup.py --config /path/to/config.yaml
# or using short parameter
python src/kma_pg_backup.py -c /path/to/config.yaml
```

### Automatic backup only
```bash
# Backup only databases marked for automatic backup
python src/kma_pg_backup.py --auto-backup-only
# or using short parameter
python src/kma_pg_backup.py -a
```

### Advanced Retention Management

#### Cleanup old backups
```bash
# Clean up both local and remote storage
python src/kma_pg_backup.py --cleanup-only

# Clean up only local storage
python src/kma_pg_backup.py --cleanup-only --cleanup-storage local

# Clean up only remote storage
python src/kma_pg_backup.py --cleanup-only --cleanup-storage remote
```

#### Validate retention configuration
```bash
# Check retention policy configuration for issues
python src/kma_pg_backup.py --validate-retention
```

#### Multi-database configuration
```bash
# Use specific database configuration
python src/kma_pg_backup.py --database-config production

# Backup all databases with specific config
python src/kma_pg_backup.py --database-config staging --auto-backup-only
```

### Windows Quick Start

**Use the interactive quick start script:**
```cmd
# Run the quick start menu
quick_start_windows.bat
```

**Or run individual commands:**
```cmd
# Activate virtual environment first
venv\Scripts\activate

# Test connection
python src\kma_pg_backup.py --test-connection

# Create backup
python src\kma_pg_backup.py

# Restore database
python src\kma_pg_restore.py --backup-file backups\your_backup.dump --database your_db --create-db
```

### Multi-database configuration
```bash
# Backup all configured databases (multi-database mode)
python src/kma_pg_backup.py

# Backup specific database using its configuration
python src/kma_pg_backup.py --database-config production

# Use legacy single configuration file
python src/kma_pg_backup.py --config config/config.yaml
```

### Configuration management
```bash
# List all configured databases
python src/kma_pg_config_manager.py --list

# Show configuration for specific database
python src/kma_pg_config_manager.py --show production

# Validate database configuration
python src/kma_pg_config_manager.py --validate production
```

## Database Restore

### Restore from backup
```bash
# Activate virtual environment first
source venv/bin/activate  # On Windows: venv\Scripts\activate

python src/kma_pg_restore.py --backup-file backup_file.dump --database target_database --create-db
# or using short parameters
python src/kma_pg_restore.py -f backup_file.dump -d target_database -n
```

### List available backups
```bash
python src/kma_pg_restore.py --list-backups
# or using short parameter
python src/kma_pg_restore.py -l
```

## Remote Storage

The backup manager supports uploading backups to remote storage servers:

### FTP Support
Upload backups to FTP servers:
```yaml
backup:
  remote_storage:
    enabled: true
    type: "ftp"
    ftp:
      host: "ftp.your-server.com"
      port: 21
      username: "your_username"
      password: "your_password"
      remote_dir: "/backups"
      passive_mode: true
      ssl: false
```

### WebDAV Support
Upload backups to WebDAV servers (Nextcloud, OwnCloud, etc.):
```yaml
backup:
  remote_storage:
    enabled: true
    type: "webdav"
    webdav:
      url: "https://your-webdav-server.com/backups"
      username: "your_username"
      password: "your_password"
      verify_ssl: true
```

### CIFS/Samba Support
Upload backups to Samba/CIFS shares:
```yaml
backup:
  remote_storage:
    enabled: true
    type: "cifs"
    cifs:
      server: "//your-samba-server.com/share"
      username: "your_username"
      password: "your_password"
      mount_point: "/mnt/backup_storage"
      auto_mount: true
```

For detailed configuration examples, see [REMOTE_STORAGE.md](REMOTE_STORAGE.md).

## Automation

### Cron (Linux/macOS)
Add to crontab for daily backup at 2:00 AM:
```bash
0 2 * * * cd /path/to/kma_pg && source venv/bin/activate && python src/backup_manager.py
```

### Task Scheduler (Windows)
Create a task in Windows Task Scheduler for automatic execution.

## Project Structure

```
kma_pg/
├── src/
│   ├── kma_pg_backup.py     # Main backup script
│   ├── kma_pg_storage.py    # Remote storage module
│   ├── kma_pg_restore.py    # Restore script
│   ├── kma_pg_config_setup.py # Interactive configuration setup
│   └── kma_pg_config_manager.py # Configuration manager
├── config/
│   ├── config.example.yaml # Example main configuration
│   └── databases/          # Example database configurations
│       ├── example_production.yaml # Example production database config
│       ├── example_staging.yaml   # Example staging database config
│       ├── example_development.yaml # Example development database config
│       └── example_analytics.yaml # Example analytics database config
├── scripts/
│   └── backup_cron.sh       # Linux/macOS cron script
├── logs/                    # Logs
├── backups/                 # Backups
├── venv/                    # Virtual environment
├── init_project.sh          # Linux/macOS initialization script
├── init_ubuntu_server.sh    # Ubuntu Server 18.04/20.04 setup script
├── init_project_windows.bat # Windows batch initialization script
├── init_project_windows.ps1 # Windows PowerShell initialization script
├── quick_start_windows.bat  # Windows quick start menu
├── WINDOWS_SETUP.md         # Detailed Windows setup guide
└── requirements.txt         # Python dependencies
```

## Backup Formats

- **custom** - PostgreSQL binary format (recommended)
- **plain** - text SQL format

## Manual Restore

### Custom format
```bash
pg_restore -h localhost -U postgres -d target_database backup_file.dump
```

### Plain format
```bash
psql -h localhost -U postgres -d target_database -f backup_file.sql
```

## Logging

All operations are logged to `logs/backup.log` file and displayed in console. Logging level is configurable.

## Requirements

### System Requirements
- **Python 3.7+**
- **PostgreSQL 9.0+** with client utilities
- **PostgreSQL client utilities** must be available in system PATH:
  - `pg_dump` - for creating database backups
  - `pg_restore` - for restoring database backups
  - `psql` - for database connections and plain text restore

### Python Dependencies
- psycopg2-binary (PostgreSQL adapter)
- PyYAML (YAML configuration support)
- requests (HTTP client for WebDAV)
- webdavclient3 (WebDAV client)

### Optional Dependencies
- cifs-utils (for CIFS/Samba support)
- ftplib (built-in Python library for FTP)

### Important Notes
- **PostgreSQL server** must be running for backup/restore operations
- **PostgreSQL client utilities** must be installed and accessible via PATH
- If utilities are not found, the script will fail with "command not found" errors
- Virtual environment is required for all Python operations

## Virtual Environment

This project uses Python virtual environment. Always activate it before running scripts:

### Linux/macOS:
```bash
# Activate virtual environment
source venv/bin/activate

# Run scripts
python src/kma_pg_backup.py
python src/kma_pg_restore.py

# Deactivate when done
deactivate
```

### Windows Command Prompt (cmd):
```cmd
# Activate virtual environment
venv\Scripts\activate

# Run scripts
python src\kma_pg_backup.py
python src\kma_pg_restore.py

# Deactivate when done
deactivate
```

### Windows PowerShell:
```powershell
# Activate virtual environment
venv\Scripts\Activate.ps1

# Run scripts
python src\kma_pg_backup.py
python src\kma_pg_restore.py

# Deactivate when done
deactivate
```

### Windows Setup Troubleshooting:

**If you get "execution policy" error in PowerShell:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**If Python is not found:**
- Make sure Python is installed and added to PATH
- Try using `py` instead of `python`:
```cmd
py -m venv venv
venv\Scripts\activate
py src\kma_pg_backup.py
```

**Alternative activation method:**
```cmd
# Direct activation without path
venv\Scripts\activate.bat
```

## Troubleshooting

### PostgreSQL Utilities Not Found

If you get errors like "pg_dump: command not found" or "pg_restore: command not found":

1. **Check if PostgreSQL is installed:**
   ```bash
   which pg_dump
   which pg_restore
   which psql
   ```

2. **If not found, install PostgreSQL:**
   ```bash
   # macOS
   brew install postgresql
   
   # Ubuntu/Debian
   sudo apt install postgresql-client
   
   # CentOS/RHEL
   sudo yum install postgresql
   ```

3. **Add PostgreSQL to PATH if needed:**
   ```bash
   # Find PostgreSQL installation
   find /usr -name "pg_dump" 2>/dev/null
   find /opt -name "pg_dump" 2>/dev/null
   
   # Add to PATH (example for macOS with Homebrew)
   echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

4. **Verify installation:**
   ```bash
   pg_dump --version
   pg_restore --version
   psql --version
   ```

### Database Connection Issues

1. **Test database connection:**
   ```bash
   python src/kma_pg_backup.py --test-connection
   ```

2. **Check PostgreSQL server status:**
   ```bash
   # macOS
   brew services list | grep postgresql
   
   # Linux
   sudo systemctl status postgresql
   ```

3. **Verify configuration:**
   ```bash
   python src/kma_pg_config_manager.py --validate production
   ```

### Common Error Messages

- **"pg_dump: command not found"** → Install PostgreSQL client utilities
- **"Database connection error"** → Check PostgreSQL server status and credentials
- **"Permission denied"** → Check file permissions for backup directory
- **"Remote storage connection failed"** → Verify remote storage configuration

## License

This project is licensed under the GNU General Public License (GPL) v3.0.

### GPL License Summary:
- **Free Software**: You are free to use, modify, and distribute this software
- **Open Source**: Source code must remain open and available
- **Copyleft**: Any derivative works must also be licensed under GPL
- **No Warranty**: Software is provided "as is" without any warranty

### Full License Text:
See [LICENSE](LICENSE) file for the complete GNU General Public License v3.0 text.

### Commercial Use:
This software can be used in commercial projects, but any modifications or distributions must comply with GPL terms.