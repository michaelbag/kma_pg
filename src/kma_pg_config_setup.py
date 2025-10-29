#!/usr/bin/env python3
"""
PostgreSQL Backup Manager - Configuration Setup
Version: 1.1.0
Author: Michael BAG
Email: mk@remark.pro
Telegram: https://t.me/michaelbag

Interactive configuration creation with default values
"""

import os
import sys
import yaml
import json
import getpass
from pathlib import Path
from typing import Dict, Any, List

from kma_pg_config_manager import DatabaseConfigManager


class ConfigSetup:
    """Interactive configuration setup manager"""
    
    def __init__(self):
        """Initialize configuration setup"""
        self.config_manager = DatabaseConfigManager()
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        
    def get_input(self, prompt: str, default: str = None, required: bool = True) -> str:
        """Get user input with default value"""
        if default:
            full_prompt = f"{prompt} [{default}]: "
        else:
            full_prompt = f"{prompt}: "
            
        while True:
            value = input(full_prompt).strip()
            if value:
                return value
            elif default and not required:
                return default
            elif not required:
                return ""
            else:
                print("This field is required. Please enter a value.")
    
    def get_boolean_input(self, prompt: str, default: bool = True) -> bool:
        """Get boolean input with default value"""
        default_str = "Y/n" if default else "y/N"
        while True:
            value = input(f"{prompt} [{default_str}]: ").strip().lower()
            if value in ['y', 'yes', '']:
                return True
            elif value in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
    
    def get_list_input(self, prompt: str, default: List[str] = None) -> List[str]:
        """Get list input with default values"""
        if default:
            print(f"{prompt} (comma-separated, press Enter for default: {', '.join(default)})")
        else:
            print(f"{prompt} (comma-separated, leave empty for all databases)")
        
        value = input(": ").strip()
        if value:
            return [item.strip() for item in value.split(',') if item.strip()]
        elif default:
            return default
        else:
            return []
    
    def get_number_input(self, prompt: str, default: int = None, min_val: int = None, max_val: int = None) -> int:
        """Get number input with validation"""
        while True:
            value = input(f"{prompt} [{default}]: " if default else f"{prompt}: ").strip()
            if not value and default is not None:
                return default
            
            try:
                num = int(value)
                if min_val is not None and num < min_val:
                    print(f"Value must be at least {min_val}")
                    continue
                if max_val is not None and num > max_val:
                    print(f"Value must be at most {max_val}")
                    continue
                return num
            except ValueError:
                print("Please enter a valid number.")
    
    def setup_database_config(self) -> Dict[str, Any]:
        """Setup database configuration"""
        print("\n=== Database Configuration ===")
        
        config = {
            'host': self.get_input("PostgreSQL host", "localhost"),
            'port': self.get_number_input("PostgreSQL port", 5432, 1, 65535),
            'username': self.get_input("PostgreSQL username", "postgres"),
            'password': getpass.getpass("PostgreSQL password: "),
            'databases': self.setup_databases_list()
        }
        
        return config
    
    def setup_databases_list(self) -> List[Dict[str, Any]]:
        """Setup databases list with activity flags"""
        print("\n--- Database List Configuration ---")
        print("Configure databases for backup. Each database can be:")
        print("- enabled/disabled")
        print("- included/excluded from automatic backup")
        print()
        
        databases = []
        
        # Get initial database list
        db_list = self.get_list_input("Database names (comma-separated, leave empty for all)", [])
        
        if not db_list:
            # If no specific databases, use all available
            print("No specific databases configured. All databases will be included.")
            return []
        
        # Configure each database
        for db_name in db_list:
            print(f"\n--- Configuring database: {db_name} ---")
            
            enabled = self.get_boolean_input(f"Enable backup for database '{db_name}'", True)
            auto_backup = True
            
            if enabled:
                auto_backup = self.get_boolean_input(f"Include '{db_name}' in automatic backup", True)
            
            databases.append({
                'name': db_name,
                'enabled': enabled,
                'auto_backup': auto_backup
            })
            
            status = "enabled" if enabled else "disabled"
            auto_status = "automatic" if auto_backup else "manual only"
            print(f"Database '{db_name}': {status}, {auto_status}")
        
        return databases
    
    def setup_multi_database_config(self) -> bool:
        """Setup multiple database configurations"""
        print("\n=== Multi-Database Configuration Setup ===")
        print("This mode creates separate configuration files for each database.")
        print("Each database can have its own connection credentials and remote storage settings.")
        print()
        
        use_multi = self.get_boolean_input("Use multi-database configuration mode", True)
        if not use_multi:
            return False
        
        # Setup main configuration
        print("\n--- Main Configuration ---")
        main_config = {
            'backup': self.setup_backup_config(),
            'logging': self.setup_logging_config()
        }
        
        # Save main configuration
        self.config_manager.save_main_config(main_config)
        print(f"✅ Main configuration saved to: {self.config_manager.main_config_path}")
        
        # Setup individual database configurations
        print("\n--- Database Configurations ---")
        databases = []
        
        while True:
            db_name = self.get_input("Database name (leave empty to finish)", required=False)
            if not db_name:
                break
            
            print(f"\n--- Configuring database: {db_name} ---")
            
            # Check if database already exists
            existing_config = self.config_manager.get_database_config(db_name)
            if existing_config:
                overwrite = self.get_boolean_input(f"Database '{db_name}' already exists. Overwrite?", False)
                if not overwrite:
                    continue
            
            # Setup database configuration
            db_config = self.setup_single_database_config(db_name)
            
            # Validate configuration
            errors = self.config_manager.validate_database_config(db_config)
            if errors:
                print(f"❌ Configuration errors for '{db_name}':")
                for error in errors:
                    print(f"  - {error}")
                continue
            
            # Save database configuration
            self.config_manager.save_database_config(db_name, db_config)
            print(f"✅ Database configuration saved: {db_name}")
            databases.append(db_name)
        
        if databases:
            print(f"\n🎉 Multi-database configuration completed!")
            print(f"📁 Configured databases: {', '.join(databases)}")
            print(f"📁 Main config: {self.config_manager.main_config_path}")
            print(f"📁 Database configs: {self.config_manager.databases_dir}")
            return True
        else:
            print("❌ No databases configured")
            return False
    
    def setup_single_database_config(self, database_name: str) -> Dict[str, Any]:
        """Setup configuration for a single database"""
        print(f"\n--- Database Configuration: {database_name} ---")
        
        # Database connection settings
        db_config = {
            'name': database_name,
            'host': self.get_input("PostgreSQL host", "localhost"),
            'port': self.get_number_input("PostgreSQL port", 5432, 1, 65535),
            'username': self.get_input("PostgreSQL username", "postgres"),
            'password': getpass.getpass("PostgreSQL password: "),
            'enabled': self.get_boolean_input("Enable backup for this database", True),
            'auto_backup': True
        }
        
        if db_config['enabled']:
            db_config['auto_backup'] = self.get_boolean_input("Include in automatic backup", True)
        
        # Database-specific backup settings
        print(f"\n--- Backup Settings for {database_name} ---")
        use_custom_backup = self.get_boolean_input("Use custom backup settings for this database", False)
        
        if use_custom_backup:
            backup_config = {
                'output_dir': self.get_input("Backup output directory", "backups"),
                'format': self.get_input("Backup format (custom/plain)", "custom"),
                'compress': self.get_boolean_input("Enable compression", True),
                'retention_days': self.get_number_input("Retention days", 30, 1, 365),
                'remote_storage': self.setup_remote_storage_config()
            }
        else:
            backup_config = {
                'remote_storage': self.setup_remote_storage_config()
            }
        
        # Database-specific logging settings
        print(f"\n--- Logging Settings for {database_name} ---")
        use_custom_logging = self.get_boolean_input("Use custom logging settings for this database", False)
        
        if use_custom_logging:
            logging_config = {
                'level': self.get_input("Log level (DEBUG/INFO/WARNING/ERROR)", "INFO"),
                'file': self.get_input("Log file path", f"logs/backup_{database_name}.log")
            }
        else:
            logging_config = {}
        
        # Combine configuration
        config = {
            'database': db_config,
            'backup': backup_config,
            'logging': logging_config
        }
        
        return config
    
    def setup_backup_config(self) -> Dict[str, Any]:
        """Setup backup configuration"""
        print("\n=== Backup Configuration ===")
        
        config = {
            'output_dir': self.get_input("Backup output directory", "backups"),
            'format': self.get_input("Backup format (custom/plain)", "custom"),
            'compress': self.get_boolean_input("Enable compression", True),
            'retention_days': self.get_number_input("Retention days", 30, 1, 365),
            'remote_storage': self.setup_remote_storage_config()
        }
        
        return config
    
    def setup_remote_storage_config(self) -> Dict[str, Any]:
        """Setup remote storage configuration"""
        print("\n=== Remote Storage Configuration ===")
        
        enabled = self.get_boolean_input("Enable remote storage", False)
        if not enabled:
            return {'enabled': False}
        
        storage_type = self.get_input("Storage type (webdav/cifs/ftp)", "webdav")
        
        config = {
            'enabled': True,
            'type': storage_type
        }
        
        if storage_type == 'webdav':
            config['webdav'] = {
                'url': self.get_input("WebDAV URL", "https://your-webdav-server.com/backups"),
                'username': self.get_input("WebDAV username"),
                'password': getpass.getpass("WebDAV password: "),
                'verify_ssl': self.get_boolean_input("Verify SSL certificate", True)
            }
        elif storage_type == 'cifs':
            config['cifs'] = {
                'server': self.get_input("CIFS server", "//your-samba-server.com/share"),
                'username': self.get_input("CIFS username"),
                'password': getpass.getpass("CIFS password: "),
                'mount_point': self.get_input("Mount point", "/mnt/backup_storage"),
                'auto_mount': self.get_boolean_input("Auto mount", True)
            }
        elif storage_type == 'ftp':
            config['ftp'] = {
                'host': self.get_input("FTP host", "ftp.your-server.com"),
                'port': self.get_number_input("FTP port", 21, 1, 65535),
                'username': self.get_input("FTP username"),
                'password': getpass.getpass("FTP password: "),
                'passive': self.get_boolean_input("Passive mode", True),
                'ssl': self.get_boolean_input("Use SSL/TLS", False)
            }
        
        return config
    
    def setup_logging_config(self) -> Dict[str, Any]:
        """Setup logging configuration"""
        print("\n=== Logging Configuration ===")
        
        config = {
            'level': self.get_input("Log level (DEBUG/INFO/WARNING/ERROR)", "INFO"),
            'file': self.get_input("Log file path", "logs/backup.log")
        }
        
        return config
    
    def create_config(self, config_path: str = None) -> str:
        """Create configuration interactively"""
        print("PostgreSQL Backup Manager - Configuration Setup")
        print("=" * 50)
        print("This wizard will help you create a configuration file.")
        print("Press Enter to use default values (shown in brackets).")
        print()
        
        # Choose configuration mode
        print("Configuration modes:")
        print("1. Single configuration file (legacy mode)")
        print("2. Multi-database configuration (recommended)")
        print()
        
        mode = self.get_input("Choose mode (1 or 2)", "2")
        
        if mode == "2":
            # Multi-database configuration
            if self.setup_multi_database_config():
                return str(self.config_manager.main_config_path)
            else:
                print("❌ Multi-database configuration failed")
                sys.exit(1)
        else:
            # Single configuration file (legacy mode)
            return self.create_legacy_config(config_path)
    
    def create_legacy_config(self, config_path: str = None) -> str:
        """Create legacy single configuration file"""
        print("\n=== Legacy Single Configuration Mode ===")
        
        # Setup configuration sections
        database_config = self.setup_database_config()
        backup_config = self.setup_backup_config()
        logging_config = self.setup_logging_config()
        
        # Create full configuration
        config = {
            'database': database_config,
            'backup': backup_config,
            'logging': logging_config
        }
        
        # Determine output path
        if not config_path:
            config_name = self.get_input("Configuration file name", "config.yaml")
            if not config_name.endswith(('.yaml', '.yml', '.json')):
                config_name += '.yaml'
            config_path = self.config_dir / config_name
        else:
            config_path = Path(config_path)
        
        # Save configuration
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            if config_path.suffix in ['.yaml', '.yml']:
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, indent=2, allow_unicode=True)
            else:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Configuration saved to: {config_path}")
            return str(config_path)
            
        except Exception as e:
            print(f"❌ Error saving configuration: {e}")
            sys.exit(1)
    
    def test_config(self, config_path: str) -> bool:
        """Test configuration file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.endswith(('.yaml', '.yml')):
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
            
            print(f"\n✅ Configuration file is valid: {config_path}")
            return True
            
        except Exception as e:
            print(f"❌ Configuration file error: {e}")
            return False


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PostgreSQL Backup Manager - Configuration Setup')
    parser.add_argument('--output', '-o', help='Output configuration file path')
    parser.add_argument('--test', '-t', help='Test existing configuration file')
    
    args = parser.parse_args()
    
    setup = ConfigSetup()
    
    if args.test:
        # Test existing configuration
        if setup.test_config(args.test):
            print("Configuration test completed successfully!")
        else:
            sys.exit(1)
    else:
        # Create new configuration
        config_path = setup.create_config(args.output)
        
        # Test the created configuration
        if setup.test_config(config_path):
            print("\n🎉 Configuration setup completed successfully!")
            print(f"📁 Configuration file: {config_path}")
            print("\nNext steps:")
            print("1. Test database connection:")
            print(f"   python src/kma_pg_backup.py -c {config_path} -t")
            print("2. Test remote storage (if enabled):")
            print(f"   python src/kma_pg_backup.py -c {config_path} -r")
            print("3. Create backup:")
            print(f"   python src/kma_pg_backup.py -c {config_path}")


if __name__ == '__main__':
    main()
