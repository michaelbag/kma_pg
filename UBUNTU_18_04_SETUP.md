# Установка на Ubuntu Server 18.04

## Проблема

Ubuntu 18.04 по умолчанию поставляется с Python 3.6, а проект требует Python 3.7 или выше.

## Решение

Скрипт `init_project.sh` автоматически определяет Ubuntu 18.04 и предлагает установить Python 3.8.

### Автоматическая установка

При запуске `init_project.sh` на Ubuntu 18.04:

1. Скрипт обнаружит Python 3.6
2. Предложит установить Python 3.8 из PPA `deadsnakes/ppa`
3. Автоматически установит необходимые пакеты
4. Создаст виртуальную среду с Python 3.8

### Ручная установка (если автоматическая не сработала)

Если скрипт не может установить Python 3.8 автоматически, выполните вручную:

```bash
# Добавить PPA для Python 3.8
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update

# Установить Python 3.8 и необходимые пакеты
sudo apt install -y \
    python3.8 \
    python3.8-venv \
    python3.8-dev \
    python3.8-distutils

# Установить pip для Python 3.8 (используйте специальную версию для Python 3.8)
curl -sS https://bootstrap.pypa.io/pip/3.8/get-pip.py | sudo python3.8
```

После установки Python 3.8 запустите скрипт инициализации снова:

```bash
./init_project.sh
```

Скрипт автоматически определит Python 3.8 и использует его для создания виртуальной среды.

## Альтернативные варианты

### Вариант 1: Использовать python3.8 напрямую

Если Python 3.8 уже установлен, но скрипт его не видит:

```bash
# Создать виртуальную среду вручную
python3.8 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Вариант 2: Обновить Ubuntu до 20.04+

Ubuntu 20.04 и выше поставляются с Python 3.8+ по умолчанию.

### Вариант 3: Использовать pyenv

```bash
# Установить pyenv
curl https://pyenv.run | bash

# Установить Python 3.8 через pyenv
pyenv install 3.8.18
pyenv local 3.8.18

# Создать виртуальную среду
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Проверка установки

После установки Python 3.8 проверьте версию:

```bash
python3.8 --version
# Должно вывести: Python 3.8.x
```

## Примечания

- Python 3.6 не поддерживается проектом из-за ограничений в зависимостях
- Python 3.8 работает со всеми зависимостями проекта
- Виртуальная среда будет создана с Python 3.8, даже если система Python 3.6 по умолчанию

## Поддержка

Если возникли проблемы с установкой Python 3.8, проверьте:

1. Доступность интернета для загрузки пакетов
2. Права sudo для установки пакетов
3. Логи установки для диагностики ошибок

Для получения помощи создайте issue в репозитории проекта.

