# PowerShell script to grant full access rights to a user on a PostgreSQL database
# Usage: .\grant_full_access.ps1 -DatabaseName "kma_pg_test" -Username "kma_pg_test" -SuperuserPassword "password" -Host "localhost" -Port 5432

param(
    [string]$DatabaseName = "kma_pg_test",
    [string]$Username = "kma_pg_test",
    [string]$SuperuserPassword = $null,
    [string]$Host = "localhost",
    [int]$Port = 5432
)

if (-not $SuperuserPassword) {
    $SuperuserPassword = Read-Host "Enter superuser password" -AsSecureString
    $SuperuserPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($SuperuserPassword))
}

Write-Host "Granting full access rights on database '$DatabaseName' to user '$Username'..." -ForegroundColor Green

# Set environment variable for password
$env:PGPASSWORD = $SuperuserPassword

# SQL commands to execute
$sqlCommands = @"
-- Terminate all existing connections to the database
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '$DatabaseName' AND pid <> pg_backend_pid();

-- Grant connect and create privileges on database
GRANT CONNECT ON DATABASE $DatabaseName TO $Username;
GRANT CREATE ON DATABASE $DatabaseName TO $Username;

-- Connect to target database to grant schema and table privileges
\c $DatabaseName

-- Grant all privileges on all existing schemas
GRANT ALL ON SCHEMA public TO $Username;
GRANT ALL ON SCHEMA pg_catalog TO $Username;
GRANT ALL ON SCHEMA information_schema TO $Username;

-- Grant all privileges on all existing tables in public schema
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $Username;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $Username;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO $Username;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $Username;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $Username;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO $Username;

-- Verify grants
\c postgres
SELECT 
    datname,
    pg_catalog.pg_get_userbyid(datdba) as owner,
    has_database_privilege('$Username', datname, 'CONNECT') as has_connect,
    has_database_privilege('$Username', datname, 'CREATE') as has_create
FROM pg_catalog.pg_database 
WHERE datname = '$DatabaseName';
"@

try {
    # Execute SQL commands
    $result = psql -h $Host -p $Port -U postgres -d postgres -c $sqlCommands
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Full access rights successfully granted to '$Username' on database '$DatabaseName'" -ForegroundColor Green
        Write-Host $result
    } else {
        Write-Host "Error granting access rights" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error executing SQL commands: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    # Clear password from environment
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
}

