#!/bin/bash
# Script to change database owner
# Usage: ./change_db_owner.sh <database_name> <new_owner> [superuser_password]

DATABASE_NAME="${1:-kma_pg_test}"
NEW_OWNER="${2:-kma_pg_test}"
SUPERUSER_PASSWORD="${3}"

echo "Changing owner of database '$DATABASE_NAME' to '$NEW_OWNER'..."

if [ -z "$SUPERUSER_PASSWORD" ]; then
    echo "Please provide superuser password:"
    read -s SUPERUSER_PASSWORD
fi

# Connect as postgres superuser and change owner
PGPASSWORD="$SUPERUSER_PASSWORD" psql -h 1c-srv.rhana.local -p 5432 -U postgres -d postgres <<EOF
-- Terminate all existing connections to the database
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '$DATABASE_NAME' AND pid <> pg_backend_pid();

-- Change database owner
ALTER DATABASE $DATABASE_NAME OWNER TO $NEW_OWNER;

-- Verify the change
SELECT datname, pg_catalog.pg_get_userbyid(datdba) as owner 
FROM pg_catalog.pg_database 
WHERE datname = '$DATABASE_NAME';
EOF

if [ $? -eq 0 ]; then
    echo "Database owner successfully changed to '$NEW_OWNER'"
else
    echo "Error changing database owner"
    exit 1
fi

