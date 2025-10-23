@echo off
REM PostgreSQL Backup Manager - Windows Project Initialization Script
REM Version: 1.0.0
REM Author: Michael BAG <mk@remark.pro>

echo ========================================
echo PostgreSQL Backup Manager - Windows Setup
echo Version: 1.0.0
echo Author: Michael BAG ^<mk@remark.pro^>
echo ========================================
echo.

REM Check if Python is installed
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)
python --version
echo ✓ Python is installed

REM Check if PostgreSQL is installed
echo.
echo [2/6] Checking PostgreSQL installation...
pg_dump --version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: PostgreSQL client utilities not found in PATH
    echo Please install PostgreSQL from https://www.postgresql.org/download/windows/
    echo Make sure to add PostgreSQL bin directory to PATH
    echo.
    echo Continuing with setup anyway...
) else (
    pg_dump --version
    echo ✓ PostgreSQL client utilities are available
)

REM Create virtual environment
echo.
echo [3/6] Creating Python virtual environment...
if exist venv (
    echo Virtual environment already exists, removing old one...
    rmdir /s /q venv
)
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo ✓ Virtual environment created

REM Activate virtual environment
echo.
echo [4/6] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo ✓ Virtual environment activated

REM Upgrade pip
echo.
echo [5/6] Upgrading pip...
python -m pip install --upgrade pip
echo ✓ Pip upgraded

REM Install dependencies
echo.
echo [6/6] Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    echo Please check requirements.txt and try again
    pause
    exit /b 1
)
echo ✓ Dependencies installed

REM Create necessary directories
echo.
echo Creating project directories...
if not exist backups mkdir backups
if not exist logs mkdir logs
if not exist config mkdir config
if not exist config\databases mkdir config\databases
echo ✓ Project directories created

REM Test installation
echo.
echo Testing installation...
python -c "import psycopg2, yaml, requests; print('✓ All dependencies imported successfully')" 2>nul
if %errorlevel% neq 0 (
    echo WARNING: Some dependencies may not be working correctly
    echo Please check the installation
)

REM Test scripts
echo.
echo Testing backup script...
python src\kma_pg_backup.py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Backup script test failed
) else (
    echo ✓ Backup script is working
)

echo.
echo Testing restore script...
python src\kma_pg_restore.py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Restore script test failed
) else (
    echo ✓ Restore script is working
)

echo.
echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Configure your database settings:
echo    python src\kma_pg_config_setup.py
echo.
echo 2. Test database connection:
echo    python src\kma_pg_backup.py --test-connection
echo.
echo 3. Create your first backup:
echo    python src\kma_pg_backup.py
echo.
echo For detailed Windows setup guide, see WINDOWS_SETUP.md
echo.
echo To activate virtual environment in the future:
echo    venv\Scripts\activate
echo.
pause
