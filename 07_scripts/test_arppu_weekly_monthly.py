#!/usr/bin/env python3
"""Тест запросов ARPPU по неделям и месяцам"""
import sys
import io
import time
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("Тестирую запросы ARPPU по неделям и месяцам...")
pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

with engine.connect() as conn:
    # Тест недельного запроса
    print("\n1. Недельный запрос:")
    with open('superset_queries/arppu_4rabet_weekly.sql', 'r', encoding='utf-8') as f:
        query = f.read()
    
    start = time.time()
    result = conn.execute(text(query))
    rows = result.fetchall()
    elapsed = time.time() - start
    
    print(f"  ✓ Выполнен за {elapsed:.2f} секунд")
    print(f"  Получено строк: {len(rows)}")
    print("  Примеры (первые 5):")
    for row in rows[:5]:
        print(f"    {row[0]}: ARPPU = {row[1]:.2f}")
    
    # Тест месячного запроса
    print("\n2. Месячный запрос:")
    with open('superset_queries/arppu_4rabet_monthly.sql', 'r', encoding='utf-8') as f:
        query = f.read()
    
    start = time.time()
    result = conn.execute(text(query))
    rows = result.fetchall()
    elapsed = time.time() - start
    
    print(f"  ✓ Выполнен за {elapsed:.2f} секунд")
    print(f"  Получено строк: {len(rows)}")
    print("  Примеры (первые 5):")
    for row in rows[:5]:
        print(f"    {row[0]}: ARPPU = {row[1]:.2f}")

print("\n✓ Все запросы работают корректно!")

