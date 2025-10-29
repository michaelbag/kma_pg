#!/usr/bin/env python3
"""
PostgreSQL Backup Manager
Version: 1.1.0/1.0.0
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
from kma_pg_retention import RetentionManager
from kma_pg_version import get_version


class PostgreSQLBackupManager:
    """PostgreSQL Backup Manager"""
    
    def __init__(self, config_path: str = None, database_name: str = None, main_config_path: str = None):
        """Initialize manager with configuration
        
        Args:
            config_path: Legacy single configuration file path (deprecated, use database_name instead)
            database_name: Database configuration name (from config/databases/)
            main_config_path: Optional path to main config file (overrides default config/config.yaml)
        """
        # Initialize config manager with optional main config path
        self.config_manager = DatabaseConfigManager(main_config_path=main_config_path)
        
        if database_name:
            # Use specific database configuration
            self.config = self.config_manager.get_merged_config(database_name)
            if not self.config:
                raise ValueError(f"Database configuration not found: {database_name}")
            self.database_name = database_name
        elif config_path:
            # Use legacy single configuration file (deprecated)
            self.config = self._load_legacy_config(config_path)
            self.database_name = None
        else:
            # Use main configuration (for multi-database mode)
            self.config = self.config_manager.get_main_config()
            self.database_name = None
        
        self._setup_logging()
        self.remote_storage = RemoteStorageManager(self.config)
        self.retention_manager = RetentionManager(self.config, self.logger)
        
        # Get remote retention settings
        self.remote_retention = self.retention_manager.remote_retention
        
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
        
        # Use the actual database name from config, not the config name
        actual_database_name = db_config['name']
        
        # Log the actual database name being used
        self.logger.info(f"Using database name: {actual_database_name} (from config: {database})")
        
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
            '-d', actual_database_name,
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
    
    def cleanup_old_backups(self, storage_type: str = 'local'):
        """
        Clean up old backups using advanced retention policy
        
        Args:
            storage_type: 'local' or 'remote' - which storage to clean up
        """
        backup_config = self.config['backup']
        output_dir = backup_config['output_dir']
        
        # Clean up local storage
        if storage_type == 'local':
            self.logger.info("Starting local storage cleanup...")
            stats = self.retention_manager.cleanup_old_backups(output_dir, 'local')
            
            if stats['deleted'] > 0:
                self.logger.info(f"Local cleanup completed: deleted={stats['deleted']}, "
                               f"kept={stats['kept']}, errors={stats['errors']}")
            else:
                self.logger.info("No files deleted from local storage")
        
        # Clean up remote storage if enabled
        elif storage_type == 'remote' and self.remote_storage.is_enabled():
            self.logger.info("Starting remote storage cleanup...")
            remote_retention = self.remote_retention
            retention_days = remote_retention.get('max_age', 30)
            
            stats = self.remote_storage.cleanup_old_backups(retention_days)
            
            if stats['deleted'] > 0:
                self.logger.info(f"Remote cleanup completed: deleted={stats['deleted']}, "
                               f"kept={stats['kept']}, errors={stats['errors']}")
            else:
                self.logger.info("No files deleted from remote storage")
        
        else:
            self.logger.warning(f"Cleanup skipped for {storage_type} storage")
    
    def cleanup_all_storages(self):
        """Clean up both local and remote storages"""
        self.logger.info("Starting comprehensive cleanup of all storages...")
        
        # Clean up local storage
        self.cleanup_old_backups('local')
        
        # Clean up remote storage if enabled
        if self.remote_storage.is_enabled():
            self.cleanup_old_backups('remote')
        
        # Log retention policy summary
        summary = self.retention_manager.get_retention_summary()
        self.logger.info(f"Retention policy summary: {summary}")
    
    def validate_retention_config(self):
        """Validate retention configuration and log any issues"""
        issues = self.retention_manager.validate_retention_config()
        
        if issues:
            self.logger.warning("Retention configuration issues found:")
            for issue in issues:
                self.logger.warning(f"  - {issue}")
        else:
            self.logger.info("Retention configuration is valid")
    
    def backup_all_databases(self, auto_backup_only: bool = False):
        """Create backups for all specified databases"""
        if self.database_name:
            # Single database mode
            if not self.test_connection():
                return False
            
            backup_path = self.create_backup(self.database_name)
            if backup_path:
                self.logger.info(f"Successfully created backup for {self.database_name}")
                self.cleanup_all_storages()
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
        
        # Clean up old backups for all storages
        self.cleanup_all_storages()
        
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
    version = get_version('kma_pg_backup.py')
    parser = argparse.ArgumentParser(description=f'PostgreSQL Backup Manager v{version}')
    parser.add_argument('--version', '-v', action='version', version=f'PostgreSQL Backup Manager v{version}\nAuthor: Michael BAG <mk@remark.pro>\nTelegram: https://t.me/michaelbag')
    parser.add_argument('--config', '-c', 
                       help='Path to global configuration file (default: config/config.yaml). Used with --database-config to override default global config.')
    parser.add_argument('--database-config', '-d', help='Use specific database configuration (config name from config/databases/)')
    parser.add_argument('--test-connection', '-t', action='store_true',
                       help='Only test database connection')
    parser.add_argument('--test-remote-storage', '-r', action='store_true',
                       help='Test remote storage connection')
    parser.add_argument('--auto-backup-only', '-a', action='store_true',
                       help='Backup only databases marked for automatic backup')
    parser.add_argument('--cleanup-only', action='store_true',
                       help='Only perform cleanup without creating new backups')
    parser.add_argument('--cleanup-storage', choices=['local', 'remote', 'all'], default='all',
                       help='Which storage to clean up (default: all)')
    parser.add_argument('--validate-retention', action='store_true',
                       help='Validate retention configuration and exit')
    
    args = parser.parse_args()
    
    try:
        # Determine configuration mode
        if args.database_config:
            # Use specific database configuration by config name
            # If --config is provided, use it as main config path
            manager = PostgreSQLBackupManager(
                database_name=args.database_config,
                main_config_path=args.config if args.config else None
            )
        elif args.config:
            # Use legacy configuration file (deprecated, use --database-config instead)
            # Check if config file exists and contains database section (legacy format)
            try:
                with open(args.config, 'r', encoding='utf-8') as f:
                    if args.config.endswith(('.yaml', '.yml')):
                        config_data = yaml.safe_load(f)
                    else:
                        config_data = json.load(f)
                
                # If it has database section, treat as legacy single-config file
                if config_data and 'database' in config_data:
                    manager = PostgreSQLBackupManager(config_path=args.config)
                else:
                    # Otherwise treat as main config for multi-database mode
                    manager = PostgreSQLBackupManager(main_config_path=args.config)
            except Exception:
                # Fallback to legacy mode
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
        
        if args.validate_retention:
            manager.validate_retention_config()
            sys.exit(0)
        
        if args.cleanup_only:
            # Only perform cleanup
            if args.cleanup_storage == 'all':
                manager.cleanup_all_storages()
            else:
                manager.cleanup_old_backups(args.cleanup_storage)
            sys.exit(0)
        
        if args.database_config:
            # Backup specific database configuration
            if not manager.test_connection():
                sys.exit(1)
            # Use the actual database name from config, not the config name
            actual_db_name = manager.config['database']['name']
            backup_path = manager.create_backup(actual_db_name)
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
