#!/usr/bin/env python3
"""
PostgreSQL Backup Manager - Version Management System
Version: 1.1.0/1.0.0

Centralized version management for the project and individual scripts.
"""

import json
import re
from pathlib import Path
from typing import Dict, Tuple, Optional


class VersionManager:
    """Version management system for project and scripts"""
    
    def __init__(self, version_file: str = "VERSION"):
        """Initialize version manager"""
        self.version_file = Path(version_file)
        self.versions = self._load_versions()
    
    def _load_versions(self) -> Dict[str, str]:
        """Load versions from file or create default"""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Default versions
        return {
            "project": "1.1.0",
            "scripts": {
                "kma_pg_backup.py": "1.0.0",
                "kma_pg_restore.py": "1.0.0", 
                "kma_pg_storage.py": "1.0.0",
                "kma_pg_config_setup.py": "1.0.0",
                "kma_pg_config_manager.py": "1.0.0",
                "kma_pg_config_builder.py": "1.0.0",
                "kma_pg_retention.py": "1.0.0"
            }
        }
    
    def _save_versions(self):
        """Save versions to file"""
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(self.versions, f, indent=2, ensure_ascii=False)
    
    def _parse_version(self, version: str) -> Tuple[int, int, int]:
        """Parse version string to tuple (major, minor, patch)"""
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)$', version)
        if not match:
            raise ValueError(f"Invalid version format: {version}")
        return tuple(int(x) for x in match.groups())
    
    def _format_version(self, major: int, minor: int, patch: int) -> str:
        """Format version tuple to string"""
        return f"{major}.{minor}.{patch}"
    
    def get_project_version(self) -> str:
        """Get current project version"""
        return self.versions["project"]
    
    def get_script_version(self, script_name: str) -> str:
        """Get current script version"""
        return self.versions["scripts"].get(script_name, "1.0.0")
    
    def get_full_version(self, script_name: str) -> str:
        """Get full version in format 'project_version/script_version'"""
        project_ver = self.get_project_version()
        script_ver = self.get_script_version(script_name)
        return f"{project_ver}/{script_ver}"
    
    def increment_script_version(self, script_name: str, increment_type: str = "patch") -> str:
        """Increment script version and update project version if needed"""
        if script_name not in self.versions["scripts"]:
            self.versions["scripts"][script_name] = "1.0.0"
        
        # Parse current versions
        project_major, project_minor, project_patch = self._parse_version(self.versions["project"])
        script_major, script_minor, script_patch = self._parse_version(self.versions["scripts"][script_name])
        
        # Increment script version
        if increment_type == "major":
            script_major += 1
            script_minor = 0
            script_patch = 0
        elif increment_type == "minor":
            script_minor += 1
            script_patch = 0
        else:  # patch
            script_patch += 1
        
        new_script_version = self._format_version(script_major, script_minor, script_patch)
        self.versions["scripts"][script_name] = new_script_version
        
        # Update project version based on script version
        if script_major > project_major or (script_major == project_major and script_minor > project_minor):
            # Major or minor increment in script requires project version update
            if script_major > project_major:
                project_major = script_major
                project_minor = 0
                project_patch = 0
            else:
                project_minor = script_minor
                project_patch = 0
        elif script_patch > project_patch:
            # Patch increment in script requires project patch update
            project_patch = script_patch
        
        new_project_version = self._format_version(project_major, project_minor, project_patch)
        self.versions["project"] = new_project_version
        
        # Save changes
        self._save_versions()
        
        return self.get_full_version(script_name)
    
    def set_script_version(self, script_name: str, version: str) -> str:
        """Set specific script version and update project version if needed"""
        # Validate version format
        self._parse_version(version)
        
        # Parse versions
        project_major, project_minor, project_patch = self._parse_version(self.versions["project"])
        script_major, script_minor, script_patch = self._parse_version(version)
        
        # Update script version
        self.versions["scripts"][script_name] = version
        
        # Update project version if needed
        if script_major > project_major or (script_major == project_major and script_minor > project_minor):
            if script_major > project_major:
                project_major = script_major
                project_minor = 0
                project_patch = 0
            else:
                project_minor = script_minor
                project_patch = 0
        elif script_patch > project_patch:
            project_patch = script_patch
        
        new_project_version = self._format_version(project_major, project_minor, project_patch)
        self.versions["project"] = new_project_version
        
        # Save changes
        self._save_versions()
        
        return self.get_full_version(script_name)
    
    def list_versions(self) -> Dict[str, str]:
        """List all versions"""
        result = {"project": self.versions["project"]}
        for script, version in self.versions["scripts"].items():
            result[script] = f"{self.versions['project']}/{version}"
        return result
    
    def get_version_info(self) -> Dict[str, any]:
        """Get detailed version information"""
        return {
            "project_version": self.versions["project"],
            "scripts": {
                script: {
                    "script_version": version,
                    "full_version": f"{self.versions['project']}/{version}"
                }
                for script, version in self.versions["scripts"].items()
            }
        }


def get_version(script_name: str) -> str:
    """Convenience function to get full version for a script"""
    vm = VersionManager()
    return vm.get_full_version(script_name)


def increment_version(script_name: str, increment_type: str = "patch") -> str:
    """Convenience function to increment script version"""
    vm = VersionManager()
    return vm.increment_script_version(script_name, increment_type)


def main():
    """Main function for version management CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Version Management System')
    parser.add_argument('--list', '-l', action='store_true', help='List all versions')
    parser.add_argument('--get', '-g', help='Get version for specific script')
    parser.add_argument('--increment', '-i', help='Increment version for specific script')
    parser.add_argument('--type', '-t', choices=['major', 'minor', 'patch'], 
                       default='patch', help='Increment type (default: patch)')
    parser.add_argument('--set', '-s', nargs=2, metavar=('SCRIPT', 'VERSION'),
                       help='Set specific version for script')
    
    args = parser.parse_args()
    
    vm = VersionManager()
    
    if args.list:
        versions = vm.list_versions()
        print("Project and Script Versions:")
        print(f"Project: {versions['project']}")
        for script, version in versions.items():
            if script != 'project':
                print(f"  {script}: {version}")
    
    elif args.get:
        version = vm.get_full_version(args.get)
        print(f"{args.get}: {version}")
    
    elif args.increment:
        version = vm.increment_script_version(args.increment, args.type)
        print(f"Incremented {args.increment} to {version}")
    
    elif args.set:
        script, version = args.set
        full_version = vm.set_script_version(script, version)
        print(f"Set {script} to {full_version}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
