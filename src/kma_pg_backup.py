#!/usr/bin/env python3
"""
PostgreSQL Backup Manager
Version: 1.0.0
Author: Michael BAG
Email: mk@remark.pro
Telegram: https://t.me/michaelbag

Script for automatic backup of PostgreSQL databases
"""

import os
import sys
import json
import yaml
import logging
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from kma_pg_storage import RemoteStorageManager
from kma_pg_config_manager import DatabaseConfigManager


class PostgreSQLBackupManager:
    """PostgreSQL Backup Manager"""
    
    def __init__(self, config_path: str = None, database_name: str = None):
        """Initialize manager with configuration"""
        self.config_manager = DatabaseConfigManager()
        
        if database_name:
            # Use specific database configuration
            self.config = self.config_manager.get_merged_config(database_name)
            if not self.config:
                raise ValueError(f"Database configuration not found: {database_name}")
            self.database_name = database_name
        elif config_path:
            # Use legacy single configuration file
            self.config = self._load_legacy_config(config_path)
            self.database_name = None
        else:
            # Use main configuration (for multi-database mode)
            self.config = self.config_manager.get_main_config()
            self.database_name = None
        
        self._setup_logging()
        self.remote_storage = RemoteStorageManager(self.config)
        
    def _load_legacy_config(self, config_path: str) -> Dict:
        """Load configuration from YAML or JSON file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        except FileNotFoundError:
            raise ValueError(f"Configuration file not found: {config_path}")
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ValueError(f"Configuration file error: {e}")
    
    def _create_default_config(self):
        """Create default configuration"""
        default_config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "username": "postgres",
                "password": "",
                "databases": ["postgres"]
            },
            "backup": {
                "output_dir": "backups",
                "format": "custom",
                "compress": True,
                "retention_days": 30
            },
            "logging": {
                "level": "INFO",
                "file": "logs/backup.log"
            }
        }
        
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True, indent=2)
            else:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
        
        print(f"Default configuration file created: {self.config_path}")
        print("Please edit it before using.")
    
    def _setup_logging(self):
        """Setup logging"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO').upper())
        log_file = log_config.get('file', 'logs/backup.log')
        
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
    
    def test_remote_storage(self) -> bool:
        """Test remote storage connection"""
        if not self.remote_storage.is_enabled():
            self.logger.info("Remote storage is disabled")
            return True
        
        self.logger.info("Testing remote storage connection...")
        if self.remote_storage.test_connection():
            self.logger.info("Remote storage connection successful")
            return True
        else:
            self.logger.error("Remote storage connection failed")
            return False
    
    def get_databases(self, auto_backup_only: bool = False) -> List[str]:
        """Get list of databases"""
        if self.database_name:
            # Single database mode
            return [self.database_name]
        
        # Multi-database mode
        enabled_configs = self.config_manager.get_enabled_databases(auto_backup_only)
        return [config['database']['name'] for config in enabled_configs]
    
    def create_backup(self, database: str) -> Optional[str]:
        """Create database backup"""
        # Get database-specific configuration
        if self.database_name and self.database_name == database:
            # Use current configuration
            db_config = self.config['database']
            backup_config = self.config['backup']
        else:
            # Get configuration for specific database
            db_config_data = self.config_manager.get_merged_config(database)
            if not db_config_data:
                self.logger.error(f"Configuration not found for database: {database}")
                return None
            db_config = db_config_data['database']
            backup_config = db_config_data['backup']
        
        # Create backup directory
        output_dir = Path(backup_config['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_format = backup_config.get('format', 'custom')
        compress = backup_config.get('compress', True)
        
        if backup_format == 'custom':
            extension = '.dump'
        elif backup_format == 'plain':
            extension = '.sql'
        else:
            extension = '.dump'
        
        if compress:
            extension += '.gz'
        
        backup_filename = f"{database}_{timestamp}{extension}"
        backup_path = output_dir / backup_filename
        
        # Build pg_dump command
        cmd = [
            'pg_dump',
            '-h', db_config['host'],
            '-p', str(db_config['port']),
            '-U', db_config['username'],
            '-d', database,
            '-f', str(backup_path)
        ]
        
        if backup_format == 'custom':
            cmd.append('-Fc')
        elif backup_format == 'plain':
            cmd.append('-Fp')
        
        if compress and backup_format != 'custom':
            cmd.extend(['-Z', '9'])
        
        # Set environment variable for password
        env = os.environ.copy()
        if db_config['password']:
            env['PGPASSWORD'] = db_config['password']
        
        try:
            self.logger.info(f"Creating database backup: {database}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            
            if backup_path.exists():
                size = backup_path.stat().st_size
                self.logger.info(f"Backup created: {backup_path} ({size} bytes)")
                
                # Upload to remote storage if enabled
                if self.remote_storage.is_enabled():
                    self.logger.info("Uploading backup to remote storage...")
                    if self.remote_storage.upload_backup(str(backup_path), backup_filename):
                        self.logger.info("Backup successfully uploaded to remote storage")
                    else:
                        self.logger.warning("Failed to upload backup to remote storage")
                
                return str(backup_path)
            else:
                self.logger.error("Backup file not created")
                return None
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Backup creation error: {e}")
            self.logger.error(f"Error output: {e.stderr}")
            return None
    
    def cleanup_old_backups(self):
        """Clean up old backups"""
        backup_config = self.config['backup']
        output_dir = Path(backup_config['output_dir'])
        retention_days = backup_config.get('retention_days', 30)
        
        if not output_dir.exists():
            return
        
        cutoff_date = datetime.now().timestamp() - (retention_days * 24 * 3600)
        deleted_count = 0
        
        for backup_file in output_dir.iterdir():
            if backup_file.is_file() and backup_file.stat().st_mtime < cutoff_date:
                try:
                    backup_file.unlink()
                    deleted_count += 1
                    self.logger.info(f"Deleted old file: {backup_file.name}")
                except Exception as e:
                    self.logger.error(f"Error deleting file {backup_file.name}: {e}")
        
        if deleted_count > 0:
            self.logger.info(f"Deleted {deleted_count} old backup files")
    
    def backup_all_databases(self, auto_backup_only: bool = False):
        """Create backups for all specified databases"""
        if self.database_name:
            # Single database mode
            if not self.test_connection():
                return False
            
            backup_path = self.create_backup(self.database_name)
            if backup_path:
                self.logger.info(f"Successfully created backup for {self.database_name}")
                self.cleanup_old_backups()
                return True
            else:
                return False
        
        # Multi-database mode
        enabled_configs = self.config_manager.get_enabled_databases(auto_backup_only)
        if not enabled_configs:
            if auto_backup_only:
                self.logger.info("No databases configured for automatic backup")
            else:
                self.logger.error("No databases found for backup")
            return False
        
        databases = [config['database']['name'] for config in enabled_configs]
        self.logger.info(f"Found {len(databases)} database(s) for backup: {', '.join(databases)}")
        
        success_count = 0
        for config in enabled_configs:
            database = config['database']['name']
            
            # Test connection for this specific database
            if not self._test_database_connection(config):
                self.logger.error(f"Connection failed for database: {database}")
                continue
            
            backup_path = self.create_backup(database)
            if backup_path:
                success_count += 1
        
        self.logger.info(f"Successfully created {success_count} out of {len(databases)} backups")
        
        # Clean up old backups
        self.cleanup_old_backups()
        
        return success_count > 0
    
    def _test_database_connection(self, config: Dict[str, Any]) -> bool:
        """Test connection to specific database"""
        db_config = config['database']
        try:
            conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'],
                user=db_config['username'],
                password=db_config['password']
            )
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"Database connection error for {db_config['name']}: {e}")
            return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='PostgreSQL Backup Manager v1.0.0')
    parser.add_argument('--version', '-v', action='version', version='PostgreSQL Backup Manager v1.0.0\nAuthor: Michael BAG <mk@remark.pro>\nTelegram: https://t.me/michaelbag')
    parser.add_argument('--config', '-c', default='config/config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--database', '-d', help='Specific database name for backup')
    parser.add_argument('--test-connection', '-t', action='store_true',
                       help='Only test database connection')
    parser.add_argument('--test-remote-storage', '-r', action='store_true',
                       help='Test remote storage connection')
    parser.add_argument('--auto-backup-only', '-a', action='store_true',
                       help='Backup only databases marked for automatic backup')
    parser.add_argument('--database-config', help='Use specific database configuration')
    
    args = parser.parse_args()
    
    try:
        # Determine configuration mode
        if args.database_config:
            # Use specific database configuration
            manager = PostgreSQLBackupManager(database_name=args.database_config)
        elif args.config:
            # Use legacy configuration file
            manager = PostgreSQLBackupManager(config_path=args.config)
        else:
            # Use multi-database configuration
            manager = PostgreSQLBackupManager()
        
        if args.test_connection:
            if manager.test_connection():
                print("Database connection successful")
                sys.exit(0)
            else:
                print("Database connection error")
                sys.exit(1)
        
        if args.test_remote_storage:
            if manager.test_remote_storage():
                print("Remote storage connection successful")
                sys.exit(0)
            else:
                print("Remote storage connection error")
                sys.exit(1)
        
        if args.database:
            # Backup specific database
            if not manager.test_connection():
                sys.exit(1)
            backup_path = manager.create_backup(args.database)
            if backup_path:
                print(f"Backup created: {backup_path}")
            else:
                sys.exit(1)
        else:
            # Backup all databases
            success = manager.backup_all_databases(args.auto_backup_only)
            sys.exit(0 if success else 1)
            
    except Exception as e:
        print(f"Critical error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
