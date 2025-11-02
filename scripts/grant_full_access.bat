@echo off
REM Script to grant full access rights to a user on a PostgreSQL database
REM Usage: grant_full_access.bat [database_name] [username] [superuser_password] [host] [port]

set DATABASE_NAME=%1
if "%DATABASE_NAME%"=="" set DATABASE_NAME=kma_pg_test

set USERNAME=%2
if "%USERNAME%"=="" set USERNAME=kma_pg_test

set SUPERUSER_PASSWORD=%3

set DB_HOST=%4
if "%DB_HOST%"=="" set DB_HOST=localhost

set DB_PORT=%5
if "%DB_PORT%"=="" set DB_PORT=5432

if "%SUPERUSER_PASSWORD%"=="" (
    echo Please provide superuser password:
    set /p SUPERUSER_PASSWORD=
)

echo Granting full access rights on database '%DATABASE_NAME%' to user '%USERNAME%'...

REM Create temporary SQL file
echo -- Terminate all existing connections to the database > temp_grant_access.sql
echo SELECT pg_terminate_backend(pid^) >> temp_grant_access.sql
echo FROM pg_stat_activity >> temp_grant_access.sql
echo WHERE datname = '%DATABASE_NAME%' AND pid ^<^> pg_backend_pid(^); >> temp_grant_access.sql
echo. >> temp_grant_access.sql
echo -- Grant connect and create privileges on database >> temp_grant_access.sql
echo GRANT CONNECT ON DATABASE %DATABASE_NAME% TO %USERNAME%; >> temp_grant_access.sql
echo GRANT CREATE ON DATABASE %DATABASE_NAME% TO %USERNAME%; >> temp_grant_access.sql
echo. >> temp_grant_access.sql
echo \c %DATABASE_NAME% >> temp_grant_access.sql
echo. >> temp_grant_access.sql
echo -- Grant all privileges on all existing schemas >> temp_grant_access.sql
echo GRANT ALL ON SCHEMA public TO %USERNAME%; >> temp_grant_access.sql
echo GRANT ALL ON SCHEMA pg_catalog TO %USERNAME%; >> temp_grant_access.sql
echo GRANT ALL ON SCHEMA information_schema TO %USERNAME%; >> temp_grant_access.sql
echo. >> temp_grant_access.sql
echo -- Grant all privileges on all existing tables in public schema >> temp_grant_access.sql
echo GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO %USERNAME%; >> temp_grant_access.sql
echo GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO %USERNAME%; >> temp_grant_access.sql
echo GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO %USERNAME%; >> temp_grant_access.sql
echo. >> temp_grant_access.sql
echo -- Set default privileges for future objects >> temp_grant_access.sql
echo ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO %USERNAME%; >> temp_grant_access.sql
echo ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO %USERNAME%; >> temp_grant_access.sql
echo ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO %USERNAME%; >> temp_grant_access.sql

REM Execute SQL commands
set PGPASSWORD=%SUPERUSER_PASSWORD%
psql -h %DB_HOST% -p %DB_PORT% -U postgres -d postgres -f temp_grant_access.sql

if %ERRORLEVEL% EQU 0 (
    echo Full access rights successfully granted to '%USERNAME%' on database '%DATABASE_NAME%'
) else (
    echo Error granting access rights
    exit /b 1
)

REM Clean up temporary file
del temp_grant_access.sql

pause

