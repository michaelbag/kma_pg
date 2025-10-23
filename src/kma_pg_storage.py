#!/usr/bin/env python3
"""
Remote Storage Manager
Version: 1.0.0
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
from pathlib import Path
from typing import Dict, Optional
import requests
from webdav3.client import Client


class RemoteStorageManager:
    """Manager for remote storage operations"""
    
    def __init__(self, config: Dict):
        """Initialize remote storage manager with configuration"""
        self.config = config
        self.remote_config = config.get('backup', {}).get('remote_storage', {})
        self.enabled = self.remote_config.get('enabled', False)
        self.storage_type = self.remote_config.get('type', 'webdav')
        
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
            print(f"Remote storage upload error: {e}")
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
            print(f"WebDAV upload error: {e}")
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
            # Create mount point if it doesn't exist
            os.makedirs(mount_point, exist_ok=True)
            
            # Mount CIFS share if auto_mount is enabled
            if auto_mount:
                self._mount_cifs_share(server, username, password, mount_point)
            
            # Check if mount point is accessible
            if not os.path.ismount(mount_point):
                raise ConnectionError(f"CIFS share not mounted at {mount_point}")
            
            # Copy file to CIFS share
            remote_path = os.path.join(mount_point, remote_filename)
            shutil.copy2(local_file_path, remote_path)
            
            print(f"Successfully uploaded {remote_filename} to CIFS server")
            return True
            
        except Exception as e:
            print(f"CIFS upload error: {e}")
            return False
    
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
            print(f"FTP upload error: {e}")
            return False
        finally:
            # Unmount CIFS share if auto_mount is enabled
            if auto_mount:
                self._unmount_cifs_share(mount_point)
    
    def _mount_cifs_share(self, server: str, username: str, password: str, mount_point: str):
        """Mount CIFS share"""
        try:
            # Create credentials file
            creds_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
            creds_file.write(f"username={username}\n")
            creds_file.write(f"password={password}\n")
            creds_file.close()
            
            # Mount command
            mount_cmd = [
                'mount', '-t', 'cifs', server, mount_point,
                '-o', f'credentials={creds_file.name},uid={os.getuid()},gid={os.getgid()}'
            ]
            
            # Execute mount
            result = subprocess.run(mount_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"Failed to mount CIFS share: {result.stderr}")
            
            print(f"CIFS share mounted at {mount_point}")
            
        except Exception as e:
            print(f"Error mounting CIFS share: {e}")
            raise
        finally:
            # Clean up credentials file
            if 'creds_file' in locals():
                try:
                    os.unlink(creds_file.name)
                except:
                    pass
    
    def _unmount_cifs_share(self, mount_point: str):
        """Unmount CIFS share"""
        try:
            if os.path.ismount(mount_point):
                subprocess.run(['umount', mount_point], check=True)
                print(f"CIFS share unmounted from {mount_point}")
        except Exception as e:
            print(f"Error unmounting CIFS share: {e}")
    
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
            
            # Create credentials file
            creds_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
            creds_file.write(f"username={username}\n")
            creds_file.write(f"password={password}\n")
            creds_file.close()
            
            # Test mount
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
