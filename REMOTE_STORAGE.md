# Remote Storage Configuration

This document describes how to configure and use remote storage for PostgreSQL backups.

## Supported Storage Types

### 1. FTP
FTP (File Transfer Protocol) is a standard network protocol for file transfer.

#### Configuration Example:
```yaml
backup:
  remote_storage:
    enabled: true
    type: "ftp"
    ftp:
      host: "ftp.your-server.com"
      port: 21
      username: "your_username"
      password: "your_password"
      remote_dir: "/backups"
      passive_mode: true
      ssl: false
```

#### Popular FTP Services:
- **vsftpd** - Linux FTP server
- **FileZilla Server** - Windows FTP server
- **ProFTPD** - Cross-platform FTP server
- **Pure-FTPd** - Lightweight FTP server
- **Commercial FTP services** - Various hosting providers

### 2. WebDAV
WebDAV (Web Distributed Authoring and Versioning) is a standard protocol for file sharing over HTTP/HTTPS.

#### Configuration Example:
```yaml
backup:
  remote_storage:
    enabled: true
    type: "webdav"
    webdav:
      url: "https://your-webdav-server.com/backups"
      username: "your_username"
      password: "your_password"
      verify_ssl: true
```

#### Popular WebDAV Services:
- **Nextcloud** - Self-hosted cloud storage
- **OwnCloud** - Open source cloud storage
- **Yandex Disk** - Russian cloud storage with WebDAV support
- **Box** - Enterprise cloud storage
- **Dropbox** - (Limited WebDAV support)

### 3. CIFS/Samba
CIFS (Common Internet File System) is a protocol for sharing files over a network, commonly used with Samba servers.

#### Configuration Example:
```yaml
backup:
  remote_storage:
    enabled: true
    type: "cifs"
    cifs:
      server: "//your-samba-server.com/share"
      username: "your_username"
      password: "your_password"
      mount_point: "/mnt/backup_storage"
      auto_mount: true
```

#### Requirements:
- `cifs-utils` package must be installed
- Mount point directory must exist
- **Sudo permissions for mount/umount commands** (see below)

#### Sudo Configuration for CIFS Mounting:

On Linux systems, mounting CIFS shares requires root privileges. The backup script automatically uses `sudo` when needed, but the backup user must be configured to run mount commands without a password.

**Option 1: Configure sudo without password (Recommended for auto_mount: true)**

1. Create sudoers configuration file:
   ```bash
   sudo visudo -f /etc/sudoers.d/kma_pg
   ```

2. Add the following line (replace `kma_pg` with your actual backup user):
   ```
   kma_pg ALL=(ALL) NOPASSWD: /usr/bin/mount, /usr/bin/umount, /usr/sbin/mount.cifs
   ```

   Or for different Linux distributions:
   ```
   kma_pg ALL=(ALL) NOPASSWD: /usr/bin/mount, /usr/bin/umount, /usr/sbin/mount.cifs, /bin/mount, /bin/umount, /sbin/mount.cifs
   ```

3. Verify syntax:
   ```bash
   sudo visudo -c -f /etc/sudoers.d/kma_pg
   ```

4. Test sudo access:
   ```bash
   sudo -l
   # Should show the mount/umount commands without password requirement
   ```

**Option 2: Configure /etc/fstab for automatic mounting (Recommended for production)**

If you prefer not to use sudo, configure automatic mounting via `/etc/fstab`:

1. Create credentials file:
   ```bash
   sudo nano /etc/cifs-credentials
   # Add:
   username=your_username
   password=your_password
   # Set secure permissions:
   sudo chmod 600 /etc/cifs-credentials
   ```

2. Add to `/etc/fstab`:
   ```
   //server/share /mnt/backup_storage cifs credentials=/etc/cifs-credentials,uid=1000,gid=1000,file_mode=0660,dir_mode=0770 0 0
   ```
   (Replace `uid=1000,gid=1000` with your backup user's UID/GID)

3. Test mounting:
   ```bash
   sudo mount -a
   ```

4. Set `auto_mount: false` in configuration to prevent script from mounting/unmounting:
   ```yaml
   cifs:
     server: "//server/share"
     mount_point: "/mnt/backup_storage"
     auto_mount: false  # Share is already mounted via /etc/fstab
   ```

**Security Note:**
- Option 1 (sudo) is safe because it only grants permission for specific mount commands, not full root access
- Option 2 (/etc/fstab) is more secure but requires manual mount management
- The script automatically detects if a share is already mounted and skips mounting if `auto_mount: false`

## Installation Requirements

### For FTP:
```bash
# FTP support is built into Python standard library
# No additional packages required
```

### For WebDAV:
```bash
pip install webdavclient3 requests
```

### For CIFS:
```bash
# Ubuntu/Debian
sudo apt-get install cifs-utils

# CentOS/RHEL
sudo yum install cifs-utils

# macOS
# CIFS support is built-in
```

## Configuration Examples

### FTP Server Example:
```yaml
backup:
  remote_storage:
    enabled: true
    type: "ftp"
    ftp:
      host: "192.168.1.100"
      port: 21
      username: "backup_user"
      password: "secure_password"
      remote_dir: "/backups"
      passive_mode: true
      ssl: false
```

### Nextcloud WebDAV Example:
```yaml
backup:
  remote_storage:
    enabled: true
    type: "webdav"
    webdav:
      url: "https://nextcloud.yourdomain.com/remote.php/dav/files/username/backups"
      username: "your_nextcloud_username"
      password: "your_app_password"
      verify_ssl: true
```

### Samba Server Example:
```yaml
backup:
  remote_storage:
    enabled: true
    type: "cifs"
    cifs:
      server: "//192.168.1.100/backups"
      username: "backup_user"
      password: "secure_password"
      mount_point: "/mnt/backup_storage"
      auto_mount: true
```

## Testing Remote Storage

### Test WebDAV Connection:
```bash
python src/backup_manager.py --test-remote-storage
```

### Test with Specific Config:
```bash
python src/backup_manager.py --config config/config.production.yaml --test-remote-storage
```

## Security Considerations

1. **Use App Passwords**: For services like Nextcloud, use app-specific passwords instead of main account passwords
2. **SSL/TLS**: Always use HTTPS for WebDAV connections
3. **Credentials**: Store credentials securely, consider using environment variables
4. **Permissions**: Ensure backup user has minimal required permissions

## Troubleshooting

### FTP Issues:
- Check host and port connectivity
- Verify username and password
- Ensure passive mode is enabled if behind firewall
- Check directory permissions on FTP server

### WebDAV Issues:
- Check URL format (should end with directory path)
- Verify SSL certificate if `verify_ssl: true`
- Test connection with WebDAV client tools

### CIFS Issues:
- Ensure `cifs-utils` is installed
- Check network connectivity to Samba server
- Verify credentials and share permissions
- Check mount point permissions
- **"only root can use --options" error**: Configure sudo permissions (see Sudo Configuration section above)
- **"Permission denied" error**: Check sudo configuration or use /etc/fstab for automatic mounting
- **"Failed to mount CIFS share"**: Verify mount point exists and has correct permissions

### Common Error Messages:
- `"FTP connection test failed"` - Check host, port, and credentials
- `"Cannot connect to WebDAV server"` - Check URL and credentials
- `"CIFS share not mounted"` - Check mount permissions and network
- `"Remote storage connection failed"` - Verify configuration and network

## Environment Variables

You can use environment variables for sensitive configuration:

```yaml
backup:
  remote_storage:
    enabled: true
    type: "webdav"
    webdav:
      url: "https://your-server.com/backups"
      username: "${WEBDAV_USERNAME}"
      password: "${WEBDAV_PASSWORD}"
      verify_ssl: true
```

Set environment variables:
```bash
export WEBDAV_USERNAME="your_username"
export WEBDAV_PASSWORD="your_password"
```

## Backup Process with Remote Storage

1. **Local Backup**: Create backup file locally
2. **Upload**: Upload to remote storage if enabled
3. **Verification**: Log upload success/failure
4. **Cleanup**: Remove old local backups (if configured)

## Monitoring

Check logs for remote storage operations:
```bash
tail -f logs/backup.log | grep -i "remote\|upload"
```

## Performance Considerations

- **Network Speed**: Consider bandwidth limitations
- **File Size**: Large backups may take time to upload
- **Retry Logic**: Failed uploads are logged but don't stop backup process
- **Concurrent Uploads**: Currently single-threaded uploads
