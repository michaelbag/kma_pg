#!/bin/bash
# ===================================================================
# Скрипт для предоставления минимальных прав BACKUP пользователю
# ===================================================================
# Использование: 
#   ./grant_minimal_backup_permissions.sh <database_name> <username> [superuser_password] [host] [port]
# ===================================================================

DATABASE_NAME="${1:-kma_pg_test}"
USERNAME="${2:-kma_pg_test}"
SUPERUSER_PASSWORD="${3}"
DB_HOST="${4:-localhost}"
DB_PORT="${5:-5432}"

if [ -z "$DATABASE_NAME" ] || [ -z "$USERNAME" ]; then
    echo "Usage: $0 <database_name> <username> [superuser_password] [host] [port]"
    echo ""
    echo "Example:"
    echo "  $0 my_database backup_user"
    echo "  $0 my_database backup_user mypassword localhost 5432"
    exit 1
fi

if [ -z "$SUPERUSER_PASSWORD" ]; then
    echo "Please provide superuser password:"
    read -s SUPERUSER_PASSWORD
fi

echo "Granting minimal BACKUP permissions to '$USERNAME' on database '$DATABASE_NAME'..."

# Connect as postgres superuser and grant minimal privileges
PGPASSWORD="$SUPERUSER_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -d postgres <<EOF
-- Grant connect to database
GRANT CONNECT ON DATABASE $DATABASE_NAME TO $USERNAME;

-- Connect to target database
\c $DATABASE_NAME

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO $USERNAME;

-- Grant SELECT on all existing tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO $USERNAME;

-- Grant SELECT on all existing sequences
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO $USERNAME;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO $USERNAME;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO $USERNAME;

-- Verify grants
\c postgres
SELECT 
    'Database privileges' as check_type,
    has_database_privilege('$USERNAME', '$DATABASE_NAME', 'CONNECT') as has_connect
UNION ALL
SELECT 
    'Schema privileges',
    has_schema_privilege('$USERNAME', 'public', 'USAGE')::text
FROM pg_database 
WHERE datname = '$DATABASE_NAME';
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Minimal backup permissions successfully granted to '$USERNAME' on database '$DATABASE_NAME'"
    echo ""
    echo "Granted privileges:"
    echo "  - CONNECT on database"
    echo "  - USAGE on schema public"
    echo "  - SELECT on all tables"
    echo "  - SELECT on all sequences"
    echo "  - Default SELECT privileges for future objects"
else
    echo "✗ Error granting backup permissions"
    exit 1
fi

