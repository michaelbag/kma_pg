@echo off
REM Script to change database owner on Windows PostgreSQL
REM Usage: change_db_owner.bat [database_name] [new_owner] [superuser_password]

set DATABASE_NAME=%1
if "%DATABASE_NAME%"=="" set DATABASE_NAME=kma_pg_test

set NEW_OWNER=%2
if "%NEW_OWNER%"=="" set NEW_OWNER=kma_pg_test

set SUPERUSER_PASSWORD=%3
if "%SUPERUSER_PASSWORD%"=="" (
    echo Please provide superuser password:
    set /p SUPERUSER_PASSWORD=
)

echo Changing owner of database '%DATABASE_NAME%' to '%NEW_OWNER%'...

REM Create temporary SQL file
echo -- Terminate all existing connections to the database > temp_change_owner.sql
echo SELECT pg_terminate_backend(pid^) >> temp_change_owner.sql
echo FROM pg_stat_activity >> temp_change_owner.sql
echo WHERE datname = '%DATABASE_NAME%' AND pid ^<^> pg_backend_pid(^); >> temp_change_owner.sql
echo. >> temp_change_owner.sql
echo -- Change database owner >> temp_change_owner.sql
echo ALTER DATABASE %DATABASE_NAME% OWNER TO %NEW_OWNER%; >> temp_change_owner.sql
echo. >> temp_change_owner.sql
echo -- Verify the change >> temp_change_owner.sql
echo SELECT datname, pg_catalog.pg_get_userbyid(datdba^) as owner >> temp_change_owner.sql
echo FROM pg_catalog.pg_database >> temp_change_owner.sql
echo WHERE datname = '%DATABASE_NAME%'; >> temp_change_owner.sql

REM Execute SQL commands
set PGPASSWORD=%SUPERUSER_PASSWORD%
psql -h 1c-srv.rhana.local -p 5432 -U postgres -d postgres -f temp_change_owner.sql

if %ERRORLEVEL% EQU 0 (
    echo Database owner successfully changed to '%NEW_OWNER%'
) else (
    echo Error changing database owner
    exit /b 1
)

REM Clean up temporary file
del temp_change_owner.sql

pause
