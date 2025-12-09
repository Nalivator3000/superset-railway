#!/bin/bash

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

# Запускаем сервер
superset run -h 0.0.0.0 -p 8088 --with-threads --reload --debugger
