#!/bin/bash
# PostgreSQL automatic backup script
# Used with cron for regular execution

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

# Activate virtual environment
source venv/bin/activate

# Run backup
python src/kma_pg_backup.py

# Check return code
if [ $? -eq 0 ]; then
    echo "$(date): Backup completed successfully"
else
    echo "$(date): Error during backup execution"
    exit 1
fi
