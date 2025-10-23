# Настройка GitHub репозитория для kma_pg

## Шаги для создания репозитория на GitHub:

### 1. Создание репозитория на GitHub.com

1. Перейдите на https://github.com/kma_pg
2. Нажмите кнопку "New repository" или "+"
3. Заполните форму:
   - **Repository name**: `kma_pg`
   - **Description**: `PostgreSQL Backup Manager - Automated backup and restore system for PostgreSQL databases`
   - **Visibility**: Public
   - **НЕ** инициализируйте с README, .gitignore или лицензией (у нас уже есть эти файлы)
4. Нажмите "Create repository"

### 2. Отправка локального репозитория на GitHub

После создания репозитория на GitHub выполните команды:

```bash
# Перейдите в директорию проекта
cd /Users/mihailkudravcev/Projects/kma_pg

# Добавьте удаленный репозиторий (если еще не добавлен)
git remote add origin https://github.com/kma_pg/kma_pg.git

# Отправьте код на GitHub
git push -u origin main
```

### 3. Проверка результата

После выполнения команд репозиторий будет доступен по адресу:
**https://github.com/kma_pg/kma_pg**

## Информация о проекте

- **Название**: PostgreSQL Backup Manager
- **Версия**: 1.0.0
- **Автор**: Michael BAG <mk@remark.pro>
- **Telegram**: https://t.me/michaelbag
- **Лицензия**: GNU GPL v3.0

## Содержимое репозитория

✅ Полная система резервного копирования PostgreSQL  
✅ Поддержка множественных форматов backup  
✅ Удаленное хранилище (FTP, WebDAV, CIFS/Samba)  
✅ Многобазовая конфигурация  
✅ Интерактивная настройка  
✅ Подробная документация  
✅ Примеры конфигураций  
✅ Виртуальное окружение Python  

## Структура файлов

```
kma_pg/
├── src/                    # Исходный код Python
├── config/                 # Примеры конфигураций
├── scripts/               # Скрипты автоматизации
├── README.md              # Основная документация
├── LICENSE                # Лицензия GNU GPL v3.0
├── requirements.txt       # Python зависимости
└── .gitignore            # Исключения для Git
```
