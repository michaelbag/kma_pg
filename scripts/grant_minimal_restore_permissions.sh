#!/bin/bash
# ===================================================================
# Скрипт для предоставления минимальных прав RESTORE пользователю
# (включает права для backup + restore)
# ===================================================================
# Использование: 
#   ./grant_minimal_restore_permissions.sh <database_name> <username> [superuser_password] [host] [port]
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
    echo "  $0 my_database restore_user"
    echo "  $0 my_database restore_user mypassword localhost 5432"
    exit 1
fi

if [ -z "$SUPERUSER_PASSWORD" ]; then
    echo "Please provide superuser password:"
    read -s SUPERUSER_PASSWORD
fi

echo "Granting minimal RESTORE permissions to '$USERNAME' on database '$DATABASE_NAME'..."
echo "(This includes both backup and restore privileges)"

# Connect as postgres superuser and grant minimal privileges
PGPASSWORD="$SUPERUSER_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -d postgres <<EOF
-- Grant connect to database
GRANT CONNECT ON DATABASE $DATABASE_NAME TO $USERNAME;

-- Connect to target database
\c $DATABASE_NAME

-- Grant usage on schema (for reading metadata)
GRANT USAGE ON SCHEMA public TO $USERNAME;

-- Grant SELECT on all existing tables (for backup)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO $USERNAME;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO $USERNAME;

-- Grant CREATE on schema (for restore)
GRANT CREATE ON SCHEMA public TO $USERNAME;

-- Grant ALL privileges on existing objects (for restore)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $USERNAME;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $USERNAME;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO $USERNAME;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $USERNAME;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $USERNAME;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO $USERNAME;

-- Verify grants
\c postgres
SELECT 
    'Database privileges' as check_type,
    has_database_privilege('$USERNAME', '$DATABASE_NAME', 'CONNECT') as has_connect,
    has_database_privilege('$USERNAME', '$DATABASE_NAME', 'CREATE') as has_create_db
UNION ALL
SELECT 
    'Schema privileges',
    has_schema_privilege('$USERNAME', 'public', 'USAGE')::text,
    has_schema_privilege('$USERNAME', 'public', 'CREATE')::text
FROM pg_database 
WHERE datname = '$DATABASE_NAME';
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Minimal restore permissions successfully granted to '$USERNAME' on database '$DATABASE_NAME'"
    echo ""
    echo "Granted privileges:"
    echo "  - CONNECT on database"
    echo "  - USAGE and CREATE on schema public"
    echo "  - SELECT on all tables (for backup)"
    echo "  - ALL PRIVILEGES on all tables, sequences, functions (for restore)"
    echo "  - Default ALL privileges for future objects"
    echo ""
    echo "Note: To enable create_database/drop_database operations, run:"
    echo "  ./grant_create_database_permissions.sh $USERNAME"
else
    echo "✗ Error granting restore permissions"
    exit 1
fi

