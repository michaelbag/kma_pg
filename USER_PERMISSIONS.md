# Минимальные требования к правам технологического пользователя для бэкапа и восстановления PostgreSQL

## 📋 Обзор

Этот документ описывает **минимальные** права, необходимые технологическому пользователю PostgreSQL для создания бэкапов и восстановления баз данных с использованием `kma_pg_backup.py` и `kma_pg_restore.py`.

---

## 🔑 Минимальные права для операций

### 1. Резервное копирование (Backup) ⚠️

#### Операции, выполняемые при бэкапе:
- `pg_dump` считывает данные и метаданные из БД
- Доступ к таблицам для чтения данных
- Доступ к системным каталогам для чтения метаданных схем
- Доступ к статистике (`pg_stat_user_tables`)

#### Минимальные права для BACKUP:

```sql
-- 1. Подключение к базе данных
GRANT CONNECT ON DATABASE database_name TO backup_user;

-- 2. Чтение данных из всех таблиц схемы public (и других пользовательских схем)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_user;

-- 3. Чтение последовательностей (sequences)
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO backup_user;

-- 4. Для чтения метаданных (схемы, таблицы, индексы и т.д.)
-- Доступ к системным каталогам предоставляется автоматически всем пользователям
-- Но может потребоваться для пользовательских схем:
GRANT USAGE ON SCHEMA public TO backup_user;

-- 5. Если используются другие схемы (не public)
GRANT USAGE ON SCHEMA schema_name TO backup_user;
GRANT SELECT ON ALL TABLES IN SCHEMA schema_name TO backup_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA schema_name TO backup_user;

-- 6. Для доступа к статистике таблиц (опционально, для инкрементальных бэкапов)
-- Статистика доступна через pg_stat_user_tables для владельцев таблиц
-- Для чтения статистики нужны права на таблицы или роль pg_read_all_stats (PG 14+)
```

**Минимальный набор прав для BACKUP:**
```sql
GRANT CONNECT ON DATABASE database_name TO backup_user;
GRANT USAGE ON SCHEMA public TO backup_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO backup_user;
```

**Примечание:** Для схем отличных от `public` требуются аналогичные права.

---

### 2. Восстановление (Restore) ⚠️⚠️

#### Операции, выполняемые при восстановлении:
- Создание базы данных (если `--create-db` используется)
- Удаление базы данных (если `--clean-db` используется)
- Создание схем, таблиц, индексов, функций, триггеров
- Вставка данных в таблицы
- Установка последовательностей (sequences)
- Восстановление прав и владельцев (если не используется `--no-owner --no-privileges`)

#### Минимальные права для RESTORE:

**Вариант 1: Восстановление в существующую БД (без создания/удаления)**

```sql
-- 1. Подключение к базе данных
GRANT CONNECT ON DATABASE database_name TO restore_user;

-- 2. Создание объектов в схеме
GRANT CREATE ON SCHEMA public TO restore_user;
GRANT USAGE ON SCHEMA public TO restore_user;

-- 3. Полные права на все существующие объекты
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO restore_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO restore_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO restore_user;

-- 4. Права на создание будущих объектов
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO restore_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO restore_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO restore_user;
```

**Вариант 2: Восстановление с созданием/удалением БД (требует superuser)**

```sql
-- Требуются права SUPERUSER или CREATEDB
ALTER USER restore_user WITH CREATEDB;
-- Или
ALTER USER restore_user WITH SUPERUSER;  -- НЕ рекомендуется для безопасности
```

**Для операций drop/terminate:**
```sql
-- Для pg_terminate_backend (используется в drop_database)
-- Требуется либо SUPERUSER, либо роль pg_signal_backend (PG 13+)
GRANT pg_signal_backend TO restore_user;
```

---

## 📊 Сравнение: Минимальные vs Рекомендуемые права

### Для BACKUP только:

| Право | Минимальное | Рекомендуемое | Необходимо |
|-------|-------------|---------------|------------|
| `CONNECT` | ✅ Да | ✅ Да | Обязательно |
| `USAGE` (schema) | ✅ Да | ✅ Да | Обязательно |
| `SELECT` (tables) | ✅ Да | ✅ Да | Обязательно |
| `SELECT` (sequences) | ✅ Да | ✅ Да | Обязательно |
| `SELECT` (functions) | ⚠️ Нет* | ✅ Да | Для некоторых типов |
| `pg_read_all_stats` | ⚠️ Нет* | ✅ Да | Для статистики (PG 14+) |

\* *Может потребоваться для некоторых типов данных или расширений*

### Для RESTORE:

| Право | Минимальное | Рекомендуемое | Необходимо |
|-------|-------------|---------------|------------|
| `CONNECT` | ✅ Да | ✅ Да | Обязательно |
| `CREATE` (database) | ⚠️ Только если создаем БД | ✅ Да | Если создаем БД |
| `CREATE` (schema) | ✅ Да | ✅ Да | Обязательно |
| `ALL` (tables) | ✅ Да | ✅ Да | Обязательно |
| `ALL` (sequences) | ✅ Да | ✅ Да | Обязательно |
| `ALL` (functions) | ⚠️ Нет* | ✅ Да | Если есть функции |
| `pg_signal_backend` | ⚠️ Нет* | ✅ Да | Для drop_database |

\* *Зависит от функциональности*

---

## 🔐 Рекомендуемые роли и права

### Сценарий 1: Только бэкап (read-only доступ)

```sql
-- Создание пользователя для бэкапа
CREATE USER backup_user WITH PASSWORD 'secure_password';

-- Минимальные права для бэкапа
GRANT CONNECT ON DATABASE target_database TO backup_user;
GRANT USAGE ON SCHEMA public TO backup_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO backup_user;

-- Для всех существующих пользовательских схем
-- (повторить для каждой схемы)
GRANT USAGE ON SCHEMA custom_schema TO backup_user;
GRANT SELECT ON ALL TABLES IN SCHEMA custom_schema TO backup_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA custom_schema TO backup_user;

-- Для будущих объектов (опционально)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO backup_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO backup_user;
```

### Сценарий 2: Бэкап + Восстановление (без создания/удаления БД)

```sql
-- Создание пользователя для бэкапа и восстановления
CREATE USER backup_restore_user WITH PASSWORD 'secure_password';

-- Права для бэкапа
GRANT CONNECT ON DATABASE target_database TO backup_restore_user;
GRANT USAGE ON SCHEMA public TO backup_restore_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_restore_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO backup_restore_user;

-- Права для восстановления
GRANT CREATE ON SCHEMA public TO backup_restore_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO backup_restore_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO backup_restore_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO backup_restore_user;

-- Права на будущие объекты
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO backup_restore_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO backup_restore_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO backup_restore_user;
```

### Сценарий 3: Полный доступ (включая создание/удаление БД)

```sql
-- Создание пользователя с правами создания БД
CREATE USER full_backup_user WITH PASSWORD 'secure_password' CREATEDB;

-- Права для создания/удаления БД
-- (CREATEDB уже предоставлен выше)

-- Права для бэкапа и восстановления
GRANT CONNECT ON DATABASE target_database TO full_backup_user;
GRANT CREATE ON SCHEMA public TO full_backup_user;
GRANT USAGE ON SCHEMA public TO full_backup_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO full_backup_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO full_backup_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO full_backup_user;

-- Для операции drop_database (pg_terminate_backend)
-- PostgreSQL 13+: использовать роль pg_signal_backend
GRANT pg_signal_backend TO full_backup_user;
-- Или для более старых версий PostgreSQL:
-- ALTER USER full_backup_user WITH SUPERUSER;  -- НЕ рекомендуется
```

---

## ⚠️ Особые случаи и ограничения

### 1. Операция `drop_database()`

**Требуемые права:**
- `SUPERUSER` (полные права) **ИЛИ**
- `CREATEDB` + `pg_signal_backend` (PostgreSQL 13+)

**Проблема:**
Функция `pg_terminate_backend()` используется для завершения всех соединений перед удалением БД и требует специальных прав.

**Решение:**
```sql
-- PostgreSQL 13+
GRANT pg_signal_backend TO backup_user;

-- Для старых версий (НЕ рекомендуется для безопасности)
ALTER USER backup_user WITH SUPERUSER;
```

**Рекомендация:** Если не требуется автоматическое удаление БД, можно пропустить эту операцию и выполнять удаление вручную.

---

### 2. Операция `create_database()`

**Требуемые права:**
- `CREATEDB` привилегия для пользователя

```sql
ALTER USER backup_user WITH CREATEDB;
```

---

### 3. Восстановление с расширениями (Extensions)

**Проблема:**
При восстановлении могут возникать ошибки, связанные с расширениями (extensions), например:
```
ERROR: must be owner of extension adminpack
```

**Решение:**
- Использовать `--no-owner` и `--no-privileges` в pg_restore (уже используется в коде)
- Восстанавливать расширения отдельно от имени superuser
- Игнорировать ошибки расширений (они не критичны для данных)

---

### 4. Доступ к системным каталогам

**Информация:**
`pg_dump` автоматически получает доступ к системным каталогам (`pg_catalog`, `information_schema`) для чтения метаданных. Специальные права не требуются.

**Исключение:**
Для чтения статистики (`pg_stat_*` views) может потребоваться:
- PostgreSQL 14+: роль `pg_read_all_stats`
- Или быть владельцем объектов

---

### 5. Пользовательские схемы (не public)

**Важно:**
Если база данных использует схемы отличные от `public`, нужно предоставить права на каждую схему:

```sql
-- Для схемы custom_schema
GRANT USAGE ON SCHEMA custom_schema TO backup_user;
GRANT SELECT ON ALL TABLES IN SCHEMA custom_schema TO backup_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA custom_schema TO backup_user;

-- Для восстановления
GRANT CREATE ON SCHEMA custom_schema TO backup_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA custom_schema TO backup_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA custom_schema TO backup_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA custom_schema TO backup_user;
```

---

## 📝 SQL скрипты для настройки прав

### Минимальный скрипт для BACKUP только:

```sql
-- backup_user_permissions.sql
-- Минимальные права для создания бэкапов

-- Замените значения:
-- database_name - имя базы данных для бэкапа
-- backup_user - имя пользователя для бэкапа

GRANT CONNECT ON DATABASE database_name TO backup_user;
GRANT USAGE ON SCHEMA public TO backup_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO backup_user;

-- Для будущих объектов (опционально)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO backup_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO backup_user;
```

### Минимальный скрипт для BACKUP + RESTORE:

```sql
-- backup_restore_user_permissions.sql
-- Минимальные права для бэкапа и восстановления

-- Замените значения:
-- database_name - имя базы данных
-- backup_restore_user - имя пользователя

-- Права для бэкапа
GRANT CONNECT ON DATABASE database_name TO backup_restore_user;
GRANT USAGE ON SCHEMA public TO backup_restore_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_restore_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO backup_restore_user;

-- Права для восстановления
GRANT CREATE ON SCHEMA public TO backup_restore_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO backup_restore_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO backup_restore_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO backup_restore_user;

-- Для будущих объектов
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO backup_restore_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO backup_restore_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO backup_restore_user;
```

### Скрипт с поддержкой create_database и drop_database:

```sql
-- full_backup_user_permissions.sql
-- Полные права для всех операций (включая создание/удаление БД)

-- Создание пользователя с CREATEDB
CREATE USER full_backup_user WITH PASSWORD 'secure_password' CREATEDB;

-- Права для работы с существующими БД
GRANT CONNECT ON DATABASE database_name TO full_backup_user;
GRANT CREATE ON SCHEMA public TO full_backup_user;
GRANT USAGE ON SCHEMA public TO full_backup_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO full_backup_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO full_backup_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO full_backup_user;

-- Для операции drop_database (PostgreSQL 13+)
GRANT pg_signal_backend TO full_backup_user;

-- Для будущих объектов
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO full_backup_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO full_backup_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO full_backup_user;
```

---

## 🔒 Рекомендации по безопасности

### ✅ Best Practices:

1. **Принцип наименьших привилегий**
   - Предоставляйте только те права, которые действительно необходимы
   - Разделяйте пользователей для backup и restore если возможно

2. **Разделение прав**
   - Пользователь для бэкапа: только `SELECT`
   - Пользователь для восстановления: `ALL PRIVILEGES` (только на нужную БД)

3. **Использование ролей PostgreSQL 13+**
   - `pg_read_all_stats` - для чтения статистики
   - `pg_signal_backend` - для завершения соединений

4. **Ограничение подключений**
   ```sql
   ALTER USER backup_user WITH CONNECTION LIMIT 5;
   ```

5. **Валидация прав**
   ```sql
   -- Проверка прав пользователя
   SELECT 
       grantee, 
       privilege_type, 
       is_grantable 
   FROM information_schema.role_table_grants 
   WHERE grantee = 'backup_user' AND table_schema = 'public';
   ```

---

## 📋 Чек-лист настройки прав

### Для BACKUP:
- [ ] `CONNECT` на целевую БД
- [ ] `USAGE` на схемы (public и другие пользовательские)
- [ ] `SELECT` на все таблицы в схемах
- [ ] `SELECT` на все последовательности в схемах
- [ ] `ALTER DEFAULT PRIVILEGES` для будущих объектов (опционально)

### Для RESTORE:
- [ ] `CONNECT` на целевую БД
- [ ] `CREATE` на схемы (public и другие)
- [ ] `ALL PRIVILEGES` на все таблицы в схемах
- [ ] `ALL PRIVILEGES` на все последовательности в схемах
- [ ] `ALL PRIVILEGES` на все функции в схемах (если используются)
- [ ] `ALTER DEFAULT PRIVILEGES` для будущих объектов

### Для create_database:
- [ ] `CREATEDB` привилегия на пользователя

### Для drop_database:
- [ ] `pg_signal_backend` роль (PG 13+) **ИЛИ**
- [ ] `SUPERUSER` (НЕ рекомендуется)

---

## ⚡ Быстрая справка

### Минимальные права для BACKUP:
```sql
GRANT CONNECT ON DATABASE db_name TO user;
GRANT USAGE ON SCHEMA public TO user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO user;
```

### Минимальные права для RESTORE:
```sql
GRANT CONNECT ON DATABASE db_name TO user;
GRANT CREATE ON SCHEMA public TO user;
GRANT ALL ON ALL TABLES IN SCHEMA public TO user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO user;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO user;
```

### Для create_database:
```sql
ALTER USER user WITH CREATEDB;
```

### Для drop_database (PG 13+):
```sql
GRANT pg_signal_backend TO user;
```

---

## 📚 Дополнительные ресурсы

- [PostgreSQL GRANT Documentation](https://www.postgresql.org/docs/current/sql-grant.html)
- [PostgreSQL Privilege System](https://www.postgresql.org/docs/current/ddl-priv.html)
- [pg_dump Documentation](https://www.postgresql.org/docs/current/app-pgdump.html)
- [pg_restore Documentation](https://www.postgresql.org/docs/current/app-pgrestore.html)

---

**Автор:** Documentation by AI Assistant  
**Дата:** 2025-11-02  
**Версия:** 1.0

