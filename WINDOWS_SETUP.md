# Windows Setup Guide

This guide provides detailed instructions for setting up the PostgreSQL Backup Manager on Windows systems.

## Prerequisites

### 1. Python Installation

**Download and install Python:**
1. Go to https://www.python.org/downloads/
2. Download Python 3.7 or later
3. **Important:** Check "Add Python to PATH" during installation
4. Verify installation:
```cmd
python --version
# or
py --version
```

### 2. PostgreSQL Installation

**Download and install PostgreSQL:**
1. Go to https://www.postgresql.org/download/windows/
2. Download PostgreSQL installer
3. **Important:** During installation, make sure to:
   - Add PostgreSQL bin directory to PATH
   - Or manually add `C:\Program Files\PostgreSQL\15\bin` to your PATH

**Verify PostgreSQL installation:**
```cmd
pg_dump --version
pg_restore --version
psql --version
```

## Project Setup

### 1. Clone or Download Project

**Using Git (if installed):**
```cmd
git clone https://github.com/michaelbag/kma_pg.git
cd kma_pg
```

**Or download ZIP:**
1. Go to https://github.com/michaelbag/kma_pg
2. Click "Code" → "Download ZIP"
3. Extract to desired location
4. Open Command Prompt in project directory

### 2. Create Virtual Environment

**Command Prompt (cmd):**
```cmd
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Verify activation (should show (venv) in prompt)
```

**PowerShell:**
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\Activate.ps1

# If you get execution policy error, run:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Install Dependencies

```cmd
# Make sure virtual environment is activated
pip install -r requirements.txt
```

### 4. Test Installation

```cmd
# Test Python imports
python -c "import psycopg2, yaml, requests; print('All dependencies OK')"

# Test backup script
python src\kma_pg_backup.py --version

# Test restore script
python src\kma_pg_restore.py --version
```

## Running the Application

### Basic Usage

**Create configuration:**
```cmd
# Interactive configuration setup
python src\kma_pg_config_setup.py

# Or use example configuration
copy config\config.example.yaml config\config.yaml
```

**Test database connection:**
```cmd
python src\kma_pg_backup.py --test-connection
```

**Create backup:**
```cmd
python src\kma_pg_backup.py
```

**Restore database:**
```cmd
python src\kma_pg_restore.py --backup-file backups\your_backup.dump --database your_db --create-db
```

## Windows-Specific Issues

### PowerShell Execution Policy

**Error:** "execution of scripts is disabled on this system"

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Python Not Found

**Error:** "python is not recognized as an internal or external command"

**Solutions:**
1. **Reinstall Python** with "Add to PATH" option
2. **Manual PATH setup:**
   - Add `C:\Python39\` and `C:\Python39\Scripts\` to PATH
   - Restart Command Prompt
3. **Use py launcher:**
```cmd
py -m venv venv
py src\kma_pg_backup.py
```

### PostgreSQL Not Found

**Error:** "pg_dump is not recognized as an internal or external command"

**Solutions:**
1. **Add PostgreSQL to PATH:**
   - Add `C:\Program Files\PostgreSQL\15\bin` to PATH
   - Restart Command Prompt
2. **Use full path:**
```cmd
"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe" --version
```

### Virtual Environment Issues

**Error:** "venv\Scripts\activate is not recognized"

**Solutions:**
1. **Use full path:**
```cmd
venv\Scripts\activate.bat
```
2. **Alternative activation:**
```cmd
call venv\Scripts\activate.bat
```

### Path Issues with Backslashes

**Use forward slashes in Python paths:**
```python
# Instead of: config\config.yaml
# Use: config/config.yaml
```

## Automation on Windows

### Task Scheduler Setup

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., daily at 2 AM)
4. Set action: Start a program
5. Program: `C:\path\to\your\venv\Scripts\python.exe`
6. Arguments: `C:\path\to\kma_pg\src\kma_pg_backup.py`
7. Start in: `C:\path\to\kma_pg`

### Batch Script Example

Create `backup.bat`:
```batch
@echo off
cd /d C:\path\to\kma_pg
call venv\Scripts\activate
python src\kma_pg_backup.py
deactivate
```

## File Paths on Windows

### Configuration Files
- Use forward slashes: `config/config.yaml`
- Or raw strings: `r"config\config.yaml"`
- Avoid backslashes in Python strings

### Backup Directories
```yaml
backup:
  output_dir: "C:/backups/postgresql"  # Use forward slashes
  # or
  output_dir: "C:\\backups\\postgresql"  # Escape backslashes
```

## Troubleshooting Commands

**Check Python version:**
```cmd
python --version
py --version
```

**Check virtual environment:**
```cmd
where python
echo %VIRTUAL_ENV%
```

**Check PostgreSQL:**
```cmd
where pg_dump
pg_dump --version
```

**Check project structure:**
```cmd
dir src
dir config
```

**Test all components:**
```cmd
python src\kma_pg_backup.py --test-connection
python src\kma_pg_backup.py --test-remote-storage
```

## Support

If you encounter issues:
1. Check this troubleshooting guide
2. Verify all prerequisites are installed
3. Ensure virtual environment is activated
4. Check file paths and permissions
5. Report issues on GitHub: https://github.com/michaelbag/kma_pg/issues
