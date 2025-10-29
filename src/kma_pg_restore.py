#!/usr/bin/env python3
"""
PostgreSQL Restore Manager
Version: 1.1.0/1.0.0
Author: Michael BAG
Email: mk@remark.pro
Telegram: https://t.me/michaelbag

Script for restoring PostgreSQL databases from backups
"""

import os
import sys
import json
import yaml
import logging
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from kma_pg_version import get_version


class PostgreSQLRestoreManager:
    """PostgreSQL Restore Manager"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize manager with configuration"""
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()
        
    def _load_config(self) -> Dict:
        """Load configuration from YAML or JSON file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ValueError(f"Configuration file error: {e}")
    
    def _setup_logging(self):
        """Setup logging"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO').upper())
        log_file = log_config.get('file', 'logs/restore.log')
        
        # Create logs directory
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def test_connection(self) -> bool:
        """Test database connection"""
        db_config = self.config['database']
        try:
            conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                user=db_config['username'],
                password=db_config['password']
            )
            conn.close()
            self.logger.info("Database connection successful")
            return True
        except Exception as e:
            self.logger.error(f"Database connection error: {e}")
            return False
    
    def create_database(self, database_name: str) -> bool:
        """Create database"""
        db_config = self.config['database']
        try:
            conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                user=db_config['username'],
                password=db_config['password']
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
            if cursor.fetchone():
                self.logger.warning(f"Database {database_name} already exists")
                cursor.close()
                conn.close()
                return True
            
            # Create database
            cursor.execute(f'CREATE DATABASE "{database_name}"')
            self.logger.info(f"Database {database_name} created")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating database {database_name}: {e}")
            return False
    
    def restore_from_custom(self, backup_file: str, database_name: str) -> bool:
        """Restore from custom format"""
        db_config = self.config['database']
        
        cmd = [
            'pg_restore',
            '-h', db_config['host'],
            '-p', str(db_config['port']),
            '-U', db_config['username'],
            '-d', database_name,
            '--clean',
            '--if-exists',
            backup_file
        ]
        
        env = os.environ.copy()
        if db_config['password']:
            env['PGPASSWORD'] = db_config['password']
        
        try:
            self.logger.info(f"Restoring database {database_name} from {backup_file}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            self.logger.info(f"Database {database_name} successfully restored")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Restore error: {e}")
            self.logger.error(f"Error output: {e.stderr}")
            return False
    
    def restore_from_plain(self, backup_file: str, database_name: str) -> bool:
        """Restore from plain format"""
        db_config = self.config['database']
        
        cmd = [
            'psql',
            '-h', db_config['host'],
            '-p', str(db_config['port']),
            '-U', db_config['username'],
            '-d', database_name,
            '-f', backup_file
        ]
        
        env = os.environ.copy()
        if db_config['password']:
            env['PGPASSWORD'] = db_config['password']
        
        try:
            self.logger.info(f"Restoring database {database_name} from {backup_file}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            self.logger.info(f"Database {database_name} successfully restored")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Restore error: {e}")
            self.logger.error(f"Error output: {e.stderr}")
            return False
    
    def detect_backup_format(self, backup_file: str) -> str:
        """Detect backup format"""
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        # Check file extension
        if backup_path.suffix == '.dump':
            return 'custom'
        elif backup_path.suffix == '.sql':
            return 'plain'
        elif backup_path.suffixes == ['.sql', '.gz']:
            return 'plain'
        else:
            # Try to determine by content
            try:
                with open(backup_file, 'rb') as f:
                    header = f.read(100)
                    if b'PostgreSQL database dump' in header:
                        return 'plain'
                    else:
                        return 'custom'
            except:
                return 'custom'
    
    def restore_database(self, backup_file: str, database_name: str, create_db: bool = True) -> bool:
        """Restore database from backup"""
        if not self.test_connection():
            return False
        
        if create_db:
            if not self.create_database(database_name):
                return False
        
        backup_format = self.detect_backup_format(backup_file)
        self.logger.info(f"Detected backup format: {backup_format}")
        
        if backup_format == 'custom':
            return self.restore_from_custom(backup_file, database_name)
        else:
            return self.restore_from_plain(backup_file, database_name)
    
    def list_backups(self, backup_dir: str = None) -> List[str]:
        """Get list of available backups"""
        if backup_dir is None:
            backup_dir = self.config.get('backup', {}).get('output_dir', 'backups')
        
        backup_path = Path(backup_dir)
        if not backup_path.exists():
            self.logger.warning(f"Backup directory not found: {backup_dir}")
            return []
        
        backup_files = []
        for file_path in backup_path.iterdir():
            if file_path.is_file() and file_path.suffix in ['.dump', '.sql']:
                backup_files.append(str(file_path))
        
        return sorted(backup_files)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='PostgreSQL Restore Manager v1.0.0')
    version = get_version('kma_pg_restore.py')
    parser.add_argument('--version', '-v', action='version', version=f'PostgreSQL Restore Manager v{version}\nAuthor: Michael BAG <mk@remark.pro>\nTelegram: https://t.me/michaelbag')
    parser.add_argument('--config', '-c', default='config/config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--backup-file', '-f',
                       help='Path to backup file')
    parser.add_argument('--database', '-d',
                       help='Database name for restore')
    parser.add_argument('--create-db', '-n', action='store_true',
                       help='Create database before restore')
    parser.add_argument('--list-backups', '-l', action='store_true',
                       help='Show list of available backups')
    
    args = parser.parse_args()
    
    # Check required arguments if not listing backups
    if not args.list_backups:
        if not args.backup_file:
            parser.error("--backup-file/-f is required")
        if not args.database:
            parser.error("--database/-d is required")
    
    try:
        manager = PostgreSQLRestoreManager(args.config)
        
        if args.list_backups:
            backups = manager.list_backups()
            if backups:
                print("Available backups:")
                for backup in backups:
                    print(f"  {backup}")
            else:
                print("No backups found")
            return
        
        if not manager.test_connection():
            sys.exit(1)
        
        success = manager.restore_database(
            args.backup_file,
            args.database,
            args.create_db
        )
        
        if success:
            print(f"Database {args.database} successfully restored")
        else:
            print(f"Error restoring database {args.database}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Critical error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
