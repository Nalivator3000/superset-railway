#!/usr/bin/env python3
"""
Отключение асинхронных запросов в Superset через API
Это решит проблему зависания всех запросов
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
SUPERSET_PASSWORD = os.environ.get("SUPERSET_PASSWORD", "admin12345")

print("=" * 80)
print("ОТКЛЮЧЕНИЕ АСИНХРОННЫХ ЗАПРОСОВ В SUPERSET")
print("=" * 80)
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
    
    # Get CSRF token
    csrf_url = f"{SUPERSET_URL}/api/v1/security/csrf_token/"
    csrf_response = session.get(csrf_url, headers={
        "Authorization": f"Bearer {access_token}",
        "Referer": SUPERSET_URL
    }, timeout=30)
    csrf_data = csrf_response.json()
    csrf_token = csrf_data.get("result", {}).get("csrf_token") if isinstance(csrf_data.get("result"), dict) else csrf_data.get("result") or csrf_data.get("csrf_token")
    
    print("   ✓ Авторизация успешна")
except Exception as e:
    print(f"   ✗ Ошибка авторизации: {e}")
    sys.exit(1)

# Headers
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "Referer": SUPERSET_URL,
    "X-CSRFToken": csrf_token
}

# Step 2: Get all databases
print("2. Поиск баз данных...")
db_url = f"{SUPERSET_URL}/api/v1/database/"
try:
    db_response = session.get(db_url, headers=headers, timeout=30)
    db_response.raise_for_status()
    databases = db_response.json()["result"]
    
    print(f"   ✓ Найдено баз данных: {len(databases)}")
    
    # Find and update each database
    updated_count = 0
    for db in databases:
        db_id = db["id"]
        db_name = db.get("database_name", f"Database {db_id}")
        allow_async = db.get("allow_run_async", False)
        
        if allow_async:
            print(f"\n3. Обновление базы данных: {db_name} (ID: {db_id})")
            print(f"   Текущее значение allow_run_async: {allow_async}")
            
            # Get full database details
            get_db_url = f"{SUPERSET_URL}/api/v1/database/{db_id}"
            get_response = session.get(get_db_url, headers=headers, timeout=30)
            get_response.raise_for_status()
            current_db = get_response.json()["result"]
            
            # Prepare update - copy all fields and set allow_run_async to False
            update_payload = {}
            for key, value in current_db.items():
                if key not in ["id", "changed_on", "created_on", "changed_by", "created_by", 
                               "changed_by_fk", "created_by_fk", "owners", "tables"]:
                    update_payload[key] = value
            
            update_payload["allow_run_async"] = False
            
            # Update database
            try:
                update_url = f"{SUPERSET_URL}/api/v1/database/{db_id}"
                update_response = session.put(update_url, headers=headers, json=update_payload, timeout=30)
                update_response.raise_for_status()
                print(f"   ✓ Асинхронные запросы отключены")
                updated_count += 1
            except Exception as e:
                print(f"   ✗ Ошибка обновления: {e}")
        else:
            print(f"   База данных {db_name}: асинхронные запросы уже отключены")
    
    print()
    print("=" * 80)
    print(f"ОБНОВЛЕНО БАЗ ДАННЫХ: {updated_count}")
    print("=" * 80)
    print()
    print("Теперь все запросы будут выполняться синхронно.")
    print("Это медленнее, но надежнее, если Celery не настроен.")
    print()
    print("Проверка:")
    print("1. Откройте SQL Lab")
    print("2. Выполните простой запрос: SELECT 1")
    print("3. Запрос должен выполниться сразу (не зависнуть)")
    
except Exception as e:
    print(f"   ✗ Ошибка: {e}")
    sys.exit(1)

