# Развертывание с разделением прав: Администратор и рабочий пользователь

## 📋 Сценарий использования

**Администратор:**
- Имеет права sudo
- Выполняет инициализацию проекта
- Устанавливает системные зависимости

**Рабочий пользователь:**
- Не имеет прав sudo
- Выполняет операции бэкапа/восстановления
- Работает с проектом в обычном режиме

---

## 🚀 Процесс развертывания

### Шаг 1: Подготовка (от администратора)

#### 1.1 Создать рабочего пользователя (если не существует)

```bash
# От root или с sudo
sudo useradd -m -s /bin/bash kma_pg
# Или использовать существующего пользователя
```

#### 1.2 Установить Python 3.8 (для Ubuntu 18.04)

```bash
# От root
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.8 python3.8-venv python3.8-dev python3.8-distutils
curl -sS https://bootstrap.pypa.io/pip/3.8/get-pip.py | sudo python3.8
```

#### 1.3 Установить системные зависимости

```bash
# От root
sudo apt install -y \
    postgresql-client \
    cifs-utils \
    smbclient \
    build-essential \
    libpq-dev
```

---

### Шаг 2: Клонирование и инициализация (от администратора)

#### 2.1 Клонировать репозиторий

```bash
# От администратора (с sudo правами)
cd /opt  # или другое подходящее место
sudo git clone https://github.com/michaelbag/kma_pg.git
cd kma_pg
```

#### 2.2 Запустить скрипт инициализации

```bash
# От администратора (можно запустить от root или с sudo)
sudo ./init_project.sh
```

**В процессе инициализации скрипт:**
1. Запросит имя рабочего пользователя (например: `kma_pg`)
2. Установит системные зависимости (если нужно)
3. Создаст виртуальную среду
4. Установит Python зависимости
5. Передаст владение всех файлов рабочему пользователю
6. Протестирует установку от имени рабочего пользователя

---

### Шаг 3: Настройка прав доступа (от администратора)

#### 3.1 Настроить права PostgreSQL для рабочего пользователя

См. `USER_PERMISSIONS.md` для детальных инструкций.

**Минимальные права для BACKUP:**
```sql
-- От имени postgres или другого суперпользователя
GRANT CONNECT ON DATABASE database_name TO kma_pg;
GRANT USAGE ON SCHEMA public TO kma_pg;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO kma_pg;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO kma_pg;
```

**Минимальные права для RESTORE:**
```sql
GRANT CONNECT ON DATABASE database_name TO kma_pg;
GRANT CREATE ON SCHEMA public TO kma_pg;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kma_pg;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kma_pg;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO kma_pg;
```

Или используйте готовые скрипты:
```bash
# Для backup-only
sudo -u postgres psql -d database_name -f scripts/grant_minimal_backup_permissions.sql

# Для backup+restore
sudo -u postgres psql -d database_name -f scripts/grant_minimal_restore_permissions.sql
```

---

### Шаг 4: Конфигурация (от рабочего пользователя)

#### 4.1 Переключиться на рабочего пользователя

```bash
sudo su - kma_pg
cd /opt/kma_pg
```

#### 4.2 Активировать виртуальную среду

```bash
source venv/bin/activate
```

#### 4.3 Создать конфигурацию

```bash
python src/kma_pg_config_setup.py
```

#### 4.4 Протестировать подключение

```bash
python src/kma_pg_backup.py --test-connection
```

---

### Шаг 5: Создание первого бэкапа (от рабочего пользователя)

```bash
# Активировать виртуальную среду
source venv/bin/activate

# Создать бэкап
python src/kma_pg_backup.py
```

---

## 📁 Структура прав доступа

### После инициализации:

```
/opt/kma_pg/
├── venv/                    # Владелец: kma_pg
├── src/                     # Владелец: kma_pg
├── config/                  # Владелец: kma_pg
│   └── databases/          # Владелец: kma_pg
├── logs/                    # Владелец: kma_pg
├── backups/                 # Владелец: kma_pg
└── scripts/                 # Владелец: kma_pg
```

**Все файлы принадлежат рабочему пользователю `kma_pg`**

---

## 🔒 Безопасность

### Права на файлы

```bash
# Конфигурационные файлы (содержат пароли)
chmod 600 config/config.yaml
chmod 600 config/databases/*.yaml

# Директории
chmod 700 backups/
chmod 755 logs/
```

### Права рабочего пользователя

- ✅ **Может:** Читать/писать файлы проекта
- ✅ **Может:** Запускать скрипты Python
- ✅ **Может:** Использовать виртуальную среду
- ✅ **Может:** Подключаться к PostgreSQL (с правильными правами)
- ❌ **Не может:** Устанавливать системные пакеты
- ❌ **Не может:** Монтировать CIFS (требует sudo, но может использовать уже смонтированные)

---

## ⚠️ Особые случаи

### CIFS монтирование без sudo

Если рабочему пользователю нужно монтировать CIFS, есть несколько вариантов:

#### Вариант 1: Использовать уже смонтированную точку

```bash
# Администратор монтирует CIFS
sudo mount -t cifs //server/share /mnt/backup -o username=user,password=pass

# Затем меняет права на точку монтирования
sudo chown kma_pg:kma_pg /mnt/backup

# Рабочий пользователь использует уже смонтированную точку
```

#### Вариант 2: Настроить passwordless sudo только для mount.cifs

```bash
# От root, добавить в /etc/sudoers.d/kma_pg
echo "kma_pg ALL=(ALL) NOPASSWD: /sbin/mount.cifs, /bin/umount" | sudo tee /etc/sudoers.d/kma_pg
```

#### Вариант 3: Использовать fstab для автоматического монтирования

```bash
# От root, добавить в /etc/fstab
//server/share /mnt/backup cifs username=user,password=pass,uid=kma_pg,gid=kma_pg 0 0
```

---

## 📋 Чек-лист развертывания

### От администратора:
- [ ] Создан рабочий пользователь
- [ ] Установлен Python 3.8 (для Ubuntu 18.04)
- [ ] Установлены системные зависимости
- [ ] Клонирован репозиторий
- [ ] Запущен `init_project.sh`
- [ ] Указан рабочий пользователь при инициализации
- [ ] Настроены права PostgreSQL для рабочего пользователя
- [ ] Проверено владение файлов (должно быть у рабочего пользователя)

### От рабочего пользователя:
- [ ] Активирована виртуальная среда
- [ ] Создана конфигурация
- [ ] Протестировано подключение к БД
- [ ] Протестировано подключение к удаленному хранилищу
- [ ] Создан первый бэкап

---

## 🐛 Устранение проблем

### Проблема: "Permission denied" при запуске скриптов

**Решение:**
```bash
# Проверить владельца файлов
ls -la /opt/kma_pg

# Если владелец не kma_pg, исправить:
sudo chown -R kma_pg:kma_pg /opt/kma_pg
```

### Проблема: "Cannot activate virtual environment"

**Решение:**
```bash
# Проверить права на venv
ls -la venv/

# Если права неправильные:
sudo chown -R kma_pg:kma_pg venv/
```

### Проблема: "Cannot mount CIFS share"

**Решение:**
- Использовать уже смонтированную точку
- Или настроить passwordless sudo для mount.cifs
- Или использовать fstab для автоматического монтирования

---

## 📚 Дополнительная документация

- `USER_PERMISSIONS.md` - Требования к правам PostgreSQL пользователя
- `UBUNTU_18_04_SETUP.md` - Установка на Ubuntu 18.04
- `README.md` - Общая документация проекта

---

**Автор:** Documentation by AI Assistant  
**Дата:** 2025-11-02  
**Версия:** 1.0

