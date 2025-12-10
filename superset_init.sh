#!/bin/bash

# Установка psycopg2-binary если его нет
pip install --no-cache-dir psycopg2-binary || true

# Инициализация БД
superset db upgrade

# Создаем admin пользователя (если еще не создан)
superset fab create-admin \
    --username "${ADMIN_USERNAME:-admin}" \
    --firstname Admin \
    --lastname User \
    --email "${ADMIN_EMAIL:-admin@superset.com}" \
    --password "${ADMIN_PASSWORD:-admin}" || true

# Инициализируем Superset
superset init

# Запускаем сервер (Railway использует PORT env variable или 8080 по умолчанию)
PORT=${PORT:-8080}
superset run -h 0.0.0.0 -p $PORT --with-threads --reload --debugger
