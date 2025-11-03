-- ===================================================================
-- Права для создания и удаления баз данных
-- ===================================================================
-- Использование: 
--   psql -U postgres -f grant_create_database_permissions.sql
-- 
-- ПЕРЕД ВЫПОЛНЕНИЕМ: Замените 'backup_user' на имя вашего пользователя
-- ===================================================================

-- Замените это значение:
\set backup_user 'backup_user'

-- Предоставить право создания баз данных
ALTER USER :backup_user WITH CREATEDB;

-- Для PostgreSQL 13+: право на завершение соединений (для drop_database)
-- Это НЕ является минимальным правом, но требуется для функции drop_database()
GRANT pg_signal_backend TO :backup_user;

-- Проверка прав
SELECT 
    rolname,
    rolcreatedb as can_create_db,
    rolsuper as is_superuser,
    ARRAY(SELECT rolname FROM pg_roles WHERE pg_has_role(:'backup_user', rolname, 'member')) as roles
FROM pg_roles 
WHERE rolname = :'backup_user';

