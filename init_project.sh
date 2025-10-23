#!/bin/bash
# PostgreSQL Backup Manager project initialization script

echo "Initializing PostgreSQL Backup Manager project..."

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p logs backups

# Make scripts executable
echo "Setting up permissions..."
chmod +x src/kma_pg_backup.py
chmod +x src/kma_pg_restore.py
chmod +x src/kma_pg_config_setup.py
chmod +x src/kma_pg_config_manager.py
chmod +x scripts/backup_cron.sh

echo "Initialization completed!"
echo ""
echo "To get started:"
echo "1. Create configuration: python src/kma_pg_config_setup.py"
echo "2. Test connection: python src/kma_pg_backup.py --test-connection"
echo "3. Create backup: python src/kma_pg_backup.py"
echo ""
echo "To activate virtual environment use:"
echo "source venv/bin/activate"
