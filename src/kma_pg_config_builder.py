#!/usr/bin/env python3
"""
PostgreSQL Backup Manager - Interactive Configuration Builder
Version: 1.1.0

Interactive tool for creating database configurations with value suggestions
from existing configurations.
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from kma_pg_config_manager import DatabaseConfigManager


class ConfigBuilder:
    """Interactive configuration builder with value suggestions"""
    
    def __init__(self, config_dir: str = "config"):
        """Initialize configuration builder"""
        self.config_dir = Path(config_dir)
        self.databases_dir = self.config_dir / "databases"
        self.config_manager = DatabaseConfigManager(config_dir)
        
        # Load existing configurations for suggestions
        self.existing_configs = self._load_existing_configs()
        self.suggestions = self._extract_suggestions()
    
    def _load_existing_configs(self) -> List[Dict[str, Any]]:
        """Load all existing database configurations"""
        configs = []
        
        if not self.databases_dir.exists():
            return configs
        
        for config_file in self.databases_dir.glob("*.yaml"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    config['_filename'] = config_file.stem
                    configs.append(config)
            except Exception as e:
                print(f"Warning: Could not load {config_file}: {e}")
                continue
        
        return configs
    
    def _extract_suggestions(self) -> Dict[str, Set[str]]:
        """Extract unique values from existing configurations for suggestions"""
        suggestions = {
            'hosts': set(),
            'ports': set(),
            'usernames': set(),
            'output_dirs': set(),
            'remote_types': set(),
            'remote_servers': set(),
            'remote_usernames': set(),
            'log_levels': set(),
            'formats': set(),
            'retention_daily': set(),
            'retention_weekly': set(),
            'retention_monthly': set(),
            'retention_max_age': set()
        }
        
        for config in self.existing_configs:
            # Database connection suggestions
            db_config = config.get('database', {})
            if db_config.get('host'):
                suggestions['hosts'].add(db_config['host'])
            if db_config.get('port'):
                suggestions['ports'].add(str(db_config['port']))
            if db_config.get('username'):
                suggestions['usernames'].add(db_config['username'])
            
            # Backup settings suggestions
            backup_config = config.get('backup', {})
            if backup_config.get('output_dir'):
                suggestions['output_dirs'].add(backup_config['output_dir'])
            if backup_config.get('format'):
                suggestions['formats'].add(backup_config['format'])
            
            # Remote storage suggestions
            remote_config = backup_config.get('remote_storage', {})
            if remote_config.get('type'):
                suggestions['remote_types'].add(remote_config['type'])
            if remote_config.get('webdav', {}).get('url'):
                suggestions['remote_servers'].add(remote_config['webdav']['url'])
            if remote_config.get('cifs', {}).get('server'):
                suggestions['remote_servers'].add(remote_config['cifs']['server'])
            if remote_config.get('ftp', {}).get('host'):
                suggestions['remote_servers'].add(remote_config['ftp']['host'])
            
            # Remote usernames
            for storage_type in ['webdav', 'cifs', 'ftp']:
                if remote_config.get(storage_type, {}).get('username'):
                    suggestions['remote_usernames'].add(remote_config[storage_type]['username'])
            
            # Logging suggestions
            log_config = config.get('logging', {})
            if log_config.get('level'):
                suggestions['log_levels'].add(log_config['level'])
            
            # Retention suggestions
            retention = backup_config.get('retention', {})
            for storage_type in ['local', 'remote']:
                if retention.get(storage_type):
                    if retention[storage_type].get('daily'):
                        suggestions['retention_daily'].add(str(retention[storage_type]['daily']))
                    if retention[storage_type].get('weekly'):
                        suggestions['retention_weekly'].add(str(retention[storage_type]['weekly']))
                    if retention[storage_type].get('monthly'):
                        suggestions['retention_monthly'].add(str(retention[storage_type]['monthly']))
                    if retention[storage_type].get('max_age'):
                        suggestions['retention_max_age'].add(str(retention[storage_type]['max_age']))
        
        return suggestions
    
    def _get_input_with_suggestions(self, prompt: str, field_name: str, 
                                  required: bool = True, 
                                  input_type: str = "string") -> Any:
        """Get user input with suggestions from existing configurations"""
        suggestions = self.suggestions.get(field_name, set())
        
        if suggestions:
            print(f"\n{prompt}")
            print("Available options from existing configurations:")
            for i, suggestion in enumerate(sorted(suggestions), 1):
                print(f"  {i}. {suggestion}")
            print(f"  {len(suggestions) + 1}. Enter custom value")
            
            while True:
                try:
                    choice = input(f"Choose option (1-{len(suggestions) + 1}): ").strip()
                    if not choice:
                        print("Please enter a valid number")
                        continue
                    choice_num = int(choice)
                    
                    if 1 <= choice_num <= len(suggestions):
                        selected_value = sorted(suggestions)[choice_num - 1]
                        print(f"Selected: {selected_value}")
                        return self._convert_value(selected_value, input_type)
                    elif choice_num == len(suggestions) + 1:
                        break
                    else:
                        print(f"Please enter a number between 1 and {len(suggestions) + 1}")
                except ValueError:
                    print("Please enter a valid number")
                except (EOFError, KeyboardInterrupt):
                    print("\nOperation cancelled")
                    return None
        else:
            print(f"\n{prompt}")
        
        # Get custom input
        while True:
            try:
                value = input("Enter value: ").strip()
                if value or not required:
                    return self._convert_value(value, input_type) if value else None
                print("This field is required. Please enter a value.")
            except (EOFError, KeyboardInterrupt):
                print("\nOperation cancelled")
                return None
    
    def _convert_value(self, value: str, input_type: str) -> Any:
        """Convert string input to appropriate type"""
        if input_type == "int":
            return int(value)
        elif input_type == "bool":
            return value.lower() in ['true', 'yes', 'y', '1', 'on']
        else:
            return value
    
    def _get_yes_no(self, prompt: str, default: bool = True) -> bool:
        """Get yes/no input with default"""
        default_text = "Y/n" if default else "y/N"
        while True:
            try:
                response = input(f"{prompt} [{default_text}]: ").strip().lower()
                if not response:
                    return default
                if response in ['y', 'yes', 'n', 'no']:
                    return response in ['y', 'yes']
                print("Please enter 'y' for yes or 'n' for no")
            except (EOFError, KeyboardInterrupt):
                return default
    
    def build_database_config(self) -> Dict[str, Any]:
        """Build database configuration interactively"""
        print("=" * 60)
        print("PostgreSQL Backup Manager - Configuration Builder")
        print("=" * 60)
        
        config = {}
        
        # Database connection settings
        print("\n" + "=" * 40)
        print("DATABASE CONNECTION SETTINGS")
        print("=" * 40)
        
        config['database'] = {
            'name': self._get_input_with_suggestions(
                "Database name:", 'usernames', required=True
            ),
            'host': self._get_input_with_suggestions(
                "PostgreSQL server hostname/IP:", 'hosts', required=True
            ),
            'port': self._get_input_with_suggestions(
                "PostgreSQL server port:", 'ports', required=True, input_type="int"
            ),
            'username': self._get_input_with_suggestions(
                "Database username:", 'usernames', required=True
            ),
            'password': input("Database password: "),
            'enabled': self._get_yes_no("Enable this database for backup operations?"),
            'auto_backup': self._get_yes_no("Include in automatic backup (cron jobs)?")
        }
        
        # Backup settings
        print("\n" + "=" * 40)
        print("BACKUP SETTINGS")
        print("=" * 40)
        
        config['backup'] = {
            'output_dir': self._get_input_with_suggestions(
                "Backup output directory:", 'output_dirs', required=True
            ),
            'format': self._get_input_with_suggestions(
                "Backup format (custom/plain):", 'formats', required=True
            ),
            'compress': self._get_yes_no("Enable compression?", default=True)
        }
        
        # Retention policy
        print("\n" + "=" * 40)
        print("RETENTION POLICY")
        print("=" * 40)
        
        use_advanced_retention = self._get_yes_no(
            "Use advanced multi-level retention policy?", default=True
        )
        
        if use_advanced_retention:
            config['backup']['retention'] = {
                'local': {
                    'daily': int(self._get_input_with_suggestions(
                        "Local daily retention (days):", 'retention_daily', 
                        required=True, input_type="int"
                    )),
                    'weekly': int(self._get_input_with_suggestions(
                        "Local weekly retention (days):", 'retention_weekly', 
                        required=True, input_type="int"
                    )),
                    'monthly': int(self._get_input_with_suggestions(
                        "Local monthly retention (days):", 'retention_monthly', 
                        required=True, input_type="int"
                    )),
                    'max_age': int(self._get_input_with_suggestions(
                        "Local max age (days):", 'retention_max_age', 
                        required=True, input_type="int"
                    ))
                },
                'remote': {
                    'daily': int(self._get_input_with_suggestions(
                        "Remote daily retention (days):", 'retention_daily', 
                        required=True, input_type="int"
                    )),
                    'weekly': int(self._get_input_with_suggestions(
                        "Remote weekly retention (days):", 'retention_weekly', 
                        required=True, input_type="int"
                    )),
                    'monthly': int(self._get_input_with_suggestions(
                        "Remote monthly retention (days):", 'retention_monthly', 
                        required=True, input_type="int"
                    )),
                    'max_age': int(self._get_input_with_suggestions(
                        "Remote max age (days):", 'retention_max_age', 
                        required=True, input_type="int"
                    ))
                }
            }
        else:
            config['backup']['retention_days'] = int(input("Retention days: "))
        
        # Remote storage
        print("\n" + "=" * 40)
        print("REMOTE STORAGE SETTINGS")
        print("=" * 40)
        
        enable_remote = self._get_yes_no("Enable remote storage upload?")
        
        if enable_remote:
            config['backup']['remote_storage'] = {
                'enabled': True,
                'type': self._get_input_with_suggestions(
                    "Remote storage type (webdav/cifs/ftp):", 'remote_types', required=True
                )
            }
            
            # Configure specific remote storage type
            remote_type = config['backup']['remote_storage']['type']
            
            if remote_type == 'webdav':
                config['backup']['remote_storage']['webdav'] = {
                    'url': self._get_input_with_suggestions(
                        "WebDAV URL:", 'remote_servers', required=True
                    ),
                    'username': self._get_input_with_suggestions(
                        "WebDAV username:", 'remote_usernames', required=True
                    ),
                    'password': input("WebDAV password: "),
                    'verify_ssl': self._get_yes_no("Verify SSL certificate?", default=True)
                }
            
            elif remote_type == 'cifs':
                config['backup']['remote_storage']['cifs'] = {
                    'server': self._get_input_with_suggestions(
                        "CIFS server path (//server/share):", 'remote_servers', required=True
                    ),
                    'username': self._get_input_with_suggestions(
                        "CIFS username:", 'remote_usernames', required=True
                    ),
                    'password': input("CIFS password: "),
                    'mount_point': input("Local mount point: "),
                    'auto_mount': self._get_yes_no("Auto-mount share?", default=True)
                }
            
            elif remote_type == 'ftp':
                config['backup']['remote_storage']['ftp'] = {
                    'host': self._get_input_with_suggestions(
                        "FTP host:", 'remote_servers', required=True
                    ),
                    'port': int(input("FTP port (21): ") or "21"),
                    'username': self._get_input_with_suggestions(
                        "FTP username:", 'remote_usernames', required=True
                    ),
                    'password': input("FTP password: "),
                    'passive': self._get_yes_no("Use passive mode?", default=True)
                }
        else:
            config['backup']['remote_storage'] = {'enabled': False}
        
        # Logging settings
        print("\n" + "=" * 40)
        print("LOGGING SETTINGS")
        print("=" * 40)
        
        config['logging'] = {
            'level': self._get_input_with_suggestions(
                "Log level (DEBUG/INFO/WARNING/ERROR):", 'log_levels', required=True
            ),
            'file': input("Log file path: ") or f"logs/backup_{config['database']['name']}.log"
        }
        
        return config
    
    def save_config(self, config: Dict[str, Any], database_name: str) -> bool:
        """Save configuration to file"""
        try:
            self.config_manager.save_database_config(database_name, config)
            print(f"\n✅ Configuration saved successfully: config/databases/{database_name}.yaml")
            return True
        except Exception as e:
            print(f"\n❌ Error saving configuration: {e}")
            return False
    
    def show_config_summary(self, config: Dict[str, Any]):
        """Show configuration summary before saving"""
        print("\n" + "=" * 60)
        print("CONFIGURATION SUMMARY")
        print("=" * 60)
        
        # Database settings
        db = config['database']
        print(f"Database: {db['name']} @ {db['host']}:{db['port']}")
        print(f"Username: {db['username']}")
        print(f"Enabled: {db['enabled']}, Auto-backup: {db['auto_backup']}")
        
        # Backup settings
        backup = config['backup']
        print(f"Output: {backup['output_dir']}")
        print(f"Format: {backup['format']}, Compress: {backup['compress']}")
        
        # Retention
        if 'retention' in backup:
            local = backup['retention']['local']
            remote = backup['retention']['remote']
            print(f"Retention - Local: {local['daily']}d/{local['weekly']}w/{local['monthly']}m")
            print(f"Retention - Remote: {remote['daily']}d/{remote['weekly']}w/{remote['monthly']}m")
        else:
            print(f"Retention: {backup.get('retention_days', 'N/A')} days")
        
        # Remote storage
        if backup['remote_storage']['enabled']:
            remote = backup['remote_storage']
            print(f"Remote: {remote['type']} - {remote.get('webdav', {}).get('url', remote.get('cifs', {}).get('server', remote.get('ftp', {}).get('host', 'N/A')))}")
        else:
            print("Remote storage: Disabled")
        
        # Logging
        log = config['logging']
        print(f"Logging: {log['level']} -> {log['file']}")
    
    def run(self):
        """Run interactive configuration builder"""
        try:
            # Build configuration
            config = self.build_database_config()
            
            # Show summary
            self.show_config_summary(config)
            
            # Confirm save
            if self._get_yes_no("\nSave this configuration?", default=True):
                database_name = config['database']['name']
                if self.save_config(config, database_name):
                    print(f"\n🎉 Configuration for '{database_name}' created successfully!")
                    print(f"Use: python src/kma_pg_backup.py --database-config {database_name}")
                else:
                    print("\n❌ Failed to save configuration")
            else:
                print("\nConfiguration not saved")
                
        except KeyboardInterrupt:
            print("\n\nConfiguration cancelled by user")
        except Exception as e:
            print(f"\n❌ Error: {e}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Interactive Configuration Builder')
    parser.add_argument('--config-dir', default='config', 
                       help='Configuration directory (default: config)')
    
    args = parser.parse_args()
    
    builder = ConfigBuilder(args.config_dir)
    builder.run()


if __name__ == "__main__":
    main()
