#!/bin/bash
# Script to grant full access rights to a user on a PostgreSQL database
# Usage: ./grant_full_access.sh <database_name> <username> [superuser_password] [host] [port]

DATABASE_NAME="${1:-kma_pg_test}"
USERNAME="${2:-kma_pg_test}"
SUPERUSER_PASSWORD="${3}"
DB_HOST="${4:-localhost}"
DB_PORT="${5:-5432}"

if [ -z "$DATABASE_NAME" ] || [ -z "$USERNAME" ]; then
    echo "Usage: $0 <database_name> <username> [superuser_password] [host] [port]"
    exit 1
fi

echo "Granting full access rights on database '$DATABASE_NAME' to user '$USERNAME'..."

if [ -z "$SUPERUSER_PASSWORD" ]; then
    echo "Please provide superuser password:"
    read -s SUPERUSER_PASSWORD
fi

# Connect as postgres superuser and grant privileges
PGPASSWORD="$SUPERUSER_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -d postgres <<EOF
-- Terminate all existing connections to the database (except current)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '$DATABASE_NAME' AND pid <> pg_backend_pid();

-- Grant connect and create privileges on database
GRANT CONNECT ON DATABASE $DATABASE_NAME TO $USERNAME;
GRANT CREATE ON DATABASE $DATABASE_NAME TO $USERNAME;

-- Connect to target database to grant schema and table privileges
\c $DATABASE_NAME

-- Grant all privileges on all existing schemas
GRANT ALL ON SCHEMA public TO $USERNAME;
GRANT ALL ON SCHEMA pg_catalog TO $USERNAME;
GRANT ALL ON SCHEMA information_schema TO $USERNAME;

-- Grant all privileges on all existing tables in public schema
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
    datname,
    pg_catalog.pg_get_userbyid(datdba) as owner,
    has_database_privilege('$USERNAME', datname, 'CONNECT') as has_connect,
    has_database_privilege('$USERNAME', datname, 'CREATE') as has_create
FROM pg_catalog.pg_database 
WHERE datname = '$DATABASE_NAME';
EOF

if [ $? -eq 0 ]; then
    echo "Full access rights successfully granted to '$USERNAME' on database '$DATABASE_NAME'"
else
    echo "Error granting access rights"
    exit 1
fi

