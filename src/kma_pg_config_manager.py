#!/usr/bin/env python3
"""
PostgreSQL Backup Manager - Configuration Manager
Version: 1.1.0/1.0.0
Author: Michael BAG
Email: mk@remark.pro
Telegram: https://t.me/michaelbag

Manages multiple database configurations with individual access credentials
"""

import os
import sys
import yaml
import json
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional


class DatabaseConfigManager:
    """Manager for multiple database configurations"""
    
    def __init__(self, config_dir: str = "config"):
        """Initialize configuration manager"""
        self.config_dir = Path(config_dir)
        self.databases_dir = self.config_dir / "databases"
        self.main_config_path = self.config_dir / "config.yaml"
        
        # Create directories if they don't exist
        self.config_dir.mkdir(exist_ok=True)
        self.databases_dir.mkdir(exist_ok=True)
    
    def get_main_config(self) -> Dict[str, Any]:
        """Get main configuration file"""
        if not self.main_config_path.exists():
            return self._create_default_main_config()
        
        try:
            with open(self.main_config_path, 'r', encoding='utf-8') as f:
                if self.main_config_path.suffix in ['.yaml', '.yml']:
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        except Exception as e:
            raise ValueError(f"Error loading main configuration: {e}")
    
    def _create_default_main_config(self) -> Dict[str, Any]:
        """Create default main configuration"""
        default_config = {
            'backup': {
                'output_dir': 'backups',
                'format': 'custom',
                'compress': True,
                'retention_days': 30,
                'remote_storage': {
                    'enabled': False
                }
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/backup.log'
            }
        }
        
        self.save_main_config(default_config)
        return default_config
    
    def save_main_config(self, config: Dict[str, Any]):
        """Save main configuration"""
        try:
            with open(self.main_config_path, 'w', encoding='utf-8') as f:
                if self.main_config_path.suffix in ['.yaml', '.yml']:
                    yaml.dump(config, f, default_flow_style=False, indent=2, allow_unicode=True)
                else:
                    json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise ValueError(f"Error saving main configuration: {e}")
    
    def get_database_configs(self) -> List[Dict[str, Any]]:
        """Get all database configurations"""
        configs = []
        
        # Look for database configuration files
        pattern = str(self.databases_dir / "*.yaml")
        yaml_files = glob.glob(pattern)
        pattern = str(self.databases_dir / "*.yml")
        yml_files = glob.glob(pattern)
        pattern = str(self.databases_dir / "*.json")
        json_files = glob.glob(pattern)
        
        all_files = yaml_files + yml_files + json_files
        
        for config_file in all_files:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    if config_file.endswith(('.yaml', '.yml')):
                        config = yaml.safe_load(f)
                    else:
                        config = json.load(f)
                    
                    # Add file path to config
                    config['_config_file'] = config_file
                    configs.append(config)
                    
            except Exception as e:
                print(f"Warning: Error loading database config {config_file}: {e}")
                continue
        
        return configs
    
    def get_database_config(self, database_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for specific database"""
        configs = self.get_database_configs()
        
        for config in configs:
            if config.get('database', {}).get('name') == database_name:
                return config
        
        return None
    
    def save_database_config(self, database_name: str, config: Dict[str, Any]):
        """Save database configuration"""
        config_file = self.databases_dir / f"{database_name}.yaml"
        
        # Remove internal fields
        clean_config = {k: v for k, v in config.items() if not k.startswith('_')}
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(clean_config, f, default_flow_style=False, indent=2, allow_unicode=True)
        except Exception as e:
            raise ValueError(f"Error saving database configuration: {e}")
    
    def delete_database_config(self, database_name: str) -> bool:
        """Delete database configuration"""
        config_file = self.databases_dir / f"{database_name}.yaml"
        
        if config_file.exists():
            try:
                config_file.unlink()
                return True
            except Exception as e:
                print(f"Error deleting database config: {e}")
                return False
        
        return False
    
    def list_databases(self) -> List[str]:
        """List all configured databases"""
        configs = self.get_database_configs()
        return [config.get('database', {}).get('name') for config in configs if config.get('database', {}).get('name')]
    
    def get_enabled_databases(self, auto_backup_only: bool = False) -> List[Dict[str, Any]]:
        """Get enabled databases with their configurations"""
        configs = self.get_database_configs()
        enabled_configs = []
        
        for config in configs:
            db_config = config.get('database', {})
            if db_config.get('enabled', True):
                if not auto_backup_only or db_config.get('auto_backup', True):
                    enabled_configs.append(config)
        
        return enabled_configs
    
    def validate_database_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate database configuration"""
        errors = []
        
        # Check required fields
        if 'database' not in config:
            errors.append("Missing 'database' section")
            return errors
        
        db_config = config['database']
        
        required_fields = ['name', 'host', 'port', 'username', 'password']
        for field in required_fields:
            if field not in db_config:
                errors.append(f"Missing required field: database.{field}")
        
        # Validate port
        if 'port' in db_config:
            try:
                port = int(db_config['port'])
                if port < 1 or port > 65535:
                    errors.append("Invalid port number (must be 1-65535)")
            except (ValueError, TypeError):
                errors.append("Port must be a number")
        
        # Validate enabled/auto_backup flags
        if 'enabled' in db_config and not isinstance(db_config['enabled'], bool):
            errors.append("'enabled' must be a boolean")
        
        if 'auto_backup' in db_config and not isinstance(db_config['auto_backup'], bool):
            errors.append("'auto_backup' must be a boolean")
        
        return errors
    
    def get_merged_config(self, database_name: str) -> Optional[Dict[str, Any]]:
        """Get merged configuration (main + database specific)"""
        main_config = self.get_main_config()
        db_config = self.get_database_config(database_name)
        
        if not db_config:
            return None
        
        # Merge configurations
        merged = main_config.copy()
        merged['database'] = db_config['database']
        
        # Override backup settings if database has specific ones
        if 'backup' in db_config:
            merged['backup'].update(db_config['backup'])
        
        # Override logging settings if database has specific ones
        if 'logging' in db_config:
            merged['logging'].update(db_config['logging'])
        
        return merged


def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database Configuration Manager')
    parser.add_argument('--list', '-l', action='store_true', help='List all databases')
    parser.add_argument('--show', '-s', help='Show configuration for specific database')
    parser.add_argument('--validate', '-v', help='Validate configuration for specific database')
    
    args = parser.parse_args()
    
    manager = DatabaseConfigManager()
    
    if args.list:
        databases = manager.list_databases()
        if databases:
            print("Configured databases:")
            for db in databases:
                print(f"  - {db}")
        else:
            print("No databases configured")
    
    elif args.show:
        config = manager.get_database_config(args.show)
        if config:
            print(f"Configuration for database '{args.show}':")
            print(yaml.dump(config, default_flow_style=False, indent=2))
        else:
            print(f"Database '{args.show}' not found")
    
    elif args.validate:
        config = manager.get_database_config(args.validate)
        if config:
            errors = manager.validate_database_config(config)
            if errors:
                print(f"Validation errors for '{args.validate}':")
                for error in errors:
                    print(f"  - {error}")
            else:
                print(f"Configuration for '{args.validate}' is valid")
        else:
            print(f"Database '{args.validate}' not found")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
