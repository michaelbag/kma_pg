# PostgreSQL Backup Manager - Windows PowerShell Project Initialization Script
# Version: 1.0.0
# Author: Michael BAG <mk@remark.pro>

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PostgreSQL Backup Manager - Windows Setup" -ForegroundColor Cyan
Write-Host "Version: 1.0.0" -ForegroundColor Cyan
Write-Host "Author: Michael BAG <mk@remark.pro>" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "[1/6] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "✓ Python is installed: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if PostgreSQL is installed
Write-Host ""
Write-Host "[2/6] Checking PostgreSQL installation..." -ForegroundColor Yellow
try {
    $pgVersion = pg_dump --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "PostgreSQL not found"
    }
    Write-Host "✓ PostgreSQL client utilities are available: $pgVersion" -ForegroundColor Green
} catch {
    Write-Host "WARNING: PostgreSQL client utilities not found in PATH" -ForegroundColor Yellow
    Write-Host "Please install PostgreSQL from https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
    Write-Host "Make sure to add PostgreSQL bin directory to PATH" -ForegroundColor Yellow
    Write-Host "Continuing with setup anyway..." -ForegroundColor Yellow
}

# Create virtual environment
Write-Host ""
Write-Host "[3/6] Creating Python virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists, removing old one..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "venv"
}
python -m venv venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "✓ Virtual environment created" -ForegroundColor Green

# Activate virtual environment
Write-Host ""
Write-Host "[4/6] Activating virtual environment..." -ForegroundColor Yellow
try {
    & "venv\Scripts\Activate.ps1"
    if ($LASTEXITCODE -ne 0) {
        throw "Activation failed"
    }
    Write-Host "✓ Virtual environment activated" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to activate virtual environment" -ForegroundColor Red
    Write-Host "You may need to set execution policy:" -ForegroundColor Yellow
    Write-Host "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Upgrade pip
Write-Host ""
Write-Host "[5/6] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Failed to upgrade pip, continuing..." -ForegroundColor Yellow
} else {
    Write-Host "✓ Pip upgraded" -ForegroundColor Green
}

# Install dependencies
Write-Host ""
Write-Host "[6/6] Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    Write-Host "Please check requirements.txt and try again" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Create necessary directories
Write-Host ""
Write-Host "Creating project directories..." -ForegroundColor Yellow
$directories = @("backups", "logs", "config", "config\databases")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Host "✓ Project directories created" -ForegroundColor Green

# Test installation
Write-Host ""
Write-Host "Testing installation..." -ForegroundColor Yellow
try {
    python -c "import psycopg2, yaml, requests; print('✓ All dependencies imported successfully')" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Import test failed"
    }
    Write-Host "✓ All dependencies imported successfully" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Some dependencies may not be working correctly" -ForegroundColor Yellow
    Write-Host "Please check the installation" -ForegroundColor Yellow
}

# Test scripts
Write-Host ""
Write-Host "Testing backup script..." -ForegroundColor Yellow
try {
    python src\kma_pg_backup.py --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Backup script test failed"
    }
    Write-Host "✓ Backup script is working" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Backup script test failed" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Testing restore script..." -ForegroundColor Yellow
try {
    python src\kma_pg_restore.py --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Restore script test failed"
    }
    Write-Host "✓ Restore script is working" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Restore script test failed" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Configure your database settings:" -ForegroundColor White
Write-Host "   python src\kma_pg_config_setup.py" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Test database connection:" -ForegroundColor White
Write-Host "   python src\kma_pg_backup.py --test-connection" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Create your first backup:" -ForegroundColor White
Write-Host "   python src\kma_pg_backup.py" -ForegroundColor Gray
Write-Host ""
Write-Host "For detailed Windows setup guide, see WINDOWS_SETUP.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "To activate virtual environment in the future:" -ForegroundColor Yellow
Write-Host "   venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host ""
Read-Host "Press Enter to continue"
