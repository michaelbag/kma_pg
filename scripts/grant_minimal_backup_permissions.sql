-- ===================================================================
-- Минимальные права для пользователя BACKUP только (read-only)
-- ===================================================================
-- Использование: 
--   psql -U postgres -d database_name -f grant_minimal_backup_permissions.sql
-- 
-- ПЕРЕД ВЫПОЛНЕНИЕМ: Замените 'backup_user' на имя вашего пользователя
--                    Замените 'database_name' на имя вашей базы данных
-- ===================================================================

-- Замените эти значения:
\set backup_user 'backup_user'
\set database_name 'target_database'

-- 1. Подключение к базе данных
GRANT CONNECT ON DATABASE :database_name TO :backup_user;

-- 2. Доступ к схеме public
GRANT USAGE ON SCHEMA public TO :backup_user;

-- 3. Чтение данных из всех существующих таблиц
GRANT SELECT ON ALL TABLES IN SCHEMA public TO :backup_user;

-- 4. Чтение последовательностей (sequences)
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO :backup_user;

-- 5. Для будущих объектов (опционально, но рекомендуется)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO :backup_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO :backup_user;

-- Если используются другие пользовательские схемы, повторите для каждой:
-- GRANT USAGE ON SCHEMA schema_name TO :backup_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA schema_name TO :backup_user;
-- GRANT SELECT ON ALL SEQUENCES IN SCHEMA schema_name TO :backup_user;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA schema_name GRANT SELECT ON TABLES TO :backup_user;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA schema_name GRANT SELECT ON SEQUENCES TO :backup_user;

-- Проверка предоставленных прав
\c :database_name
SELECT 
    'Database privileges:' as check_type,
    has_database_privilege(:'backup_user', :'database_name', 'CONNECT') as has_connect
UNION ALL
SELECT 
    'Schema privileges:',
    has_schema_privilege(:'backup_user', 'public', 'USAGE')::text
UNION ALL
SELECT 
    'Table privileges (count):',
    COUNT(*)::text
FROM information_schema.table_privileges 
WHERE grantee = :'backup_user' 
    AND table_schema = 'public' 
    AND privilege_type = 'SELECT';

\c postgres

