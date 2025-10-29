#!/usr/bin/env python3
"""
Advanced Retention Policy Manager
Version: 1.1.0
Author: Michael BAG
Email: mk@remark.pro
Telegram: https://t.me/michaelbag

Module for managing advanced backup retention policies with multi-level storage
"""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import re


class RetentionManager:
    """Manager for advanced backup retention policies"""
    
    def __init__(self, config: Dict, logger: logging.Logger = None):
        """Initialize retention manager with configuration"""
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.backup_config = config.get('backup', {})
        
        # Get retention settings with fallback to legacy settings
        self.retention_config = self.backup_config.get('retention', {})
        self.legacy_retention_days = self.backup_config.get('retention_days', 30)
        
        # Parse retention settings
        self.local_retention = self._parse_retention_config('local')
        self.remote_retention = self._parse_retention_config('remote')
    
    def _parse_retention_config(self, storage_type: str) -> Dict[str, int]:
        """Parse retention configuration for specific storage type"""
        retention = self.retention_config.get(storage_type, {})
        
        # If no advanced retention is configured, use legacy settings
        if not retention:
            return {
                'daily': self.legacy_retention_days,
                'weekly': self.legacy_retention_days,
                'monthly': self.legacy_retention_days,
                'max_age': self.legacy_retention_days
            }
        
        return {
            'daily': retention.get('daily', 30),
            'weekly': retention.get('weekly', 60),
            'monthly': retention.get('monthly', 365),
            'max_age': retention.get('max_age', 365)
        }
    
    def cleanup_old_backups(self, backup_dir: str, storage_type: str = 'local') -> Dict[str, int]:
        """
        Clean up old backups using advanced retention policy
        
        Args:
            backup_dir: Directory containing backup files
            storage_type: 'local' or 'remote'
        
        Returns:
            Dictionary with cleanup statistics
        """
        backup_path = Path(backup_dir)
        if not backup_path.exists():
            self.logger.warning(f"Backup directory not found: {backup_dir}")
            return {'deleted': 0, 'kept': 0, 'errors': 0}
        
        retention = self.local_retention if storage_type == 'local' else self.remote_retention
        
        # Get all backup files
        backup_files = self._get_backup_files(backup_path)
        if not backup_files:
            self.logger.info(f"No backup files found in {backup_dir}")
            return {'deleted': 0, 'kept': 0, 'errors': 0}
        
        # Categorize files by backup type and age
        categorized_files = self._categorize_backup_files(backup_files)
        
        # Apply retention policy
        stats = self._apply_retention_policy(categorized_files, retention, storage_type)
        
        self.logger.info(f"Retention cleanup completed for {storage_type} storage: "
                        f"deleted={stats['deleted']}, kept={stats['kept']}, errors={stats['errors']}")
        
        return stats
    
    def _get_backup_files(self, backup_path: Path) -> List[Path]:
        """Get all backup files from directory"""
        backup_files = []
        for file_path in backup_path.iterdir():
            if file_path.is_file() and file_path.suffix in ['.dump', '.sql', '.gz', '.bz2']:
                backup_files.append(file_path)
        return sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True)
    
    def _categorize_backup_files(self, backup_files: List[Path]) -> Dict[str, List[Path]]:
        """Categorize backup files by type (daily, weekly, monthly)"""
        now = datetime.now()
        categorized = {
            'daily': [],
            'weekly': [],
            'monthly': [],
            'unknown': []
        }
        
        for file_path in backup_files:
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            age_days = (now - file_time).days
            
            # Determine backup type based on filename pattern and age
            backup_type = self._determine_backup_type(file_path, age_days)
            categorized[backup_type].append(file_path)
        
        return categorized
    
    def _determine_backup_type(self, file_path: Path, age_days: int) -> str:
        """Determine backup type based on filename and age"""
        filename = file_path.name.lower()
        
        # Check for explicit type indicators in filename
        if 'daily' in filename or 'day' in filename:
            return 'daily'
        elif 'weekly' in filename or 'week' in filename:
            return 'weekly'
        elif 'monthly' in filename or 'month' in filename:
            return 'monthly'
        
        # Determine type based on age and file pattern
        if age_days <= 30:
            return 'daily'
        elif age_days <= 90:
            return 'weekly'
        elif age_days <= 365:
            return 'monthly'
        else:
            return 'unknown'
    
    def _apply_retention_policy(self, categorized_files: Dict[str, List[Path]], 
                               retention: Dict[str, int], storage_type: str) -> Dict[str, int]:
        """Apply retention policy to categorized files"""
        stats = {'deleted': 0, 'kept': 0, 'errors': 0}
        now = datetime.now()
        
        for backup_type, files in categorized_files.items():
            if backup_type == 'unknown':
                # For unknown files, use max_age
                max_age = retention['max_age']
                cutoff_date = now - timedelta(days=max_age)
                
                for file_path in files:
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        if self._delete_file(file_path, f"older than {max_age} days"):
                            stats['deleted'] += 1
                        else:
                            stats['errors'] += 1
                    else:
                        stats['kept'] += 1
            else:
                # For known backup types, apply specific retention
                retention_days = retention.get(backup_type, retention['max_age'])
                cutoff_date = now - timedelta(days=retention_days)
                
                for file_path in files:
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        if self._delete_file(file_path, f"{backup_type} backup older than {retention_days} days"):
                            stats['deleted'] += 1
                        else:
                            stats['errors'] += 1
                    else:
                        stats['kept'] += 1
        
        return stats
    
    def _delete_file(self, file_path: Path, reason: str) -> bool:
        """Delete a backup file with logging"""
        try:
            file_path.unlink()
            self.logger.info(f"Deleted {file_path.name}: {reason}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting {file_path.name}: {e}")
            return False
    
    def get_retention_summary(self) -> Dict[str, Any]:
        """Get summary of current retention policy"""
        return {
            'local': self.local_retention,
            'remote': self.remote_retention,
            'legacy_mode': not bool(self.retention_config)
        }
    
    def validate_retention_config(self) -> List[str]:
        """Validate retention configuration and return any issues"""
        issues = []
        
        # Check if retention is configured
        if not self.retention_config:
            issues.append("No advanced retention policy configured, using legacy settings")
            return issues
        
        # Validate local retention
        local_issues = self._validate_retention_section('local', self.local_retention)
        issues.extend([f"Local storage: {issue}" for issue in local_issues])
        
        # Validate remote retention
        remote_issues = self._validate_retention_section('remote', self.remote_retention)
        issues.extend([f"Remote storage: {issue}" for issue in remote_issues])
        
        return issues
    
    def _validate_retention_section(self, storage_type: str, retention: Dict[str, int]) -> List[str]:
        """Validate a specific retention section"""
        issues = []
        
        required_keys = ['daily', 'weekly', 'monthly', 'max_age']
        for key in required_keys:
            if key not in retention:
                issues.append(f"Missing {key} setting")
            elif not isinstance(retention[key], int) or retention[key] < 0:
                issues.append(f"Invalid {key} value: {retention[key]}")
        
        # Check logical consistency
        if 'daily' in retention and 'weekly' in retention:
            if retention['daily'] > retention['weekly']:
                issues.append("Daily retention should be less than or equal to weekly retention")
        
        if 'weekly' in retention and 'monthly' in retention:
            if retention['weekly'] > retention['monthly']:
                issues.append("Weekly retention should be less than or equal to monthly retention")
        
        if 'monthly' in retention and 'max_age' in retention:
            if retention['monthly'] > retention['max_age']:
                issues.append("Monthly retention should be less than or equal to max_age")
        
        return issues
