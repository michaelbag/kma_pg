# Deployment Guide

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/michaelbag/kma_pg.git
cd kma_pg
```

### 2. Setup Environment

#### macOS
```bash
# Install PostgreSQL client tools
brew install postgresql

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Linux (Ubuntu Server)
```bash
# Install system dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv postgresql-client cifs-utils smbclient

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Windows
```cmd
# Install PostgreSQL client tools
# Download from: https://www.postgresql.org/download/windows/

# Setup Python environment
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Initial Configuration

```bash
# Create your first configuration
python src/kma_pg_config_builder.py

# Or use the interactive setup
python src/kma_pg_config_setup.py
```

### 4. Test the Setup

```bash
# Test database connection
python src/kma_pg_backup.py --test-connection

# Test remote storage (if configured)
python src/kma_pg_backup.py --test-remote-storage

# Create your first backup
python src/kma_pg_backup.py
```

## 📋 Production Deployment

### Prerequisites

- **PostgreSQL Server** (9.6+)
- **Python 3.8+**
- **Operating System**: macOS, Linux, or Windows
- **Network Access** to PostgreSQL server
- **Remote Storage** (optional): WebDAV, CIFS/Samba, or FTP

### Step-by-Step Deployment

#### 1. Server Preparation

```bash
# Create application directory
sudo mkdir -p /opt/kma_pg
sudo chown $USER:$USER /opt/kma_pg
cd /opt/kma_pg

# Clone repository
git clone https://github.com/michaelbag/kma_pg.git .
```

#### 2. Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs backups config/databases
```

#### 3. Configuration

```bash
# Create main configuration
cp config/config.example.yaml config/config.yaml

# Edit configuration
nano config/config.yaml

# Create database configurations
python src/kma_pg_config_builder.py
```

#### 4. System Integration

```bash
# Create systemd service (Linux)
sudo cp scripts/kma_pg_backup.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable kma_pg_backup

# Create cron job
crontab -e
# Add: 0 2 * * * /opt/kma_pg/venv/bin/python /opt/kma_pg/src/kma_pg_backup.py
```

#### 5. Testing

```bash
# Test all components
python src/kma_pg_backup.py --test-connection
python src/kma_pg_backup.py --test-remote-storage
python src/kma_pg_backup.py --validate-retention

# Create test backup
python src/kma_pg_backup.py
```

## 🔧 Configuration Examples

### Basic Configuration

```yaml
# config/config.yaml
backup:
  output_dir: /var/backups/postgresql
  format: custom
  compress: true
  retention:
    local:
      daily: 7
      weekly: 30
      monthly: 365
      max_age: 365
    remote:
      daily: 14
      weekly: 60
      monthly: 730
      max_age: 730
  remote_storage:
    enabled: true
    type: "webdav"
    webdav:
      url: "https://your-server.com/remote.php/dav/files/backup/"
      username: "backup_user"
      password: "secure_password"
      verify_ssl: true

logging:
  level: INFO
  file: logs/backup.log
```

### Database Configuration

```yaml
# config/databases/production.yaml
database:
  name: production
  host: db-server.company.com
  port: 5432
  username: backup_user
  password: "secure_password"
  enabled: true
  auto_backup: true

backup:
  output_dir: /var/backups/postgresql/production
  format: custom
  compress: true
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

logging:
  level: INFO
  file: logs/backup_production.log
```

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    cifs-utils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs backups config/databases

# Set permissions
RUN chmod +x src/*.py

# Default command
CMD ["python", "src/kma_pg_backup.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  kma_pg_backup:
    build: .
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
      - ./backups:/app/backups
    environment:
      - PGPASSWORD=your_password
    command: python src/kma_pg_backup.py
    restart: unless-stopped
```

## 🔒 Security Considerations

### 1. File Permissions

```bash
# Secure configuration files
chmod 600 config/config.yaml
chmod 600 config/databases/*.yaml

# Secure backup directory
chmod 700 backups/
```

### 2. Password Management

```bash
# Use environment variables for passwords
export PGPASSWORD="your_password"
export WEBDAV_PASSWORD="your_webdav_password"

# Or use .env file
echo "PGPASSWORD=your_password" > .env
echo "WEBDAV_PASSWORD=your_webdav_password" >> .env
```

### 3. Network Security

- Use SSL/TLS for database connections
- Encrypt backup files before remote storage
- Use VPN or private networks for database access
- Implement proper firewall rules

## 📊 Monitoring and Logging

### 1. Log Configuration

```yaml
logging:
  level: INFO
  file: logs/backup.log
  max_size: 10MB
  backup_count: 5
```

### 2. Monitoring Script

```bash
#!/bin/bash
# monitor_backup.sh

LOG_FILE="logs/backup.log"
ALERT_EMAIL="admin@company.com"

# Check if backup completed successfully
if grep -q "Successfully created backup" "$LOG_FILE"; then
    echo "Backup completed successfully"
else
    echo "Backup failed" | mail -s "Backup Alert" "$ALERT_EMAIL"
fi
```

### 3. Health Check

```bash
#!/bin/bash
# health_check.sh

# Check if backup process is running
if pgrep -f "kma_pg_backup.py" > /dev/null; then
    echo "Backup process is running"
else
    echo "Backup process is not running"
    # Restart service
    systemctl restart kma_pg_backup
fi
```

## 🔄 Backup and Restore

### Backup Configuration

```bash
# Backup all configurations
tar -czf kma_pg_config_backup.tar.gz config/

# Backup with encryption
gpg --symmetric --cipher-algo AES256 kma_pg_config_backup.tar.gz
```

### Restore Configuration

```bash
# Restore configurations
tar -xzf kma_pg_config_backup.tar.gz

# Or from encrypted backup
gpg --decrypt kma_pg_config_backup.tar.gz.gpg | tar -xzf -
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Database Connection Failed
```bash
# Check PostgreSQL service
systemctl status postgresql

# Test connection manually
psql -h your-server -U your-user -d your-database

# Check firewall
telnet your-server 5432
```

#### 2. Remote Storage Issues
```bash
# Test WebDAV connection
curl -u username:password https://your-server.com/remote.php/dav/files/

# Test CIFS connection
smbclient -L //your-server/share -U username

# Test FTP connection
ftp your-server.com
```

#### 3. Permission Issues
```bash
# Fix file permissions
chmod +x src/*.py
chmod 600 config/*.yaml
chmod 700 backups/

# Check ownership
ls -la config/
ls -la backups/
```

### Log Analysis

```bash
# View recent logs
tail -f logs/backup.log

# Search for errors
grep -i error logs/backup.log

# Check backup statistics
grep "Retention cleanup completed" logs/backup.log
```

## 📞 Support

### Getting Help

- **Documentation**: Check README.md and other docs
- **Issues**: Create GitHub issues for bugs
- **Discussions**: Use GitHub discussions for questions
- **Email**: mk@remark.pro
- **Telegram**: https://t.me/michaelbag

### Reporting Issues

When reporting issues, please include:
- Operating system and version
- Python version
- PostgreSQL version
- Error messages and logs
- Steps to reproduce

---

**Repository**: https://github.com/michaelbag/kma_pg  
**Version**: 2.0.0  
**Status**: In Development  
**Last Updated**: October 29, 2025
