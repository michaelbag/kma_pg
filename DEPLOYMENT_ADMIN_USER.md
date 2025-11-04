# Deployment with Role Separation: Administrator and Worker User

## 📋 Use Case Scenario

**Administrator:**
- Has sudo privileges
- Performs project initialization
- Installs system dependencies

**Worker User:**
- Does not have sudo privileges
- Performs backup/restore operations
- Works with the project in normal mode

---

## 🚀 Deployment Process

### Step 1: Preparation (as Administrator)

#### 1.1 Create Worker User (if not exists)

```bash
# As root or with sudo
sudo useradd -m -s /bin/bash kma_pg
# Or use existing user
```

#### 1.2 Install Python 3.8 (for Ubuntu 18.04)

```bash
# As root
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.8 python3.8-venv python3.8-dev python3.8-distutils
curl -sS https://bootstrap.pypa.io/pip/3.8/get-pip.py | sudo python3.8
```

#### 1.3 Install System Dependencies

```bash
# As root
sudo apt install -y \
    postgresql-client \
    cifs-utils \
    smbclient \
    build-essential \
    libpq-dev
```

---

### Step 2: Cloning and Initialization (as Administrator)

#### 2.1 Clone Repository

```bash
# As administrator (with sudo privileges)
cd /opt  # or another suitable location
sudo git clone https://github.com/michaelbag/kma_pg.git
cd kma_pg
```

#### 2.2 Run Initialization Script

```bash
# As administrator (can run as root or with sudo)
sudo ./init_project.sh
```

**During initialization, the script will:**
1. Ask for worker user name (e.g., `kma_pg`)
2. Install system dependencies (if needed)
3. Create virtual environment
4. Install Python dependencies
5. Transfer ownership of all files to worker user
6. Test installation as worker user

---

### Step 3: Access Rights Configuration (as Administrator)

#### 3.1 Configure PostgreSQL Permissions for Worker User

See `USER_PERMISSIONS.md` for detailed instructions.

**Minimum permissions for BACKUP:**
```sql
-- As postgres or another superuser
GRANT CONNECT ON DATABASE database_name TO kma_pg;
GRANT USAGE ON SCHEMA public TO kma_pg;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO kma_pg;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO kma_pg;
```

**Minimum permissions for RESTORE:**
```sql
GRANT CONNECT ON DATABASE database_name TO kma_pg;
GRANT CREATE ON SCHEMA public TO kma_pg;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kma_pg;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kma_pg;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO kma_pg;
```

Or use ready-made scripts:
```bash
# For backup-only
sudo -u postgres psql -d database_name -f scripts/grant_minimal_backup_permissions.sql

# For backup+restore
sudo -u postgres psql -d database_name -f scripts/grant_minimal_restore_permissions.sql
```

---

### Step 4: Configuration (as Worker User)

#### 4.1 Switch to Worker User

```bash
sudo su - kma_pg
cd /opt/kma_pg
```

#### 4.2 Activate Virtual Environment

```bash
source venv/bin/activate
```

#### 4.3 Create Configuration

```bash
python src/kma_pg_config_setup.py
```

#### 4.4 Test Connection

```bash
python src/kma_pg_backup.py --test-connection
```

---

### Step 5: Create First Backup (as Worker User)

```bash
# Activate virtual environment
source venv/bin/activate

# Create backup
python src/kma_pg_backup.py
```

---

## 📁 Access Rights Structure

### After Initialization:

```
/opt/kma_pg/
├── venv/                    # Owner: kma_pg
├── src/                     # Owner: kma_pg
├── config/                  # Owner: kma_pg
│   └── databases/          # Owner: kma_pg
├── logs/                    # Owner: kma_pg
├── backups/                 # Owner: kma_pg
└── scripts/                 # Owner: kma_pg
```

**All files belong to worker user `kma_pg`**

---

## 🔒 Security

### File Permissions

```bash
# Configuration files (contain passwords)
chmod 600 config/config.yaml
chmod 600 config/databases/*.yaml

# Directories
chmod 700 backups/
chmod 755 logs/
```

### Worker User Permissions

- ✅ **Can:** Read/write project files
- ✅ **Can:** Run Python scripts
- ✅ **Can:** Use virtual environment
- ✅ **Can:** Connect to PostgreSQL (with proper permissions)
- ❌ **Cannot:** Install system packages
- ❌ **Cannot:** Mount CIFS (requires sudo, but can use already mounted shares)

---

## ⚠️ Special Cases

### CIFS Mounting Without Sudo

If the worker user needs to mount CIFS, there are several options:

#### Option 1: Use Already Mounted Share

```bash
# Administrator mounts CIFS
sudo mount -t cifs //server/share /mnt/backup -o username=user,password=pass

# Then change ownership of mount point
sudo chown kma_pg:kma_pg /mnt/backup

# Worker user uses already mounted share
```

#### Option 2: Configure Passwordless Sudo Only for mount.cifs

```bash
# As root, add to /etc/sudoers.d/kma_pg
echo "kma_pg ALL=(ALL) NOPASSWD: /sbin/mount.cifs, /bin/umount" | sudo tee /etc/sudoers.d/kma_pg
```

#### Option 3: Use fstab for Automatic Mounting

```bash
# As root, add to /etc/fstab
//server/share /mnt/backup cifs username=user,password=pass,uid=kma_pg,gid=kma_pg 0 0
```

---

## 📋 Deployment Checklist

### As Administrator:
- [ ] Worker user created
- [ ] Python 3.8 installed (for Ubuntu 18.04)
- [ ] System dependencies installed
- [ ] Repository cloned
- [ ] `init_project.sh` executed
- [ ] Worker user specified during initialization
- [ ] PostgreSQL permissions configured for worker user
- [ ] File ownership verified (should belong to worker user)

### As Worker User:
- [ ] Virtual environment activated
- [ ] Configuration created
- [ ] Database connection tested
- [ ] Remote storage connection tested
- [ ] First backup created

---

## 🐛 Troubleshooting

### Problem: "Permission denied" when running scripts

**Solution:**
```bash
# Check file ownership
ls -la /opt/kma_pg

# If owner is not kma_pg, fix it:
sudo chown -R kma_pg:kma_pg /opt/kma_pg
```

### Problem: "Cannot activate virtual environment"

**Solution:**
```bash
# Check venv permissions
ls -la venv/

# If permissions are incorrect:
sudo chown -R kma_pg:kma_pg venv/
```

### Problem: "Cannot mount CIFS share"

**Solution:**
- Use already mounted share
- Or configure passwordless sudo for mount.cifs
- Or use fstab for automatic mounting

---

## 📚 Additional Documentation

- `USER_PERMISSIONS.md` - PostgreSQL user permissions requirements
- `UBUNTU_18_04_SETUP.md` - Ubuntu 18.04 setup instructions
- `README.md` - General project documentation

---

**Author:** Documentation by AI Assistant  
**Date:** 2025-11-02  
**Version:** 1.0
