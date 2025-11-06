#!/usr/bin/env python3
"""
PostgreSQL Backup Manager - Configuration Setup
Version: 2.0.7/1.0.3
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
import pwd
import grp
import stat
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

from kma_pg_config_manager import DatabaseConfigManager


class ConfigSetup:
    """Interactive configuration setup manager"""
    
    def __init__(self, config_owner: Optional[str] = None):
        """Initialize configuration setup
        
        Args:
            config_owner: Username to set as owner of config files (default: current user)
        """
        self.config_manager = DatabaseConfigManager()
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        
        # Determine config owner
        # Priority: explicit parameter > PROJECT_USER env var > .project_user file > SUDO_USER > USER
        # Note: PROJECT_USER is set by init_project.sh and saved to .project_user file
        if config_owner:
            self.config_owner = config_owner
        else:
            # Try to get from environment variable first
            project_user = os.environ.get('PROJECT_USER')
            
            # If not in environment, try to read from .project_user file
            if not project_user:
                project_user_file = Path('.project_user')
                if project_user_file.exists():
                    try:
                        project_user = project_user_file.read_text().strip()
                    except Exception:
                        pass
            
            self.config_owner = (project_user or 
                               os.environ.get('SUDO_USER') or 
                               os.environ.get('USER') or 
                               os.getlogin())
        
        # Get current effective user
        try:
            current_user = os.getlogin()
        except:
            current_user = os.environ.get('USER', os.environ.get('SUDO_USER', 'unknown'))
        
        # Check if we're running as root/administrator
        self.is_root = os.geteuid() == 0
        
        # Informational messages
        if self.is_root:
            print(f"ℹ Running as root/administrator, will set ownership to: {self.config_owner}")
            print(f"ℹ All configuration files will be owned by '{self.config_owner}' with 0600 permissions")
        elif current_user != self.config_owner:
            print(f"ℹ Current user: {current_user}, target owner: {self.config_owner}")
            print(f"ℹ If files are already owned by '{self.config_owner}', permissions will be set correctly")
            print(f"ℹ If files are owned by different user, root may be needed to change ownership")
        
        # Load existing configurations for suggestions
        self.existing_configs = self._load_existing_configs()
        self.suggestions = self._extract_suggestions()
        
        # Track saved config paths for fallback
        self.saved_config_paths = []
    
    def _set_file_permissions(self, file_path: Path):
        """Set file owner and permissions (read/write for owner only)"""
        try:
            # Get user and group IDs
            try:
                user_info = pwd.getpwnam(self.config_owner)
                uid = user_info.pw_uid
                gid = user_info.pw_gid
            except KeyError:
                # User not found, skip ownership change
                print(f"⚠ Warning: User '{self.config_owner}' not found, skipping ownership change")
                return
            
            # Set ownership
            # If running as root/administrator, os.chown works directly (root can change ownership to any user)
            # If running as kma_pg (non-root), we can only change ownership if we already own the file
            # Since kma_pg doesn't have sudo, we cannot change ownership of files owned by other users
            
            try:
                os.chown(file_path, uid, gid)
                if self.is_root:
                    # Successfully changed ownership as root/administrator
                    pass
            except PermissionError:
                # Can't change ownership - check if file is already owned by correct user
                try:
                    current_stat = file_path.stat()
                    if current_stat.st_uid == uid:
                        # File is already owned by correct user (kma_pg), that's fine
                        pass
                    else:
                        # File is owned by different user and we can't change it
                        try:
                            current_owner = pwd.getpwuid(current_stat.st_uid).pw_name
                        except:
                            current_owner = f"uid:{current_stat.st_uid}"
                        
                        print(f"⚠ Warning: Cannot change ownership of {file_path}")
                        print(f"   Current owner: {current_owner}, required: {self.config_owner}")
                        if not self.is_root:
                            print(f"   Suggestion: Run as root/administrator to set ownership, or ensure file is owned by {self.config_owner}")
                        # Continue to set permissions anyway (they might be changeable if we own the file)
                except Exception:
                    pass
            
            # Set permissions: read/write for owner only (0600)
            # This should work if we own the file or are root
            try:
                file_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
            except PermissionError:
                print(f"⚠ Warning: Cannot set permissions for {file_path} (may need root)")
            
        except Exception as e:
            # Don't fail if we can't set permissions
            print(f"⚠ Warning: Could not set permissions for {file_path}: {e}")
    
    def _set_directory_permissions(self, dir_path: Path):
        """Set directory owner and permissions (read/write/execute for owner only)"""
        try:
            # Get user and group IDs
            try:
                user_info = pwd.getpwnam(self.config_owner)
                uid = user_info.pw_uid
                gid = user_info.pw_gid
            except KeyError:
                # User not found, skip ownership change
                return
            
            # Set ownership
            # If running as root/administrator, change ownership recursively
            # If running as kma_pg, only change if we already own the directory
            
            try:
                os.chown(dir_path, uid, gid)
                if self.is_root:
                    # Successfully changed ownership as root/administrator
                    # Also change ownership recursively for all files in directory
                    for file_path in dir_path.rglob('*'):
                        try:
                            os.chown(file_path, uid, gid)
                        except (PermissionError, OSError):
                            pass  # Skip files we can't change
            except PermissionError:
                # Can't change ownership - check if directory is already owned by correct user
                try:
                    current_stat = dir_path.stat()
                    if current_stat.st_uid == uid:
                        # Directory is already owned by correct user (kma_pg), that's fine
                        pass
                    else:
                        # Directory is owned by different user and we can't change it
                        try:
                            current_owner = pwd.getpwuid(current_stat.st_uid).pw_name
                        except:
                            current_owner = f"uid:{current_stat.st_uid}"
                        
                        print(f"⚠ Warning: Cannot change ownership of {dir_path}")
                        print(f"   Current owner: {current_owner}, required: {self.config_owner}")
                        if not self.is_root:
                            print(f"   Suggestion: Run as root/administrator to set ownership, or ensure directory is owned by {self.config_owner}")
                except Exception:
                    pass
            
            # Set permissions: read/write/execute for owner only (0700)
            try:
                dir_path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            except PermissionError:
                print(f"⚠ Warning: Cannot set permissions for {dir_path} (may need root)")
            
            # Set permissions for all files in directory
            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    try:
                        file_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
                    except PermissionError:
                        pass  # Skip files we can't change permissions for
            
        except Exception as e:
            # Don't fail if we can't set permissions
            print(f"⚠ Warning: Could not set permissions for {dir_path}: {e}")
    
    def _get_home_dir(self) -> Path:
        """Get user's home directory"""
        try:
            return Path.home()
        except Exception:
            # Fallback to environment variable
            home = os.environ.get('HOME') or os.environ.get('USERPROFILE')
            if home:
                return Path(home)
            # Last resort - use current directory
            return Path.cwd()
    
    def _find_available_home_config_path(self, base_name: str, extension: str = '.yaml') -> Path:
        """Find available config path in home directory with index if needed
        
        Args:
            base_name: Base name for the config file (may include extension)
            extension: File extension (default: .yaml)
        
        Returns:
            Path to available config file in home directory
        """
        home_dir = self._get_home_dir()
        
        # Remove extension from base_name if present
        if base_name.endswith(('.yaml', '.yml', '.json')):
            base_stem = Path(base_name).stem
        else:
            base_stem = base_name
        
        # Try base name first
        config_path = home_dir / f"{base_stem}{extension}"
        if not config_path.exists():
            return config_path
        
        # Find next available index
        index = 1
        while True:
            config_path = home_dir / f"{base_stem}_{index}{extension}"
            if not config_path.exists():
                return config_path
            index += 1
    
    def _safe_save_config_file(self, config: Dict[str, Any], preferred_path: Path, 
                               config_type: str = "configuration") -> Path:
        """Safely save configuration file with fallback to home directory
        
        Args:
            config: Configuration dictionary to save
            preferred_path: Preferred path in project directory
            config_type: Type of configuration (for user messages)
        
        Returns:
            Path where configuration was actually saved
        """
        # Determine file format
        is_yaml = preferred_path.suffix in ['.yaml', '.yml']
        
        # Try to save to preferred location first
        try:
            # Create parent directory if needed
            preferred_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Try to write file
            with open(preferred_path, 'w', encoding='utf-8') as f:
                if is_yaml:
                    yaml.dump(config, f, default_flow_style=False, indent=2, allow_unicode=True)
                else:
                    json.dump(config, f, indent=2, ensure_ascii=False)
            
            # Try to set permissions
            try:
                self._set_file_permissions(preferred_path)
            except Exception:
                pass  # Continue even if permissions fail
            
            # Successfully saved to preferred location
            return preferred_path
            
        except (PermissionError, OSError, IOError) as e:
            # Cannot save to preferred location - fallback to home directory
            print(f"\n⚠ Warning: Cannot save {config_type} to preferred location: {preferred_path}")
            print(f"   Error: {e}")
            print(f"   Saving to home directory instead...")
            
            # Find available path in home directory
            home_path = self._find_available_home_config_path(preferred_path.stem, preferred_path.suffix)
            
            try:
                # Save to home directory
                with open(home_path, 'w', encoding='utf-8') as f:
                    if is_yaml:
                        yaml.dump(config, f, default_flow_style=False, indent=2, allow_unicode=True)
                    else:
                        json.dump(config, f, indent=2, ensure_ascii=False)
                
                print(f"✅ {config_type.capitalize()} saved to: {home_path}")
                return home_path
                
            except Exception as e2:
                # Even home directory save failed
                raise IOError(f"Failed to save {config_type} to both preferred location and home directory: {e2}")
    
    def _load_existing_configs(self) -> List[Dict[str, Any]]:
        """Load all existing database configurations for suggestions"""
        configs = []
        
        databases_dir = self.config_manager.databases_dir
        if not databases_dir.exists():
            return configs
        
        for config_file in databases_dir.glob("*.yaml"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    config['_filename'] = config_file.stem
                    configs.append(config)
            except Exception as e:
                # Silently skip invalid configs for suggestions
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
    
    def get_input_with_suggestions(self, prompt: str, field_name: str, 
                                  default: str = None,
                                  required: bool = True,
                                  input_type: str = "string") -> Any:
        """Get user input with suggestions from existing configurations"""
        suggestions = self.suggestions.get(field_name, set())
        
        # If we have suggestions, offer them
        if suggestions:
            print(f"\n{prompt}")
            print("Available options from existing configurations:")
            sorted_suggestions = sorted(suggestions)
            for i, suggestion in enumerate(sorted_suggestions, 1):
                print(f"  {i}. {suggestion}")
            print(f"  {len(suggestions) + 1}. Enter custom value")
            if default:
                print(f"  {len(suggestions) + 2}. Use default [{default}]")
            
            while True:
                try:
                    choice = input(f"Choose option (1-{len(suggestions) + (2 if default else 1)}): ").strip()
                    if not choice:
                        if default:
                            return self._convert_value(default, input_type)
                        elif not required:
                            return None
                        print("Please enter a valid number")
                        continue
                    
                    choice_num = int(choice)
                    max_option = len(suggestions) + (2 if default else 1)
                    
                    if 1 <= choice_num <= len(suggestions):
                        selected_value = sorted_suggestions[choice_num - 1]
                        print(f"Selected: {selected_value}")
                        return self._convert_value(selected_value, input_type)
                    elif choice_num == len(suggestions) + 1:
                        # User wants to enter custom value
                        break
                    elif default and choice_num == len(suggestions) + 2:
                        # User wants to use default
                        return self._convert_value(default, input_type)
                    else:
                        print(f"Please enter a number between 1 and {max_option}")
                except ValueError:
                    print("Please enter a valid number")
                except (EOFError, KeyboardInterrupt):
                    print("\nOperation cancelled")
                    return None if not required else default
        
        # No suggestions or user chose custom value - use regular input
        return self.get_input(prompt, default, required)
    
    def _convert_value(self, value: str, input_type: str) -> Any:
        """Convert string input to appropriate type"""
        if input_type == "int":
            return int(value)
        elif input_type == "bool":
            return value.lower() in ['true', 'yes', 'y', '1', 'on']
        else:
            return value
        
    def get_input(self, prompt: str, default: str = None, required: bool = True) -> str:
        """Get user input with default value"""
        if default:
            full_prompt = f"{prompt} [{default}]: "
        else:
            full_prompt = f"{prompt}: "
            
        while True:
            value = input(full_prompt).strip()
            if value:
                # User entered a value, return it
                return value
            elif default is not None:
                # User pressed Enter, use default value
                return default
            elif not required:
                # No default, not required, return empty string
                return ""
            else:
                # No default, required field, ask again
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
    
    def get_backup_format_input(self, prompt: str, default: str = "custom", show_description: bool = True) -> str:
        """Get backup format input with short form support (c for custom, p for plain)"""
        if show_description:
            print("\nBackup format options:")
            print("  - custom (c): PostgreSQL custom format - binary format, supports selective restore")
            print("  - plain (p):  SQL script format - plain text SQL, can be edited and restored with psql")
            print()
        
        while True:
            value = input(f"{prompt} [{default}]: ").strip().lower()
            
            if not value:
                # User pressed Enter, use default value
                return default
            
            # Handle short forms
            if value == 'c':
                return 'custom'
            elif value == 'p':
                return 'plain'
            # Handle full forms
            elif value in ['custom', 'plain']:
                return value
            else:
                print("Please enter 'custom' or 'plain' (or 'c' for custom, 'p' for plain).")
    
    def get_password_input(self, prompt: str) -> Optional[str]:
        """Get password input with option to use ~/.pgpass
        
        Returns:
            Password string if provided, None if empty (will use ~/.pgpass automatically)
        """
        print(f"\n{prompt}")
        print("Note: Leave empty to use ~/.pgpass file (PostgreSQL standard password file)")
        print("      pg_dump and pg_restore will automatically read passwords from ~/.pgpass")
        print("      Format: hostname:port:database:username:password")
        print("      File location: ~/.pgpass (or %APPDATA%\\postgresql\\pgpass.conf on Windows)")
        password = getpass.getpass("Password (press Enter to use ~/.pgpass): ")
        password = password.strip()
        return password if password else None
    
    def setup_database_config(self) -> Dict[str, Any]:
        """Setup database configuration"""
        print("\n=== Database Configuration ===")
        
        config = {
            'host': self.get_input("PostgreSQL host", "localhost"),
            'port': self.get_number_input("PostgreSQL port", 5432, 1, 65535),
            'username': self.get_input("PostgreSQL username", "postgres"),
            'databases': self.setup_databases_list()
        }
        
        # Only add password if provided (otherwise pg_dump/pg_restore will use ~/.pgpass)
        password = self.get_password_input("PostgreSQL password")
        if password:
            config['password'] = password
        
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
        
        # Check if main configuration already exists
        main_config_exists = self.config_manager.main_config_path.exists()
        existing_databases = []
        
        if main_config_exists:
            try:
                main_config = self.config_manager.get_main_config()
                print(f"✓ Found existing main configuration: {self.config_manager.main_config_path}")
                
                # Get list of existing database configurations
                if self.config_manager.databases_dir.exists():
                    for config_file in self.config_manager.databases_dir.glob("*.yaml"):
                        db_name = config_file.stem
                        if self.config_manager.get_database_config(db_name):
                            existing_databases.append(db_name)
                    
                    if existing_databases:
                        print(f"✓ Found {len(existing_databases)} existing database configuration(s): {', '.join(existing_databases)}")
            except Exception as e:
                print(f"⚠ Warning: Could not load existing configuration: {e}")
                main_config_exists = False
        
        if main_config_exists:
            print("\nOptions:")
            print("1. Add new database configuration(s) to existing setup")
            print("2. Update main configuration and add database(s)")
            print("3. Start fresh (overwrite existing configuration)")
            print()
            
            choice = self.get_input("Choose option (1, 2, or 3)", "1")
            
            if choice == "1":
                # Just add new databases, ask about main config
                print("\n--- Adding New Database Configurations ---")
                update_main = self.get_boolean_input("Update main (general) configuration?", False)
                if update_main:
                    print("\n--- Main Configuration Update ---")
                    main_config = {
                        'backup': self.setup_backup_config(),
                        'logging': self.setup_logging_config()
                    }
                    # Save safely with fallback
                    saved_path = self._safe_save_config_file(main_config, self.config_manager.main_config_path, "main configuration")
                    self.saved_config_paths.append(saved_path)
                    print(f"✅ Main configuration updated: {saved_path}")
                else:
                    print("Note: Main configuration will remain unchanged.")
            elif choice == "2":
                # Update main config and add databases
                print("\n--- Main Configuration Update ---")
                main_config = {
                    'backup': self.setup_backup_config(),
                    'logging': self.setup_logging_config()
                }
                # Save safely with fallback
                saved_path = self._safe_save_config_file(main_config, self.config_manager.main_config_path, "main configuration")
                self.saved_config_paths.append(saved_path)
                print(f"✅ Main configuration updated: {saved_path}")
                print("\n--- Adding Database Configurations ---")
            else:
                # Start fresh
                print("\n--- Main Configuration ---")
                main_config = {
                    'backup': self.setup_backup_config(),
                    'logging': self.setup_logging_config()
                }
                # Save safely with fallback
                saved_path = self._safe_save_config_file(main_config, self.config_manager.main_config_path, "main configuration")
                self.saved_config_paths.append(saved_path)
                print(f"✅ Main configuration saved: {saved_path}")
                print("\n--- Database Configurations ---")
        else:
            # Setup main configuration
            print("\n--- Main Configuration ---")
            main_config = {
                'backup': self.setup_backup_config(),
                'logging': self.setup_logging_config()
            }
            
            # Save main configuration safely with fallback
            saved_path = self._safe_save_config_file(main_config, self.config_manager.main_config_path, "main configuration")
            self.saved_config_paths.append(saved_path)
            print(f"✅ Main configuration saved to: {saved_path}")
            
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
                    print(f"⏭ Skipping database '{db_name}'")
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
            
            # Save database configuration safely with fallback
            db_config_path = self.config_manager.databases_dir / f"{db_name}.yaml"
            # Remove internal fields before saving
            clean_config = {k: v for k, v in db_config.items() if not k.startswith('_')}
            saved_path = self._safe_save_config_file(clean_config, db_config_path, f"database configuration for '{db_name}'")
            self.saved_config_paths.append(saved_path)
            print(f"✅ Database configuration saved: {db_name} -> {saved_path}")
            databases.append(db_name)
        
        if databases:
            print(f"\n🎉 Multi-database configuration completed!")
            print(f"📁 Newly configured databases: {', '.join(databases)}")
            if existing_databases:
                print(f"📁 Existing databases: {', '.join(existing_databases)}")
            
            # Show all saved configuration paths
            print(f"\n📋 Configuration files saved:")
            saved_to_home = False
            for saved_path in self.saved_config_paths:
                saved_path_obj = Path(saved_path) if isinstance(saved_path, str) else saved_path
                main_path = Path(self.config_manager.main_config_path)
                db_dir = Path(self.config_manager.databases_dir)
                
                if saved_path_obj.resolve() == main_path.resolve() or saved_path_obj.parent.resolve() == db_dir.resolve():
                    print(f"   ✓ {saved_path} (project directory)")
                else:
                    saved_to_home = True
                    print(f"   ⚠ {saved_path} (home directory - saved due to insufficient permissions)")
            
            # Show intended locations if different
            if saved_to_home:
                print(f"\n💡 Note: Some configurations were saved to home directory due to insufficient permissions.")
                print(f"   Intended locations:")
                print(f"   - Main config: {self.config_manager.main_config_path}")
                print(f"   - Database configs: {self.config_manager.databases_dir}")
            
            return True
        else:
            if existing_databases:
                print(f"\n✓ No new databases added. Existing configuration preserved.")
                print(f"📁 Existing databases: {', '.join(existing_databases)}")
                return True
            else:
                print("❌ No databases configured")
                return False
    
    def setup_single_database_config(self, database_name: str) -> Dict[str, Any]:
        """Setup configuration for a single database"""
        print(f"\n--- Database Configuration: {database_name} ---")
        
        # Database connection settings (with suggestions if available)
        db_config = {
            'name': database_name,
            'host': self.get_input_with_suggestions("PostgreSQL host", 'hosts', "localhost", required=True),
            'port': int(self.get_input_with_suggestions("PostgreSQL port", 'ports', "5432", required=True, input_type="int")),
            'username': self.get_input_with_suggestions("PostgreSQL username", 'usernames', "postgres", required=True),
            'enabled': self.get_boolean_input("Enable backup for this database", True),
            'auto_backup': True
        }
        
        # Only add password if provided (otherwise pg_dump/pg_restore will use ~/.pgpass)
        password = self.get_password_input("PostgreSQL password")
        if password:
            db_config['password'] = password
        
        if db_config['enabled']:
            db_config['auto_backup'] = self.get_boolean_input("Include in automatic backup", True)
        
        # Database-specific backup settings
        print(f"\n--- Backup Settings for {database_name} ---")
        print("Note: If 'No' - uses settings from main config (output_dir, format, compress, retention_days).")
        print("      If 'Yes' - allows individual backup settings for this database only.")
        use_custom_backup = self.get_boolean_input("Use custom backup settings for this database", False)
        
        if use_custom_backup:
            backup_config = {
                'output_dir': self.get_input_with_suggestions("Backup output directory", 'output_dirs', "backups", required=True),
                'format': self.get_backup_format_input("Backup format (custom/plain or c/p)", "custom", show_description=True),
                'compress': self.get_boolean_input("Enable compression", True),
                'retention_days': self.get_number_input("Retention days", 30, 1, 365),
                'remote_storage': self.setup_remote_storage_config()
            }
        else:
            # When using main config backup settings, ask separately about remote storage
            backup_config = {}
            print(f"\n--- Remote Storage Settings for {database_name} ---")
            print("Note: If 'No' - uses remote storage settings from main config.")
            print("      If 'Yes' - allows individual remote storage settings for this database only.")
            use_custom_remote = self.get_boolean_input("Use custom remote storage settings for this database", False)
            if use_custom_remote:
                backup_config['remote_storage'] = self.setup_remote_storage_config()
            # If No, don't add remote_storage - it will be inherited from main config
        
        # Database-specific logging settings
        print(f"\n--- Logging Settings for {database_name} ---")
        use_custom_logging = self.get_boolean_input("Use custom logging settings for this database", False)
        
        if use_custom_logging:
            logging_config = {
                'level': self.get_input_with_suggestions("Log level (DEBUG/INFO/WARNING/ERROR)", 'log_levels', "INFO", required=True),
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
            'output_dir': self.get_input_with_suggestions("Backup output directory", 'output_dirs', "backups", required=True),
            'format': self.get_backup_format_input("Backup format (custom/plain or c/p)", "custom", show_description=True),
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
        
        storage_type = self.get_input_with_suggestions("Storage type (webdav/cifs/ftp)", 'remote_types', "webdav", required=True)
        
        config = {
            'enabled': True,
            'type': storage_type
        }
        
        if storage_type == 'webdav':
            config['webdav'] = {
                'url': self.get_input_with_suggestions("WebDAV URL", 'remote_servers', "https://your-webdav-server.com/backups", required=True),
                'username': self.get_input_with_suggestions("WebDAV username", 'remote_usernames', required=True),
                'password': getpass.getpass("WebDAV password: "),
                'verify_ssl': self.get_boolean_input("Verify SSL certificate", True)
            }
        elif storage_type == 'cifs':
            config['cifs'] = {
                'server': self.get_input_with_suggestions("CIFS server", 'remote_servers', "//your-samba-server.com/share", required=True),
                'username': self.get_input_with_suggestions("CIFS username", 'remote_usernames', required=True),
                'password': getpass.getpass("CIFS password: "),
                'mount_point': self.get_input("Mount point", "/mnt/backup_storage"),
                'auto_mount': self.get_boolean_input("Auto mount", True)
            }
        elif storage_type == 'ftp':
            config['ftp'] = {
                'host': self.get_input_with_suggestions("FTP host", 'remote_servers', "ftp.your-server.com", required=True),
                'port': self.get_number_input("FTP port", 21, 1, 65535),
                'username': self.get_input_with_suggestions("FTP username", 'remote_usernames', required=True),
                'password': getpass.getpass("FTP password: "),
                'passive': self.get_boolean_input("Passive mode", True),
                'ssl': self.get_boolean_input("Use SSL/TLS", False)
            }
        
        return config
    
    def setup_logging_config(self) -> Dict[str, Any]:
        """Setup logging configuration"""
        print("\n=== Logging Configuration ===")
        
        config = {
            'level': self.get_input_with_suggestions("Log level (DEBUG/INFO/WARNING/ERROR)", 'log_levels', "INFO", required=True),
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
        print()
        print("1. Single configuration file (legacy mode)")
        print("   - All databases in one configuration file")
        print("   - Single connection settings for all databases")
        print("   - Simple setup, suitable for small deployments")
        print()
        print("2. Multi-database configuration (recommended)")
        print("   - Separate configuration file for each database")
        print("   - Individual connection settings and backup options per database")
        print("   - Flexible, suitable for production environments")
        print()
        
        mode = self.get_input("Choose mode (1 or 2)", "2")
        
        if mode == "2":
            # Multi-database configuration
            if self.setup_multi_database_config():
                # Return the actual saved main config path (may be in home directory)
                if self.saved_config_paths:
                    # Find main config path (first one saved, or the one matching main_config_path)
                    main_path = Path(self.config_manager.main_config_path)
                    for saved_path in self.saved_config_paths:
                        saved_path_obj = Path(saved_path) if isinstance(saved_path, str) else saved_path
                        if saved_path_obj.resolve() == main_path.resolve():
                            return str(saved_path_obj)
                    # If not found, return first saved (should be main config)
                    return str(Path(self.saved_config_paths[0]) if isinstance(self.saved_config_paths[0], str) else self.saved_config_paths[0])
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
        
        # Save configuration safely (with fallback to home directory)
        try:
            saved_path = self._safe_save_config_file(config, config_path, "configuration")
            self.saved_config_paths.append(saved_path)
            
            # Try to set directory permissions (if we saved to project directory)
            if saved_path == config_path:
                try:
                    self._set_directory_permissions(self.config_dir)
                except Exception:
                    pass  # Continue even if directory permissions fail
            
            print(f"\n✅ Configuration saved to: {saved_path}")
            return str(saved_path)
            
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
    parser.add_argument('--owner', help='Username to set as owner of config files (default: current user or PROJECT_USER env var)')
    
    args = parser.parse_args()
    
    setup = ConfigSetup(config_owner=args.owner)
    
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
