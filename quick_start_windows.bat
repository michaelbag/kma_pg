@echo off
REM PostgreSQL Backup Manager - Quick Start for Windows
REM This script provides quick access to common operations

echo ========================================
echo PostgreSQL Backup Manager - Quick Start
echo ========================================
echo.

REM Check if virtual environment exists
if not exist venv (
    echo Virtual environment not found!
    echo Please run init_project_windows.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

echo Choose an option:
echo 1. Test database connection
echo 2. Create configuration
echo 3. Create backup
echo 4. List available backups
echo 5. Restore database
echo 6. Show help
echo 7. Exit
echo.

set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" (
    echo Testing database connection...
    python src\kma_pg_backup.py --test-connection
) else if "%choice%"=="2" (
    echo Starting configuration setup...
    python src\kma_pg_config_setup.py
) else if "%choice%"=="3" (
    echo Creating backup...
    python src\kma_pg_backup.py
) else if "%choice%"=="4" (
    echo Listing available backups...
    python src\kma_pg_restore.py --list-backups
) else if "%choice%"=="5" (
    set /p backup_file="Enter backup file path: "
    set /p database_name="Enter database name: "
    echo Restoring database...
    python src\kma_pg_restore.py --backup-file "%backup_file%" --database "%database_name%" --create-db
) else if "%choice%"=="6" (
    echo Backup script help:
    python src\kma_pg_backup.py --help
    echo.
    echo Restore script help:
    python src\kma_pg_restore.py --help
) else if "%choice%"=="7" (
    echo Goodbye!
    exit /b 0
) else (
    echo Invalid choice!
)

echo.
pause
