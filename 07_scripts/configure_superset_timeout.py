#!/usr/bin/env python3
"""
Скрипт для настройки таймаутов в Superset через API
Автоматически включает асинхронные запросы и устанавливает таймаут для Database
"""
import requests
import json
import sys
import io
import os

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SUPERSET_URL = os.environ.get("SUPERSET_URL", "https://superset-railway-production-38aa.up.railway.app")
SUPERSET_USERNAME = os.environ.get("SUPERSET_USERNAME", "admin")
SUPERSET_PASSWORD = os.environ.get("SUPERSET_PASSWORD", "admin")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "Ubidex Events DB")

print("=" * 80)
print("НАСТРОЙКА ТАЙМАУТОВ В SUPERSET ЧЕРЕЗ API")
print("=" * 80)
print()
print(f"Superset URL: {SUPERSET_URL}")
print(f"Database: {DATABASE_NAME}")
print()

# Step 1: Login
print("1. Авторизация в Superset...")
session = requests.Session()

login_url = f"{SUPERSET_URL}/api/v1/security/login"
login_payload = {
    "username": SUPERSET_USERNAME,
    "password": SUPERSET_PASSWORD,
    "provider": "db",
    "refresh": True
}

try:
    login_response = session.post(login_url, json=login_payload, timeout=30)
    login_response.raise_for_status()
    access_token = login_response.json()["access_token"]
    refresh_token = login_response.json()["refresh_token"]
    
    # Get CSRF token
    csrf_token = session.cookies.get('csrf_access_token') or session.cookies.get('csrf')
    
    print("   ✓ Авторизация успешна")
except Exception as e:
    print(f"   ✗ Ошибка авторизации: {e}")
    if login_response.status_code == 401:
        print("   Проверьте SUPERSET_USERNAME и SUPERSET_PASSWORD")
    sys.exit(1)

# Headers for API requests
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

if csrf_token:
    headers["X-CSRFToken"] = csrf_token
    headers["Referer"] = SUPERSET_URL

# Step 2: Get database
print("2. Поиск базы данных...")
db_url = f"{SUPERSET_URL}/api/v1/database/"
try:
    db_response = requests.get(db_url, headers=headers, timeout=30)
    db_response.raise_for_status()
    databases = db_response.json()["result"]
    
    db_id = None
    db_data = None
    for db in databases:
        if db.get("database_name") == DATABASE_NAME:
            db_id = db["id"]
            db_data = db
            break
    
    if not db_id:
        print(f"   ✗ База данных '{DATABASE_NAME}' не найдена")
        print("   Доступные базы данных:")
        for db in databases:
            print(f"     - {db.get('database_name')} (ID: {db.get('id')})")
        sys.exit(1)
    
    print(f"   ✓ База данных найдена (ID: {db_id})")
except Exception as e:
    print(f"   ✗ Ошибка при поиске базы данных: {e}")
    sys.exit(1)

# Step 3: Get current database configuration
print("3. Получение текущей конфигурации...")
try:
    get_db_url = f"{SUPERSET_URL}/api/v1/database/{db_id}"
    get_response = requests.get(get_db_url, headers=headers, timeout=30)
    get_response.raise_for_status()
    current_db = get_response.json()["result"]
    print("   ✓ Конфигурация получена")
except Exception as e:
    print(f"   ✗ Ошибка при получении конфигурации: {e}")
    sys.exit(1)

# Step 4: Update database configuration
print("4. Обновление конфигурации...")
print()

# Prepare update payload
update_payload = {
    "database_name": current_db.get("database_name"),
    "sqlalchemy_uri": current_db.get("sqlalchemy_uri"),
    "cache_timeout": current_db.get("cache_timeout", 0),
    "expose_in_sqllab": current_db.get("expose_in_sqllab", True),
    "allow_run_async": True,  # Enable async queries
    "query_timeout": 600,  # 10 minutes in seconds
}

# Copy other existing fields
for field in ["configuration_method", "engine", "extra", "impersonate_user", 
              "is_managed_externally", "server_cert", "parameters"]:
    if field in current_db:
        update_payload[field] = current_db[field]

# Check current settings
current_async = current_db.get("allow_run_async", False)
current_timeout = current_db.get("query_timeout", 0)

print(f"   Текущие настройки:")
print(f"     - Async queries: {current_async}")
print(f"     - Query timeout: {current_timeout} секунд")
print()
print(f"   Новые настройки:")
print(f"     - Async queries: {update_payload['allow_run_async']}")
print(f"     - Query timeout: {update_payload['query_timeout']} секунд")
print()

if current_async == update_payload["allow_run_async"] and current_timeout == update_payload["query_timeout"]:
    print("   ⚠ Настройки уже установлены правильно. Ничего не нужно менять.")
    sys.exit(0)

# Update database
try:
    update_url = f"{SUPERSET_URL}/api/v1/database/{db_id}"
    update_response = requests.put(update_url, headers=headers, json=update_payload, timeout=30)
    update_response.raise_for_status()
    print("   ✓ Конфигурация обновлена успешно!")
except Exception as e:
    print(f"   ✗ Ошибка при обновлении конфигурации: {e}")
    if hasattr(e, 'response') and e.response is not None:
        try:
            error_data = e.response.json()
            print(f"   Детали ошибки: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
        except:
            print(f"   Ответ сервера: {e.response.text}")
    sys.exit(1)

print()
print("=" * 80)
print("НАСТРОЙКА ЗАВЕРШЕНА!")
print("=" * 80)
print()
print("Теперь Chart queries должны работать дольше 60 секунд без таймаута.")
print()
print("Проверка:")
print("1. Откройте Superset → Data → Databases")
print(f"2. Найдите '{DATABASE_NAME}' и проверьте настройки")
print("3. Должны быть включены: 'Allow async queries' и 'Query timeout: 600'")

