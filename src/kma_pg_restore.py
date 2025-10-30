#!/usr/bin/env python3
"""
PostgreSQL Restore Manager
Version: 2.0.5/1.1.6
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
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from kma_pg_version import get_version
from kma_pg_config_manager import DatabaseConfigManager
from kma_pg_storage import RemoteStorageManager


class PostgreSQLRestoreManager:
    """PostgreSQL Restore Manager"""
    
    def __init__(self, config_path: str = None, database_name: str = None, main_config_path: str = None):
        """Initialize manager with configuration
        
        Args:
            config_path: Legacy single configuration file path (deprecated)
            database_name: Database configuration name (from config/databases/)
            main_config_path: Optional path to main config file
        """
        self.config_manager = DatabaseConfigManager(main_config_path=main_config_path)
        
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
            # Use main configuration
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
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
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
    
    def drop_database(self, database_name: str) -> bool:
        """Drop database using psql command line"""
        db_config = self.config['database']
        try:
            # Use psql command line to drop database
            # First terminate all connections, then drop database
            terminate_sql = f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{database_name}' AND pid <> pg_backend_pid();
            """
            
            drop_sql = f'DROP DATABASE "{database_name}";'
            
            # Set environment variable for password
            env = os.environ.copy()
            if db_config['password']:
                env['PGPASSWORD'] = db_config['password']
            
            # First, terminate connections using any available database
            # Try to connect to the target database itself for termination
            try:
                terminate_cmd = [
                    'psql',
                    '-h', db_config['host'],
                    '-p', str(db_config['port']),
                    '-U', db_config['username'],
                    '-d', database_name,  # Connect to target database
                    '-c', terminate_sql
                ]
                
                result = subprocess.run(terminate_cmd, env=env, capture_output=True, text=True, check=False)
                if result.returncode != 0:
                    self.logger.warning(f"Could not terminate connections: {result.stderr}")
            except Exception as e:
                self.logger.warning(f"Could not terminate connections: {e}")
            
            # Now try to drop database using template1 or postgres
            databases_to_try = ['template1', 'postgres', 'template0']
            drop_success = False
            
            for db_name in databases_to_try:
                try:
                    drop_cmd = [
                        'psql',
                        '-h', db_config['host'],
                        '-p', str(db_config['port']),
                        '-U', db_config['username'],
                        '-d', db_name,
                        '-c', drop_sql
                    ]
                    
                    result = subprocess.run(drop_cmd, env=env, capture_output=True, text=True, check=False)
                    if result.returncode == 0:
                        self.logger.info(f"Database {database_name} dropped successfully")
                        drop_success = True
                        break
                    else:
                        self.logger.debug(f"Failed to drop from {db_name}: {result.stderr}")
                        
                except Exception as e:
                    self.logger.debug(f"Failed to connect to {db_name}: {e}")
                    continue
            
            if not drop_success:
                # Check if database still exists
                check_cmd = [
                    'psql',
                    '-h', db_config['host'],
                    '-p', str(db_config['port']),
                    '-U', db_config['username'],
                    '-d', 'template1',
                    '-c', f"SELECT 1 FROM pg_database WHERE datname = '{database_name}';"
                ]
                
                result = subprocess.run(check_cmd, env=env, capture_output=True, text=True, check=False)
                if result.returncode == 0 and not result.stdout.strip():
                    # Database doesn't exist, consider it dropped
                    self.logger.info(f"Database {database_name} does not exist (already dropped)")
                    return True
                else:
                    raise Exception(f"Could not drop database {database_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error dropping database: {e}")
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
            '--no-owner',
            '--no-privileges',
            '--disable-triggers',
            '--single-transaction',
            backup_file
        ]
        
        env = os.environ.copy()
        if db_config['password']:
            env['PGPASSWORD'] = db_config['password']
        
        try:
            self.logger.info(f"Restoring database {database_name} from {backup_file}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)
            
            # Check if restore was successful or only had minor errors (extensions)
            if result.returncode == 0:
                self.logger.info(f"Database {database_name} successfully restored")
                return True
            else:
                # Check if errors are only about extensions (adminpack, etc.)
                extension_errors = [
                    'must be owner of extension',
                    'extension adminpack',
                    'extension pg_',
                    'pg_restore: warning: errors ignored on restore'
                ]
                
                # Count non-extension errors
                has_critical_errors = False
                for line in result.stderr.split('\n'):
                    if 'error:' in line.lower() and not any(ext_err in line.lower() for ext_err in extension_errors):
                        has_critical_errors = True
                        break
                
                if not has_critical_errors:
                    # Only extension errors, consider restore successful
                    self.logger.warning(f"Restore completed with extension warnings (these are safe to ignore)")
                    self.logger.info(f"Database {database_name} successfully restored")
                    return True
                else:
                    # Critical errors occurred
                    self.logger.error(f"Restore error: {result.stderr}")
                    return False
            
        except Exception as e:
            self.logger.error(f"Restore error: {e}")
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
    
    def restore_database(self, backup_file: str, database_name: str, create_db: bool = True, clean_db: bool = False) -> bool:
        """Restore database from backup"""
        if not self.test_connection():
            return False
        
        if clean_db:
            # Drop and recreate database
            if not self.drop_database(database_name):
                return False
            if not self.create_database(database_name):
                return False
        elif create_db:
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
            if file_path.is_file():
                # Check for backup file extensions (including compressed)
                if (file_path.suffix in ['.dump', '.sql'] or 
                    file_path.suffixes in [['.dump', '.gz'], ['.sql', '.gz']]):
                    backup_files.append(str(file_path))
        
        return sorted(backup_files)
    
    def download_from_remote_storage(self, remote_filename: str) -> Optional[str]:
        """Download backup file from remote storage"""
        if not self.remote_storage.is_enabled():
            self.logger.error("Remote storage is not enabled")
            return None
        
        try:
            # Determine file extension from remote filename
            remote_path = Path(remote_filename)
            if remote_path.suffixes == ['.sql', '.gz']:
                suffix = '.sql.gz'
            elif remote_path.suffixes == ['.dump', '.gz']:
                suffix = '.dump.gz'
            elif remote_path.suffix == '.sql':
                suffix = '.sql'
            elif remote_path.suffix == '.dump':
                suffix = '.dump'
            else:
                suffix = '.dump'  # Default fallback
            
            # Create temporary file with correct extension
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_path = temp_file.name
            temp_file.close()
            
            # Download file from remote storage
            if self.remote_storage.download_backup(remote_filename, temp_path):
                self.logger.info(f"Downloaded {remote_filename} from remote storage")
                return temp_path
            else:
                self.logger.error(f"Failed to download {remote_filename} from remote storage")
                return None
        except Exception as e:
            self.logger.error(f"Error downloading from remote storage: {e}")
            return None
    
    def list_remote_backups(self) -> List[str]:
        """List available backups in remote storage"""
        if not self.remote_storage.is_enabled():
            self.logger.error("Remote storage is not enabled")
            return []
        
        try:
            return self.remote_storage.list_backups()
        except Exception as e:
            self.logger.error(f"Error listing remote backups: {e}")
            return []
    
    def restore_from_remote(self, remote_filename: str, target_database: str, create_db: bool = False, clean_db: bool = False) -> bool:
        """Restore database from remote backup file"""
        # Download backup file
        local_file = self.download_from_remote_storage(remote_filename)
        if not local_file:
            return False
        
        try:
            # Restore from local file
            success = self.restore_database(local_file, target_database, create_db, clean_db)
            return success
        finally:
            # Clean up temporary file
            try:
                os.unlink(local_file)
            except Exception:
                pass


def main():
    """Main function"""
    version = get_version('kma_pg_restore.py')
    parser = argparse.ArgumentParser(description=f'PostgreSQL Restore Manager v{version}')
    parser.add_argument('--version', '-v', action='version', version=f'PostgreSQL Restore Manager v{version}\nAuthor: Michael BAG <mk@remark.pro>\nTelegram: https://t.me/michaelbag')
    parser.add_argument('--config', '-c', 
                       help='Path to global configuration file (default: config/config.yaml). Used with --database-config to override default global config.')
    parser.add_argument('--database-config', '-D', help='Use specific database configuration (config name from config/databases/)')
    parser.add_argument('--backup-file', '-f', help='Path to backup file (local or remote filename)')
    parser.add_argument('--database', '-d', help='Database name for restore')
    parser.add_argument('--create-db', '-n', action='store_true', help='Create database before restore')
    parser.add_argument('--clean-db', '-X', action='store_true', help='Clean database before restore (drop and recreate)')
    parser.add_argument('--remote-storage', '-r', action='store_true', help='Restore from remote storage')
    parser.add_argument('--list-backups', '-l', action='store_true', help='Show list of available backups')
    parser.add_argument('--list-remote', '-R', action='store_true', help='Show list of remote backups')
    
    args = parser.parse_args()
    
    # Check required arguments if not listing backups
    if not args.list_backups and not args.list_remote:
        if not args.backup_file:
            parser.error("--backup-file/-f is required")
        if not args.database and not args.database_config:
            parser.error("--database/-d or --database-config is required")
    
    try:
        # Determine configuration mode
        if args.database_config:
            # Use specific database configuration
            manager = PostgreSQLRestoreManager(
                database_name=args.database_config,
                main_config_path=args.config if args.config else None
            )
        elif args.config:
            # Use legacy configuration file
            manager = PostgreSQLRestoreManager(config_path=args.config)
        else:
            # Use main configuration
            manager = PostgreSQLRestoreManager()
        
        if args.list_backups:
            backups = manager.list_backups()
            if backups:
                print("Available local backups:")
                for backup in backups:
                    print(f"  {backup}")
            else:
                print("No local backups found")
            return
        
        if args.list_remote:
            backups = manager.list_remote_backups()
            if backups:
                print("Available remote backups:")
                for backup in backups:
                    print(f"  {backup}")
            else:
                print("No remote backups found")
            return
        
        # Determine target database
        if args.database:
            target_database = args.database
        elif args.database_config:
            target_database = manager.config['database']['name']
        else:
            target_database = args.database
        
        if not manager.test_connection():
            sys.exit(1)
        
        # Perform restore
        if args.remote_storage:
            success = manager.restore_from_remote(
                args.backup_file,
                target_database,
                args.create_db,
                args.clean_db
            )
        else:
            success = manager.restore_database(
                args.backup_file,
                target_database,
                args.create_db,
                args.clean_db
            )
        
        if success:
            print(f"Database {target_database} successfully restored")
        else:
            print(f"Failed to restore database {target_database}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
