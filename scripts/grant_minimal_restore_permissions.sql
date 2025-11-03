-- ===================================================================
-- Минимальные права для пользователя RESTORE (backup + restore)
-- ===================================================================
-- Использование: 
--   psql -U postgres -d database_name -f grant_minimal_restore_permissions.sql
-- 
-- ПЕРЕД ВЫПОЛНЕНИЕМ: Замените 'restore_user' на имя вашего пользователя
--                    Замените 'database_name' на имя вашей базы данных
-- ===================================================================

-- Замените эти значения:
\set restore_user 'restore_user'
\set database_name 'target_database'

-- 1. Подключение к базе данных
GRANT CONNECT ON DATABASE :database_name TO :restore_user;

-- 2. Доступ к схеме public (для чтения метаданных)
GRANT USAGE ON SCHEMA public TO :restore_user;

-- 3. Права для BACKUP (чтение данных)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO :restore_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO :restore_user;

-- 4. Права для RESTORE (создание и изменение объектов)
GRANT CREATE ON SCHEMA public TO :restore_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO :restore_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO :restore_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO :restore_user;

-- 5. Для будущих объектов
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO :restore_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO :restore_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO :restore_user;

-- Если используются другие пользовательские схемы, повторите для каждой:
-- GRANT USAGE ON SCHEMA schema_name TO :restore_user;
-- GRANT CREATE ON SCHEMA schema_name TO :restore_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA schema_name TO :restore_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA schema_name TO :restore_user;
-- GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA schema_name TO :restore_user;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA schema_name GRANT ALL ON TABLES TO :restore_user;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA schema_name GRANT ALL ON SEQUENCES TO :restore_user;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA schema_name GRANT ALL ON FUNCTIONS TO :restore_user;

-- Проверка предоставленных прав
\c :database_name
SELECT 
    'Database privileges:' as check_type,
    has_database_privilege(:'restore_user', :'database_name', 'CONNECT') as has_connect,
    has_database_privilege(:'restore_user', :'database_name', 'CREATE') as has_create
UNION ALL
SELECT 
    'Schema privileges:',
    has_schema_privilege(:'restore_user', 'public', 'USAGE')::text,
    has_schema_privilege(:'restore_user', 'public', 'CREATE')::text
UNION ALL
SELECT 
    'Table privileges (SELECT count):',
    COUNT(*)::text,
    NULL
FROM information_schema.table_privileges 
WHERE grantee = :'restore_user' 
    AND table_schema = 'public' 
    AND privilege_type = 'SELECT'
UNION ALL
SELECT 
    'Table privileges (ALL count):',
    COUNT(*)::text,
    NULL
FROM information_schema.table_privileges 
WHERE grantee = :'restore_user' 
    AND table_schema = 'public' 
    AND privilege_type IN ('INSERT', 'UPDATE', 'DELETE');

\c postgres

