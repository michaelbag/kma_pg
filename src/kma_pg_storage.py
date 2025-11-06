#!/usr/bin/env python3
"""
Remote Storage Manager
Version: 2.0.7/1.0.1
Author: Michael BAG
Email: mk@remark.pro
Telegram: https://t.me/michaelbag

Module for uploading backups to CIFS/Samba and WebDAV servers
"""

import os
import shutil
import subprocess
import tempfile
import ftplib
import re
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import requests
from webdav3.client import Client


def mask_password(text: str) -> str:
    """
    Mask passwords in text strings to prevent logging sensitive information.
    
    Args:
        text: Text string that may contain passwords
        
    Returns:
        Text with passwords masked
    """
    if not text:
        return text
    
    # Mask password=value patterns (case insensitive)
    text = re.sub(
        r'(password\s*[=:]\s*)([^\s\'"&,}]+)',
        r'\1****',
        text,
        flags=re.IGNORECASE
    )
    
    # Mask PGPASSWORD=value patterns
    text = re.sub(
        r'(PGPASSWORD\s*=\s*)([^\s\'"]+)',
        r'\1****',
        text,
        flags=re.IGNORECASE
    )
    
    # Mask password in URLs like //username:password@server
    text = re.sub(
        r'(://[^:]+:)([^@]+)(@)',
        r'\1****\3',
        text
    )
    
    # Mask passwords in connection strings like "password='...'"
    text = re.sub(
        r"(password\s*[=:]\s*['\"])([^'\"]+)(['\"])",
        r'\1****\3',
        text,
        flags=re.IGNORECASE
    )
    
    # Mask passwords in dictionary/JSON representations
    text = re.sub(
        r"(['\"]password['\"]\s*:\s*['\"])([^'\"]+)(['\"])",
        r'\1****\3',
        text,
        flags=re.IGNORECASE
    )
    
    return text


class RemoteStorageManager:
    """Manager for remote storage operations"""
    
    def __init__(self, config: Dict):
        """Initialize remote storage manager with configuration"""
        self.config = config
        self.remote_config = config.get('backup', {}).get('remote_storage', {})
        self.enabled = self.remote_config.get('enabled', False)
        self.storage_type = self.remote_config.get('type', 'webdav')
        # Track mounted mount points for cleanup
        self._mounted_points = set()
        
    def is_enabled(self) -> bool:
        """Check if remote storage is enabled"""
        return self.remote_config.get('enabled', False)
    
    def upload_backup(self, local_file_path: str, remote_filename: str) -> bool:
        """Upload backup file to remote storage"""
        if not self.is_enabled():
            return True  # Remote storage disabled, consider upload successful
        
        try:
            if self.storage_type == 'webdav':
                return self._upload_to_webdav(local_file_path, remote_filename)
            elif self.storage_type == 'cifs':
                return self._upload_to_cifs(local_file_path, remote_filename)
            elif self.storage_type == 'ftp':
                return self._upload_to_ftp(local_file_path, remote_filename)
            else:
                raise ValueError(f"Unsupported storage type: {self.storage_type}")
        except Exception as e:
            error_msg = mask_password(str(e))
            print(f"Remote storage upload error: {error_msg}")
            return False
    
    def _upload_to_webdav(self, local_file_path: str, remote_filename: str) -> bool:
        """Upload file to WebDAV server"""
        webdav_config = self.remote_config.get('webdav', {})
        
        if not webdav_config:
            raise ValueError("WebDAV configuration not found")
        
        # WebDAV client configuration
        options = {
            'webdav_hostname': webdav_config.get('url'),
            'webdav_login': webdav_config.get('username'),
            'webdav_password': webdav_config.get('password'),
            'webdav_verify_ssl': webdav_config.get('verify_ssl', True)
        }
        
        try:
            client = Client(options)
            
            # Test connection
            if not client.check():
                raise ConnectionError("Cannot connect to WebDAV server")
            
            # Upload file
            client.upload_sync(remote_path=remote_filename, local_path=local_file_path)
            print(f"Successfully uploaded {remote_filename} to WebDAV server")
            return True
            
        except Exception as e:
            error_msg = mask_password(str(e))
            print(f"WebDAV upload error: {error_msg}")
            return False
    
    def _upload_to_cifs(self, local_file_path: str, remote_filename: str) -> bool:
        """Upload file to CIFS/Samba server"""
        cifs_config = self.remote_config.get('cifs', {})
        
        if not cifs_config:
            raise ValueError("CIFS configuration not found")
        
        server = cifs_config.get('server')
        username = cifs_config.get('username')
        password = cifs_config.get('password')
        mount_point = cifs_config.get('mount_point', '/mnt/backup_storage')
        auto_mount = cifs_config.get('auto_mount', True)
        
        if not server or not username or not password:
            raise ValueError("CIFS server, username, and password are required")
        
        try:
            # Mount CIFS share if auto_mount is enabled
            if auto_mount:
                # Check if already mounted
                if os.path.ismount(mount_point):
                    print(f"CIFS share already mounted at {mount_point}")
                else:
                    # Check if directory exists but is not a mount point
                    if os.path.exists(mount_point):
                        if not os.path.isdir(mount_point):
                            raise ValueError(f"Mount point {mount_point} exists but is not a directory")
                        # Directory exists but not mounted - try to remove it if empty
                        try:
                            # Check if directory is empty (allow .DS_Store on macOS)
                            contents = [f for f in os.listdir(mount_point) if f != '.DS_Store']
                            if not contents:
                                # Directory is empty, safe to try mounting
                                pass
                            else:
                                # Directory has contents - might be a previous mount that didn't unmount properly
                                print(f"Warning: Mount point {mount_point} contains files. Attempting to use existing directory.")
                        except OSError:
                            # Can't list directory, might be a mount issue
                            pass
                    else:
                        # Create mount point if it doesn't exist
                        os.makedirs(mount_point, exist_ok=True)
                    
                    # Try to mount
                    self._mount_cifs_share(server, username, password, mount_point)
                    # Track mounted point
                    if os.path.ismount(mount_point):
                        self._mounted_points.add(mount_point)
            
            # Check if mount point is accessible
            if not os.path.ismount(mount_point):
                raise ConnectionError(f"CIFS share not mounted at {mount_point}")
            
            # Copy file to CIFS share
            remote_path = os.path.join(mount_point, remote_filename)
            shutil.copy2(local_file_path, remote_path)
            
            print(f"Successfully uploaded {remote_filename} to CIFS server")
            return True
            
        except Exception as e:
            error_msg = mask_password(str(e))
            print(f"CIFS upload error: {error_msg}")
            return False
        finally:
            # Unmount CIFS share if auto_mount is enabled
            if auto_mount:
                self._unmount_cifs_share(mount_point)
    
    def _upload_to_ftp(self, local_file_path: str, remote_filename: str) -> bool:
        """Upload file to FTP server"""
        ftp_config = self.remote_config.get('ftp', {})
        
        if not ftp_config:
            raise ValueError("FTP configuration not found")
        
        host = ftp_config.get('host')
        port = ftp_config.get('port', 21)
        username = ftp_config.get('username')
        password = ftp_config.get('password')
        remote_dir = ftp_config.get('remote_dir', '/')
        passive_mode = ftp_config.get('passive_mode', True)
        ssl = ftp_config.get('ssl', False)
        
        if not all([host, username, password]):
            raise ValueError("FTP host, username, and password are required")
        
        try:
            # Create FTP connection
            if ssl:
                ftp = ftplib.FTP_TLS()
            else:
                ftp = ftplib.FTP()
            
            # Connect to server
            ftp.connect(host, port)
            ftp.login(username, password)
            
            # Set passive mode
            if passive_mode:
                ftp.set_pasv(True)
            
            # Change to remote directory
            if remote_dir and remote_dir != '/':
                try:
                    ftp.cwd(remote_dir)
                except ftplib.error_perm:
                    # Try to create directory if it doesn't exist
                    try:
                        ftp.mkd(remote_dir)
                        ftp.cwd(remote_dir)
                    except ftplib.error_perm:
                        print(f"Warning: Could not create or access directory {remote_dir}")
            
            # Upload file
            with open(local_file_path, 'rb') as file:
                ftp.storbinary(f'STOR {remote_filename}', file)
            
            # Close connection
            ftp.quit()
            
            print(f"Successfully uploaded {remote_filename} to FTP server")
            return True
            
        except Exception as e:
            error_msg = mask_password(str(e))
            print(f"FTP upload error: {error_msg}")
            return False
    
    def _mount_cifs_share(self, server: str, username: str, password: str, mount_point: str):
        """Mount CIFS share"""
        try:
            # Detect OS and use appropriate mount command
            import platform
            system = platform.system().lower()
            
            if system == 'darwin':  # macOS
                # Use mount_smbfs for macOS
                # Check if already mounted at this point
                if os.path.ismount(mount_point):
                    print(f"CIFS share already mounted at {mount_point}")
                    return
                
                # On macOS, check if this share is already mounted elsewhere
                # mount_smbfs typically mounts to /Volumes/sharename
                try:
                    mount_result = subprocess.run(['mount'], capture_output=True, text=True)
                    clean_server = server.replace("//", "").replace("\\", "/").split('/')[-1]
                    # Look for existing mounts of this share
                    for line in mount_result.stdout.split('\n'):
                        if 'smbfs' in line.lower() and clean_server in line:
                            # Share is already mounted somewhere
                            existing_mount = line.split(' on ')[-1].split(' ')[0] if ' on ' in line else None
                            if existing_mount and existing_mount != mount_point:
                                print(f"Share {clean_server} is already mounted at {existing_mount}")
                                # Option 1: Use existing mount point
                                if mount_point != existing_mount:
                                    print(f"Using existing mount point: {existing_mount}")
                                    # Update mount_point in caller if possible, or use existing
                                    # For now, we'll try to unmount and remount
                                    try:
                                        subprocess.run(['umount', existing_mount], check=False, timeout=5)
                                    except:
                                        pass
                except:
                    pass
                
                # Clean up server path
                clean_server = server.replace("//", "").replace("\\", "/")
                mount_cmd = [
                    'mount_smbfs',
                    f'//{username}:{password}@{clean_server}',
                    mount_point
                ]
            else:  # Linux
                # Check if already mounted
                if os.path.ismount(mount_point):
                    print(f"CIFS share already mounted at {mount_point}")
                    return
                
                # Create credentials file
                creds_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cifs')
                creds_file.write(f"username={username}\n")
                creds_file.write(f"password={password}\n")
                creds_file.close()
                
                # Set secure permissions on credentials file
                try:
                    os.chmod(creds_file.name, 0o600)
                except:
                    pass
                
                # Mount command for Linux
                # Try mount.cifs first, then regular mount, then sudo mount
                mount_options = f'credentials={creds_file.name},uid={os.getuid()},gid={os.getgid()}'
                
                # Try mount.cifs (preferred method)
                mount_cmd = None
                if shutil.which('mount.cifs'):
                    mount_cmd = [
                        'mount.cifs', server, mount_point,
                        '-o', mount_options
                    ]
                else:
                    # Fallback to regular mount
                    mount_cmd = [
                        'mount', '-t', 'cifs', server, mount_point,
                        '-o', mount_options
                    ]
            
            # Execute mount
            result = subprocess.run(mount_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                # Check if error is about permissions (root required)
                if "only root can" in result.stderr.lower() or "permission denied" in result.stderr.lower():
                    # Try with sudo if available
                    if shutil.which('sudo'):
                        print(f"Regular mount failed (requires root). Trying with sudo...")
                        sudo_cmd = ['sudo'] + mount_cmd
                        result = subprocess.run(sudo_cmd, capture_output=True, text=True)
                        if result.returncode == 0:
                            print(f"CIFS share mounted at {mount_point} (using sudo)")
                            return
                    # If sudo also failed or not available, provide helpful error message
                    raise RuntimeError(
                        f"Failed to mount CIFS share: {result.stderr}\n"
                        f"Tip: Mounting CIFS requires root privileges. Options:\n"
                        f"  1. Configure sudo without password for mount command:\n"
                        f"     sudo visudo -f /etc/sudoers.d/kma_pg\n"
                        f"     Add: kma_pg ALL=(ALL) NOPASSWD: /usr/bin/mount, /usr/bin/umount, /usr/sbin/mount.cifs\n"
                        f"  2. Configure /etc/fstab for automatic mounting (recommended)\n"
                        f"  3. Run backup script with sudo (not recommended for security)"
                    )
                # Check if error is "File exists" - this means directory exists but not mounted
                if "File exists" in result.stderr or "mount: /" in result.stderr:
                    # Try to use the existing directory if it's accessible
                    if os.path.exists(mount_point) and os.path.isdir(mount_point):
                        print(f"Warning: Mount point {mount_point} already exists. Using existing directory.")
                        # Check if it's actually mounted (might be mounted elsewhere)
                        if os.path.ismount(mount_point):
                            print(f"CIFS share already mounted at {mount_point}")
                            return
                        else:
                            # Not mounted but directory exists - might need to clean up
                            raise RuntimeError(f"Mount point {mount_point} exists but is not mounted. Please check or remove the directory.")
                raise RuntimeError(f"Failed to mount CIFS share: {result.stderr}")
            
            print(f"CIFS share mounted at {mount_point}")
            
        except Exception as e:
            error_msg = mask_password(str(e))
            print(f"Error mounting CIFS share: {error_msg}")
            raise
        finally:
            # Clean up credentials file (Linux only)
            if system != 'darwin' and 'creds_file' in locals():
                try:
                    os.unlink(creds_file.name)
                except:
                    pass
    
    def _unmount_cifs_share(self, mount_point: str):
        """Unmount CIFS share"""
        try:
            if os.path.ismount(mount_point):
                # Detect OS and use appropriate unmount command
                import platform
                system = platform.system().lower()
                
                if system == 'darwin':  # macOS
                    # On macOS, use diskutil for SMB/CIFS shares
                    result = subprocess.run(['diskutil', 'unmount', mount_point], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode != 0:
                        # Fallback to umount if diskutil fails
                        subprocess.run(['umount', mount_point], check=True, timeout=10)
                else:  # Linux
                    unmount_cmd = ['umount', mount_point]
                    result = subprocess.run(unmount_cmd, capture_output=True, text=True, timeout=10)
                    if result.returncode != 0:
                        # Check if error is about permissions (root required)
                        if "only root can" in result.stderr.lower() or "permission denied" in result.stderr.lower():
                            # Try with sudo if available
                            if shutil.which('sudo'):
                                print(f"Regular unmount failed (requires root). Trying with sudo...")
                                sudo_cmd = ['sudo'] + unmount_cmd
                                result = subprocess.run(sudo_cmd, capture_output=True, text=True, timeout=10)
                                if result.returncode != 0:
                                    raise RuntimeError(f"Failed to unmount CIFS share: {result.stderr}")
                            else:
                                raise RuntimeError(f"Failed to unmount CIFS share: {result.stderr}")
                        else:
                            raise RuntimeError(f"Failed to unmount CIFS share: {result.stderr}")
                
                print(f"CIFS share unmounted from {mount_point}")
                # Remove from tracking
                self._mounted_points.discard(mount_point)
        except subprocess.TimeoutExpired:
            print(f"Warning: Timeout while unmounting {mount_point}")
        except Exception as e:
            error_msg = mask_password(str(e))
            print(f"Error unmounting CIFS share: {error_msg}")
            raise
    
    def cleanup_all_mounts(self):
        """Unmount all tracked mount points"""
        unmounted_count = 0
        import platform
        system = platform.system().lower()
        
        for mount_point in list(self._mounted_points):
            try:
                if os.path.ismount(mount_point):
                    if system == 'darwin':  # macOS
                        # On macOS, use diskutil for SMB/CIFS shares
                        result = subprocess.run(['diskutil', 'unmount', mount_point], 
                                              capture_output=True, text=True, timeout=10)
                        if result.returncode != 0:
                            # Fallback to umount if diskutil fails
                            subprocess.run(['umount', mount_point], check=True, timeout=10)
                    else:  # Linux
                        subprocess.run(['umount', mount_point], check=True, timeout=10)
                    
                    print(f"CIFS share unmounted from {mount_point}")
                    unmounted_count += 1
                self._mounted_points.discard(mount_point)
            except subprocess.TimeoutExpired:
                print(f"Warning: Timeout while unmounting {mount_point}")
            except Exception as e:
                error_msg = mask_password(str(e))
                print(f"Error unmounting {mount_point}: {error_msg}")
        
        if unmounted_count > 0:
            print(f"Cleaned up {unmounted_count} mounted resource(s)")
    
    def test_connection(self) -> bool:
        """Test connection to remote storage"""
        if not self.is_enabled():
            return True
        
        try:
            if self.storage_type == 'webdav':
                return self._test_webdav_connection()
            elif self.storage_type == 'cifs':
                return self._test_cifs_connection()
            elif self.storage_type == 'ftp':
                return self._test_ftp_connection()
            else:
                return False
        except Exception as e:
            print(f"Remote storage connection test failed: {e}")
            return False
    
    def _test_webdav_connection(self) -> bool:
        """Test WebDAV connection"""
        webdav_config = self.remote_config.get('webdav', {})
        
        if not webdav_config:
            return False
        
        try:
            options = {
                'webdav_hostname': webdav_config.get('url'),
                'webdav_login': webdav_config.get('username'),
                'webdav_password': webdav_config.get('password'),
                'webdav_verify_ssl': webdav_config.get('verify_ssl', True)
            }
            
            client = Client(options)
            return client.check()
            
        except Exception as e:
            print(f"WebDAV connection test failed: {e}")
            return False
    
    def _test_cifs_connection(self) -> bool:
        """Test CIFS connection"""
        cifs_config = self.remote_config.get('cifs', {})
        
        if not cifs_config:
            return False
        
        server = cifs_config.get('server')
        username = cifs_config.get('username')
        password = cifs_config.get('password')
        mount_point = cifs_config.get('mount_point', '/mnt/backup_storage')
        
        if not all([server, username, password]):
            return False
        
        try:
            # Create temporary mount point
            temp_mount = tempfile.mkdtemp()
            
            # Detect OS and use appropriate mount command
            import platform
            system = platform.system().lower()
            
            if system == 'darwin':  # macOS
                # Use mount_smbfs for macOS
                mount_cmd = [
                    'mount_smbfs',
                    f'//{username}:{password}@{server.replace("//", "").replace("/", "/")}',
                    temp_mount
                ]
            else:  # Linux
                # Create credentials file
                creds_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
                creds_file.write(f"username={username}\n")
                creds_file.write(f"password={password}\n")
                creds_file.close()
                
                # Test mount for Linux
                mount_cmd = [
                    'mount', '-t', 'cifs', server, temp_mount,
                    '-o', f'credentials={creds_file.name},uid={os.getuid()},gid={os.getgid()}'
                ]
            
            result = subprocess.run(mount_cmd, capture_output=True, text=True)
            success = result.returncode == 0
            
            if success:
                # Unmount test mount
                subprocess.run(['umount', temp_mount], capture_output=True)
            
            # Clean up
            os.rmdir(temp_mount)
            if system != 'darwin' and 'creds_file' in locals():
                os.unlink(creds_file.name)
            
            return success
            
        except Exception as e:
            print(f"CIFS connection test failed: {e}")
            return False
    
    def _test_ftp_connection(self) -> bool:
        """Test FTP connection"""
        ftp_config = self.remote_config.get('ftp', {})
        
        if not ftp_config:
            return False
        
        host = ftp_config.get('host')
        port = ftp_config.get('port', 21)
        username = ftp_config.get('username')
        password = ftp_config.get('password')
        ssl = ftp_config.get('ssl', False)
        
        if not all([host, username, password]):
            return False
        
        try:
            # Create FTP connection
            if ssl:
                ftp = ftplib.FTP_TLS()
            else:
                ftp = ftplib.FTP()
            
            # Test connection
            ftp.connect(host, port)
            ftp.login(username, password)
            
            # Test directory access
            remote_dir = ftp_config.get('remote_dir', '/')
            if remote_dir and remote_dir != '/':
                try:
                    ftp.cwd(remote_dir)
                except ftplib.error_perm:
                    # Try to create directory if it doesn't exist
                    try:
                        ftp.mkd(remote_dir)
                        ftp.cwd(remote_dir)
                    except ftplib.error_perm:
                        pass  # Directory creation failed, but connection is OK
            
            # Close connection
            ftp.quit()
            
            return True
            
        except Exception as e:
            print(f"FTP connection test failed: {e}")
            return False
    
    def cleanup_old_backups(self, retention_days: int) -> Dict[str, int]:
        """
        Clean up old backup files from remote storage
        
        Args:
            retention_days: Number of days to keep backups
        
        Returns:
            Dictionary with cleanup statistics
        """
        if not self.is_enabled():
            return {'deleted': 0, 'kept': 0, 'errors': 0}
        
        try:
            if self.storage_type == 'webdav':
                return self._cleanup_webdav_backups(retention_days)
            elif self.storage_type == 'cifs':
                return self._cleanup_cifs_backups(retention_days)
            elif self.storage_type == 'ftp':
                return self._cleanup_ftp_backups(retention_days)
            else:
                print(f"Cleanup not supported for storage type: {self.storage_type}")
                return {'deleted': 0, 'kept': 0, 'errors': 0}
        except Exception as e:
            error_msg = mask_password(str(e))
            print(f"Remote storage cleanup error: {error_msg}")
            return {'deleted': 0, 'kept': 0, 'errors': 1}
    
    def _cleanup_webdav_backups(self, retention_days: int) -> Dict[str, int]:
        """Clean up old backups from WebDAV server"""
        webdav_config = self.remote_config.get('webdav', {})
        
        if not webdav_config:
            print("WebDAV configuration not found")
            return {'deleted': 0, 'kept': 0, 'errors': 1}
        
        try:
            options = {
                'webdav_hostname': webdav_config.get('url'),
                'webdav_login': webdav_config.get('username'),
                'webdav_password': webdav_config.get('password'),
                'webdav_verify_ssl': webdav_config.get('verify_ssl', True)
            }
            
            client = Client(options)
            
            # Get list of files
            files = client.list()
            if not files:
                return {'deleted': 0, 'kept': 0, 'errors': 0}
            
            # Filter backup files
            backup_files = [f for f in files if f.endswith(('.dump', '.sql', '.gz', '.bz2'))]
            
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            stats = {'deleted': 0, 'kept': 0, 'errors': 0}
            
            for file_path in backup_files:
                try:
                    # Get file info (this is a simplified approach)
                    # In a real implementation, you'd need to get file modification time
                    # WebDAV doesn't always provide this easily
                    file_name = os.path.basename(file_path)
                    
                    # For now, we'll use a simple filename-based approach
                    # This is a limitation of the current WebDAV implementation
                    if self._should_delete_file(file_name, retention_days):
                        client.delete(file_path)
                        stats['deleted'] += 1
                        print(f"Deleted remote file: {file_name}")
                    else:
                        stats['kept'] += 1
                        
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")
                    stats['errors'] += 1
            
            return stats
            
        except Exception as e:
            error_msg = mask_password(str(e))
            print(f"WebDAV cleanup error: {error_msg}")
            return {'deleted': 0, 'kept': 0, 'errors': 1}
    
    def _cleanup_cifs_backups(self, retention_days: int) -> Dict[str, int]:
        """Clean up old backups from CIFS/Samba server"""
        cifs_config = self.remote_config.get('cifs', {})
        
        if not cifs_config:
            print("CIFS configuration not found")
            return {'deleted': 0, 'kept': 0, 'errors': 1}
        
        server = cifs_config.get('server')
        username = cifs_config.get('username')
        password = cifs_config.get('password')
        mount_point = cifs_config.get('mount_point', '/mnt/backup_storage')
        auto_mount = cifs_config.get('auto_mount', True)
        
        try:
            # Mount CIFS share if auto_mount is enabled
            if auto_mount:
                # Check if already mounted
                if not os.path.ismount(mount_point):
                    self._mount_cifs_share(server, username, password, mount_point)
                    # Track mounted point
                    if os.path.ismount(mount_point):
                        self._mounted_points.add(mount_point)
                else:
                    print(f"CIFS share already mounted at {mount_point}")
                    # Track existing mount point
                    self._mounted_points.add(mount_point)
            
            # Check if mount point is accessible
            if not os.path.ismount(mount_point):
                print(f"CIFS share not mounted at {mount_point}")
                return {'deleted': 0, 'kept': 0, 'errors': 1}
            
            # Get backup files
            backup_files = []
            for file_path in Path(mount_point).iterdir():
                if file_path.is_file() and file_path.suffix in ['.dump', '.sql', '.gz', '.bz2']:
                    backup_files.append(file_path)
            
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            stats = {'deleted': 0, 'kept': 0, 'errors': 0}
            
            for file_path in backup_files:
                try:
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        file_path.unlink()
                        stats['deleted'] += 1
                        print(f"Deleted remote file: {file_path.name}")
                    else:
                        stats['kept'] += 1
                        
                except Exception as e:
                    print(f"Error deleting file {file_path.name}: {e}")
                    stats['errors'] += 1
            
            return stats
            
        except Exception as e:
            error_msg = mask_password(str(e))
            print(f"CIFS cleanup error: {error_msg}")
            return {'deleted': 0, 'kept': 0, 'errors': 1}
        finally:
            # Unmount CIFS share if auto_mount is enabled
            if auto_mount:
                self._unmount_cifs_share(mount_point)
    
    def _cleanup_ftp_backups(self, retention_days: int) -> Dict[str, int]:
        """Clean up old backups from FTP server"""
        ftp_config = self.remote_config.get('ftp', {})
        
        if not ftp_config:
            print("FTP configuration not found")
            return {'deleted': 0, 'kept': 0, 'errors': 1}
        
        host = ftp_config.get('host')
        port = ftp_config.get('port', 21)
        username = ftp_config.get('username')
        password = ftp_config.get('password')
        remote_dir = ftp_config.get('remote_dir', '/')
        ssl = ftp_config.get('ssl', False)
        
        try:
            # Create FTP connection
            if ssl:
                ftp = ftplib.FTP_TLS()
            else:
                ftp = ftplib.FTP()
            
            # Connect to server
            ftp.connect(host, port)
            ftp.login(username, password)
            
            # Change to remote directory
            if remote_dir and remote_dir != '/':
                try:
                    ftp.cwd(remote_dir)
                except ftplib.error_perm:
                    print(f"Could not access directory {remote_dir}")
                    return {'deleted': 0, 'kept': 0, 'errors': 1}
            
            # Get list of files
            files = []
            ftp.retrlines('LIST', files.append)
            
            # Parse files and filter backup files
            backup_files = []
            for line in files:
                parts = line.split()
                if len(parts) >= 9:
                    filename = ' '.join(parts[8:])
                    if filename.endswith(('.dump', '.sql', '.gz', '.bz2')):
                        backup_files.append(filename)
            
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            stats = {'deleted': 0, 'kept': 0, 'errors': 0}
            
            for filename in backup_files:
                try:
                    # Get file modification time (simplified approach)
                    # FTP doesn't always provide reliable modification time
                    if self._should_delete_file(filename, retention_days):
                        ftp.delete(filename)
                        stats['deleted'] += 1
                        print(f"Deleted remote file: {filename}")
                    else:
                        stats['kept'] += 1
                        
                except Exception as e:
                    print(f"Error deleting file {filename}: {e}")
                    stats['errors'] += 1
            
            # Close connection
            ftp.quit()
            
            return stats
            
        except Exception as e:
            error_msg = mask_password(str(e))
            print(f"FTP cleanup error: {error_msg}")
            return {'deleted': 0, 'kept': 0, 'errors': 1}
    
    def _should_delete_file(self, filename: str, retention_days: int) -> bool:
        """
        Determine if a file should be deleted based on filename and retention policy
        This is a simplified approach - in a real implementation, you'd want to
        parse the actual file modification time from the remote storage
        """
        # This is a placeholder implementation
        # In practice, you'd need to implement proper file age detection
        # based on the specific remote storage type
        return False  # Conservative approach - don't delete by default
    
    def download_backup(self, remote_filename: str, local_path: str) -> bool:
        """Download backup file from remote storage"""
        if not self.is_enabled():
            return False
        
        try:
            if self.storage_type == 'webdav':
                return self._download_from_webdav(remote_filename, local_path)
            elif self.storage_type == 'cifs':
                return self._download_from_cifs(remote_filename, local_path)
            elif self.storage_type == 'ftp':
                return self._download_from_ftp(remote_filename, local_path)
            else:
                raise ValueError(f"Unsupported storage type: {self.storage_type}")
        except Exception as e:
            error_msg = mask_password(str(e))
            print(f"Remote storage download error: {error_msg}")
            return False
    
    def _download_from_webdav(self, remote_filename: str, local_path: str) -> bool:
        """Download file from WebDAV server"""
        webdav_config = self.remote_config.get('webdav', {})
        
        if not webdav_config:
            raise ValueError("WebDAV configuration not found")
        
        # WebDAV client configuration
        options = {
            'webdav_hostname': webdav_config.get('url'),
            'webdav_login': webdav_config.get('username'),
            'webdav_password': webdav_config.get('password'),
            'webdav_verify_ssl': webdav_config.get('verify_ssl', True)
        }
        
        try:
            from webdav3.client import Client
            client = Client(options)
            
            # Download file
            client.download_sync(remote_path=remote_filename, local_path=local_path)
            return True
            
        except Exception as e:
            error_msg = mask_password(str(e))
            print(f"WebDAV download error: {error_msg}")
            return False
    
    def _download_from_cifs(self, remote_filename: str, local_path: str) -> bool:
        """Download file from CIFS/Samba server"""
        cifs_config = self.remote_config.get('cifs', {})
        
        if not cifs_config:
            raise ValueError("CIFS configuration not found")
        
        server = cifs_config.get('server')
        username = cifs_config.get('username')
        password = cifs_config.get('password')
        mount_point = cifs_config.get('mount_point', '/mnt/backup_storage')
        auto_mount = cifs_config.get('auto_mount', True)
        
        if not server or not username or not password:
            raise ValueError("CIFS server, username, and password are required")
        
        try:
            # Create mount point if it doesn't exist
            os.makedirs(mount_point, exist_ok=True)
            
            # Mount CIFS share if auto_mount is enabled
            if auto_mount:
                # Check if already mounted
                if not os.path.ismount(mount_point):
                    self._mount_cifs_share(server, username, password, mount_point)
                    # Track mounted point
                    if os.path.ismount(mount_point):
                        self._mounted_points.add(mount_point)
                else:
                    print(f"CIFS share already mounted at {mount_point}")
                    # Track existing mount point
                    self._mounted_points.add(mount_point)
            
            # Check if mount point is accessible
            if not os.path.ismount(mount_point):
                raise ConnectionError(f"CIFS share not mounted at {mount_point}")
            
            # Copy file from CIFS share
            remote_path = os.path.join(mount_point, remote_filename)
            if os.path.exists(remote_path):
                shutil.copy2(remote_path, local_path)
                return True
            else:
                print(f"File not found on CIFS share: {remote_filename}")
                return False
                
        except Exception as e:
            error_msg = mask_password(str(e))
            print(f"CIFS download error: {error_msg}")
            return False
        finally:
            # Unmount CIFS share if auto_mount is enabled
            if auto_mount:
                self._unmount_cifs_share(mount_point)
    
    def _download_from_ftp(self, remote_filename: str, local_path: str) -> bool:
        """Download file from FTP server"""
        ftp_config = self.remote_config.get('ftp', {})
        
        if not ftp_config:
            raise ValueError("FTP configuration not found")
        
        host = ftp_config.get('host')
        username = ftp_config.get('username')
        password = ftp_config.get('password')
        port = ftp_config.get('port', 21)
        
        if not host or not username or not password:
            raise ValueError("FTP host, username, and password are required")
        
        try:
            import ftplib
            
            # Connect to FTP server
            ftp = ftplib.FTP()
            ftp.connect(host, port)
            ftp.login(username, password)
            
            # Download file
            with open(local_path, 'wb') as local_file:
                ftp.retrbinary(f'RETR {remote_filename}', local_file.write)
            
            # Close connection
            ftp.quit()
            return True
            
        except Exception as e:
            error_msg = mask_password(str(e))
            print(f"FTP download error: {error_msg}")
            return False
    
    def list_backups(self) -> List[str]:
        """List available backup files in remote storage"""
        if not self.is_enabled():
            return []
        
        try:
            if self.storage_type == 'webdav':
                return self._list_webdav_backups()
            elif self.storage_type == 'cifs':
                return self._list_cifs_backups()
            elif self.storage_type == 'ftp':
                return self._list_ftp_backups()
            else:
                raise ValueError(f"Unsupported storage type: {self.storage_type}")
        except Exception as e:
            error_msg = mask_password(str(e))
            print(f"Remote storage list error: {error_msg}")
            return []
    
    def _list_webdav_backups(self) -> List[str]:
        """List backup files from WebDAV server"""
        webdav_config = self.remote_config.get('webdav', {})
        
        if not webdav_config:
            return []
        
        # WebDAV client configuration
        options = {
            'webdav_hostname': webdav_config.get('url'),
            'webdav_login': webdav_config.get('username'),
            'webdav_password': webdav_config.get('password'),
            'webdav_verify_ssl': webdav_config.get('verify_ssl', True)
        }
        
        try:
            from webdav3.client import Client
            client = Client(options)
            
            # List files
            files = client.list()
            backup_files = [f for f in files if f.endswith(('.dump', '.sql', '.dump.gz', '.sql.gz'))]
            return backup_files
            
        except Exception as e:
            error_msg = mask_password(str(e))
            print(f"WebDAV list error: {error_msg}")
            return []
    
    def _list_cifs_backups(self) -> List[str]:
        """List backup files from CIFS/Samba server"""
        cifs_config = self.remote_config.get('cifs', {})
        
        if not cifs_config:
            return []
        
        server = cifs_config.get('server')
        username = cifs_config.get('username')
        password = cifs_config.get('password')
        mount_point = cifs_config.get('mount_point', '/mnt/backup_storage')
        auto_mount = cifs_config.get('auto_mount', True)
        
        if not server or not username or not password:
            return []
        
        try:
            # Create mount point if it doesn't exist
            os.makedirs(mount_point, exist_ok=True)
            
            # Mount CIFS share if auto_mount is enabled
            if auto_mount:
                # Check if already mounted
                if not os.path.ismount(mount_point):
                    self._mount_cifs_share(server, username, password, mount_point)
                    # Track mounted point
                    if os.path.ismount(mount_point):
                        self._mounted_points.add(mount_point)
                else:
                    print(f"CIFS share already mounted at {mount_point}")
                    # Track existing mount point
                    self._mounted_points.add(mount_point)
            
            # Check if mount point is accessible
            if not os.path.ismount(mount_point):
                return []
            
            # List files
            backup_files = []
            for file_path in Path(mount_point).iterdir():
                if file_path.is_file():
                    # Check for backup file extensions (including compressed)
                    if (file_path.suffix in ['.dump', '.sql'] or 
                        file_path.suffixes in [['.dump', '.gz'], ['.sql', '.gz']]):
                        backup_files.append(file_path.name)
            
            return backup_files
            
        except Exception as e:
            error_msg = mask_password(str(e))
            print(f"CIFS list error: {error_msg}")
            return []
        finally:
            # Unmount CIFS share if auto_mount is enabled
            if auto_mount:
                self._unmount_cifs_share(mount_point)
    
    def _list_ftp_backups(self) -> List[str]:
        """List backup files from FTP server"""
        ftp_config = self.remote_config.get('ftp', {})
        
        if not ftp_config:
            return []
        
        host = ftp_config.get('host')
        username = ftp_config.get('username')
        password = ftp_config.get('password')
        port = ftp_config.get('port', 21)
        
        if not host or not username or not password:
            return []
        
        try:
            import ftplib
            
            # Connect to FTP server
            ftp = ftplib.FTP()
            ftp.connect(host, port)
            ftp.login(username, password)
            
            # List files
            files = ftp.nlst()
            backup_files = [f for f in files if f.endswith(('.dump', '.sql', '.dump.gz', '.sql.gz'))]
            
            # Close connection
            ftp.quit()
            return backup_files
            
        except Exception as e:
            error_msg = mask_password(str(e))
            print(f"FTP list error: {error_msg}")
            return []


if __name__ == "__main__":
    """Test remote storage connection"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Remote Storage Manager - Test connection')
    parser.add_argument('--test', '-t', action='store_true',
                       help='Test remote storage connection')
    parser.add_argument('--config', '-c', 
                       help='Path to configuration file (default: config/config.yaml)')
    
    args = parser.parse_args()
    
    try:
        import yaml
        import json
        from pathlib import Path
        
        # Load configuration
        config_path = args.config or 'config/config.yaml'
        if not Path(config_path).exists():
            print(f"Error: Configuration file not found: {config_path}")
            print("Please specify a valid config file with --config")
            sys.exit(1)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.endswith(('.yaml', '.yml')):
                config = yaml.safe_load(f)
            else:
                config = json.load(f)
        
        # Initialize storage manager
        storage = RemoteStorageManager(config)
        
        if args.test or len(sys.argv) == 1:
            print("Testing remote storage connection...")
            if storage.test_connection():
                print("✓ Remote storage connection successful")
                sys.exit(0)
            else:
                print("✗ Remote storage connection failed")
                sys.exit(1)
        else:
            parser.print_help()
            sys.exit(0)
            
    except ImportError as e:
        print(f"Error: Missing required module: {e}")
        print("Please install dependencies: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
