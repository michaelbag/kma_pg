# Система версионирования проекта

## Обзор

Проект использует **двухуровневую систему версионирования**:
- **Версия проекта** - общая версия всего проекта
- **Версия скрипта** - индивидуальная версия каждого скрипта
- **Итоговая версия** - формат `версия_проекта/версия_скрипта`

## Формат версий

### Структура версии
```
X.Y.Z
│ │ └─ Patch (исправления, мелкие изменения)
│ └─── Minor (новые функции, обратно совместимые)
└───── Major (критические изменения, несовместимые)
```

### Примеры
- `1.0.0` - первая стабильная версия
- `1.1.0` - добавлены новые функции
- `1.1.1` - исправлены ошибки
- `2.0.0` - критические изменения

## Управление версиями

### Файл VERSION
Версии хранятся в файле `VERSION` в формате JSON:

```json
{
  "project": "2.0.0",
  "scripts": {
    "kma_pg_backup.py": "1.0.1",
    "kma_pg_restore.py": "1.0.0",
    "kma_pg_storage.py": "1.0.0",
    "kma_pg_config_setup.py": "1.0.0",
    "kma_pg_config_manager.py": "1.0.0",
    "kma_pg_config_builder.py": "2.0.0",
    "kma_pg_retention.py": "1.0.0"
  }
}
```

### Команды управления версиями

```bash
# Просмотр всех версий
python src/kma_pg_version.py --list

# Получение версии конкретного скрипта
python src/kma_pg_version.py --get kma_pg_backup.py

# Инкремент версии скрипта
python src/kma_pg_version.py --increment kma_pg_backup.py --type patch

# Установка конкретной версии
python src/kma_pg_version.py --set kma_pg_backup.py 1.2.0
```

## Правила инкремента

### Patch (исправления)
- Исправления ошибок
- Улучшения производительности
- Обновления документации
- **Версия проекта**: увеличивается patch
- **Версия скрипта**: увеличивается patch

### Minor (новые функции)
- Добавление новых функций
- Расширение существующего API
- Обратно совместимые изменения
- **Версия проекта**: увеличивается minor, patch = 0
- **Версия скрипта**: увеличивается minor, patch = 0

### Major (критические изменения)
- Критические изменения API
- Несовместимые изменения
- Удаление устаревших функций
- **Версия проекта**: увеличивается major, minor = 0, patch = 0
- **Версия скрипта**: увеличивается major, minor = 0, patch = 0

## Автоматическое обновление версии проекта

При изменении версии скрипта **автоматически обновляется версия проекта**:

### Правила обновления
1. **Major increment скрипта** → Major increment проекта
2. **Minor increment скрипта** → Minor increment проекта (если >= текущего minor)
3. **Patch increment скрипта** → Patch increment проекта (если >= текущего patch)

### Примеры

#### Patch increment
```bash
# До
Project: 1.1.0
kma_pg_backup.py: 1.0.0

# После patch increment
python src/kma_pg_version.py --increment kma_pg_backup.py --type patch

# Результат
Project: 1.1.1
kma_pg_backup.py: 1.0.1
```

#### Minor increment
```bash
# До
Project: 1.1.0
kma_pg_backup.py: 1.0.0

# После minor increment
python src/kma_pg_version.py --increment kma_pg_backup.py --type minor

# Результат
Project: 1.2.0
kma_pg_backup.py: 1.1.0
```

#### Major increment
```bash
# До
Project: 1.1.0
kma_pg_backup.py: 1.0.0

# После major increment
python src/kma_pg_version.py --increment kma_pg_backup.py --type major

# Результат
Project: 2.0.0
kma_pg_backup.py: 2.0.0
```

## Использование в коде

### Импорт версии
```python
from kma_pg_version import get_version

# Получение полной версии скрипта
version = get_version('kma_pg_backup.py')
print(f"Version: {version}")  # Output: 2.0.0/1.0.1
```

### Отображение версии в CLI
```python
import argparse
from kma_pg_version import get_version

version = get_version('kma_pg_backup.py')
parser = argparse.ArgumentParser(description=f'PostgreSQL Backup Manager v{version}')
parser.add_argument('--version', '-v', action='version', 
                   version=f'PostgreSQL Backup Manager v{version}')
```

## Workflow разработки

### 1. Разработка новой функции
```bash
# Создание feature branch
git checkout -b feature/new-backup-format

# Разработка...
# Тестирование...

# Инкремент minor версии
python src/kma_pg_version.py --increment kma_pg_backup.py --type minor

# Коммит изменений
git add .
git commit -m "Add new backup format support (v2.1.0/1.1.0)"
```

### 2. Исправление ошибки
```bash
# Создание hotfix branch
git checkout -b hotfix/fix-backup-error

# Исправление...
# Тестирование...

# Инкремент patch версии
python src/kma_pg_version.py --increment kma_pg_backup.py --type patch

# Коммит изменений
git add .
git commit -m "Fix backup error (v2.1.1/1.1.1)"
```

### 3. Критические изменения
```bash
# Создание breaking-change branch
git checkout -b breaking/redesign-api

# Критические изменения...
# Тестирование...

# Инкремент major версии
python src/kma_pg_version.py --increment kma_pg_backup.py --type major

# Коммит изменений
git add .
git commit -m "Redesign API (v3.0.0/2.0.0)"
```

## Интеграция с Git

### Теги версий
```bash
# Создание тега для релиза
git tag -a v2.1.0 -m "Release v2.1.0: New backup format support"

# Отправка тегов
git push origin v2.1.0
```

### Автоматическое создание тегов
```bash
# Скрипт для автоматического создания тегов при major/minor изменениях
#!/bin/bash
VERSION=$(python src/kma_pg_version.py --get project)
if [[ $VERSION =~ ^[0-9]+\.[0-9]+\.0$ ]]; then
    git tag -a "v$VERSION" -m "Release v$VERSION"
    git push origin "v$VERSION"
fi
```

## Мониторинг версий

### Проверка версий всех скриптов
```bash
python src/kma_pg_version.py --list
```

### Проверка конкретного скрипта
```bash
python src/kma_pg_backup.py --version
```

### Программная проверка
```python
from kma_pg_version import VersionManager

vm = VersionManager()
info = vm.get_version_info()

print(f"Project version: {info['project_version']}")
for script, details in info['scripts'].items():
    print(f"{script}: {details['full_version']}")
```

## Лучшие практики

### 1. Семантическое версионирование
- **MAJOR**: несовместимые изменения API
- **MINOR**: новая функциональность (обратно совместимая)
- **PATCH**: исправления ошибок (обратно совместимые)

### 2. Коммиты
- Используйте описательные сообщения коммитов
- Указывайте версию в сообщении коммита
- Группируйте связанные изменения

### 3. Тестирование
- Тестируйте перед инкрементом версии
- Обновляйте тесты при изменении API
- Проверяйте обратную совместимость

### 4. Документация
- Обновляйте CHANGELOG.md при изменениях
- Документируйте breaking changes
- Обновляйте README при необходимости

## Примеры использования

### Создание нового скрипта
```python
#!/usr/bin/env python3
"""
New Script
Version: 2.0.0/1.0.0
"""

from kma_pg_version import get_version

def main():
    version = get_version('new_script.py')
    print(f"New Script v{version}")

if __name__ == "__main__":
    main()
```

### Обновление версии при разработке
```bash
# Начало разработки
python src/kma_pg_version.py --set new_script.py 1.0.0

# Добавление функции
python src/kma_pg_version.py --increment new_script.py --type minor

# Исправление ошибки
python src/kma_pg_version.py --increment new_script.py --type patch

# Критические изменения
python src/kma_pg_version.py --increment new_script.py --type major
```

---

**Система версионирования обеспечивает четкое отслеживание изменений и упрощает управление релизами проекта!** 🚀
