# Interactive Configuration Builder

Интерактивный конструктор конфигураций для PostgreSQL Backup Manager с возможностью выбора значений из существующих конфигураций.

## Возможности

- 🎯 **Интерактивное создание конфигураций** с пошаговым вводом
- 🔍 **Предложения значений** из существующих конфигураций
- 📋 **Автодополнение** для всех основных полей
- 🔒 **Безопасный ввод паролей** (не сохраняются в предложениях)
- ✅ **Предварительный просмотр** конфигурации перед сохранением
- 🎨 **Удобный интерфейс** с нумерованными опциями

## Использование

### Базовое использование

```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Запустить конструктор конфигураций
python src/kma_pg_config_builder.py
```

### С указанием директории конфигураций

```bash
python src/kma_pg_config_builder.py --config-dir /path/to/config
```

## Процесс создания конфигурации

### 1. Настройки подключения к базе данных

```
DATABASE CONNECTION SETTINGS
============================

Database name:
Available options from existing configurations:
  1. analytics_backup
  2. backup_user
  3. dev_user
  4. kma_pg_test
  5. staging_backup_user
  6. Enter custom value
Choose option (1-6): 4
Selected: kma_pg_test

PostgreSQL server hostname/IP:
Available options from existing configurations:
  1. 1c-srv.rhana.local
  2. analytics-db.company.com
  3. localhost
  4. prod-db-server.company.com
  5. staging-db-server.company.com
  6. Enter custom value
Choose option (1-6): 1
Selected: 1c-srv.rhana.local
```

### 2. Настройки резервного копирования

```
BACKUP SETTINGS
===============

Backup output directory:
Available options from existing configurations:
  1. /var/backups/postgresql/analytics
  2. /var/backups/postgresql/production
  3. /var/backups/postgresql/staging
  4. backups/development
  5. test_backup
  6. Enter custom value
Choose option (1-6): 5
Selected: test_backup

Backup format (custom/plain):
Available options from existing configurations:
  1. custom
  2. plain
  3. Enter custom value
Choose option (1-3): 1
Selected: custom
```

### 3. Политика хранения (Retention Policy)

```
RETENTION POLICY
================

Use advanced multi-level retention policy? [Y/n]: y

Local daily retention (days):
Available options from existing configurations:
  1. 14
  2. 30
  3. 60
  4. 7
  5. Enter custom value
Choose option (1-5): 4
Selected: 7
```

### 4. Удаленное хранилище

```
REMOTE STORAGE SETTINGS
=======================

Enable remote storage upload? [y/N]: y

Remote storage type (webdav/cifs/ftp):
Available options from existing configurations:
  1. cifs
  2. ftp
  3. webdav
  4. Enter custom value
Choose option (1-4): 1
Selected: cifs

CIFS server path (//server/share):
Available options from existing configurations:
  1. //files.rhana.local/kma_pg_test
  2. //your-samba-server.com/staging_backups
  3. Enter custom value
Choose option (1-3): 1
Selected: //files.rhana.local/kma_pg_test
```

### 5. Настройки логирования

```
LOGGING SETTINGS
================

Log level (DEBUG/INFO/WARNING/ERROR):
Available options from existing configurations:
  1. DEBUG
  2. INFO
  3. Enter custom value
Choose option (1-3): 2
Selected: INFO

Log file path: logs/backup_new_db.log
```

## Предварительный просмотр

После ввода всех настроек отображается сводка:

```
============================================================
CONFIGURATION SUMMARY
============================================================
Database: new_database @ 1c-srv.rhana.local:5432
Username: new_user
Enabled: True, Auto-backup: True
Output: test_backup
Format: custom, Compress: True
Retention - Local: 7d/14w/30m
Retention - Remote: 14d/30w/60m
Remote: cifs - //files.rhana.local/kma_pg_test
Logging: INFO -> logs/backup_new_db.log

Save this configuration? [Y/n]: y

✅ Configuration saved successfully: config/databases/new_database.yaml
🎉 Configuration for 'new_database' created successfully!
Use: python src/kma_pg_backup.py --database-config new_database
```

## Извлекаемые предложения

Конструктор автоматически извлекает следующие значения из существующих конфигураций:

### Подключение к базе данных
- **Хосты** - все уникальные hostname/IP адреса
- **Порты** - все используемые порты PostgreSQL
- **Пользователи** - все имена пользователей БД

### Настройки резервного копирования
- **Директории вывода** - все пути для сохранения бэкапов
- **Форматы** - все используемые форматы (custom/plain)

### Удаленное хранилище
- **Типы хранилища** - webdav, cifs, ftp
- **Серверы** - все URL и пути к серверам
- **Пользователи** - все имена пользователей для удаленного доступа

### Политика хранения
- **Дневное хранение** - все значения для daily retention
- **Недельное хранение** - все значения для weekly retention
- **Месячное хранение** - все значения для monthly retention
- **Максимальный возраст** - все значения для max_age

### Логирование
- **Уровни логирования** - DEBUG, INFO, WARNING, ERROR

## Безопасность

- 🔒 **Пароли не сохраняются** в предложениях
- 🔒 **Пароли вводятся** только при необходимости
- 🔒 **Конфигурации с паролями** исключены из репозитория
- 🔒 **Безопасное сохранение** в игнорируемые файлы

## Примеры использования

### Создание тестовой конфигурации

```bash
python src/kma_pg_config_builder.py
# Выбрать значения из существующих конфигураций
# Использовать test_backup как директорию
# Выбрать CIFS как тип удаленного хранилища
```

### Создание продакшн конфигурации

```bash
python src/kma_pg_config_builder.py
# Выбрать продакшн сервер из предложений
# Использовать /var/backups/ как директорию
# Настроить WebDAV для удаленного хранилища
# Установить длительные периоды хранения
```

## Интеграция с основным приложением

После создания конфигурации через конструктор, она автоматически становится доступной для основного приложения:

```bash
# Тестирование подключения
python src/kma_pg_backup.py --database-config new_database --test-connection

# Создание резервной копии
python src/kma_pg_backup.py --database-config new_database

# Тестирование удаленного хранилища
python src/kma_pg_backup.py --database-config new_database --test-remote-storage
```

## Устранение неполадок

### Ошибка "No existing configurations found"
- Убедитесь, что в `config/databases/` есть файлы конфигураций
- Проверьте права доступа к директории

### Ошибка "Configuration not saved"
- Проверьте права записи в директорию `config/databases/`
- Убедитесь, что имя базы данных уникально

### Пустые предложения
- Добавьте несколько примеров конфигураций
- Используйте `config/databases/example_*.yaml` как шаблоны
