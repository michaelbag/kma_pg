# PowerShell script to change database owner on Windows PostgreSQL
# Usage: .\change_db_owner.ps1 -DatabaseName "kma_pg_test" -NewOwner "kma_pg_test" -SuperuserPassword "password"

param(
    [string]$DatabaseName = "kma_pg_test",
    [string]$NewOwner = "kma_pg_test",
    [string]$SuperuserPassword = $null
)

if (-not $SuperuserPassword) {
    $SuperuserPassword = Read-Host "Enter superuser password" -AsSecureString
    $SuperuserPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($SuperuserPassword))
}

Write-Host "Changing owner of database '$DatabaseName' to '$NewOwner'..." -ForegroundColor Green

# Set environment variable for password
$env:PGPASSWORD = $SuperuserPassword

# SQL commands to execute
$sqlCommands = @"
-- Terminate all existing connections to the database
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '$DatabaseName' AND pid <> pg_backend_pid();

-- Change database owner
ALTER DATABASE $DatabaseName OWNER TO $NewOwner;

-- Verify the change
SELECT datname, pg_catalog.pg_get_userbyid(datdba) as owner 
FROM pg_catalog.pg_database 
WHERE datname = '$DatabaseName';
"@

try {
    # Execute SQL commands
    $result = psql -h 1c-srv.rhana.local -p 5432 -U postgres -d postgres -c $sqlCommands
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Database owner successfully changed to '$NewOwner'" -ForegroundColor Green
        Write-Host $result
    } else {
        Write-Host "Error changing database owner" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error executing SQL commands: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    # Clear password from environment
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
}
