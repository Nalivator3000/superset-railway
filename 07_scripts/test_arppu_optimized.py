#!/usr/bin/env python3
"""Тест оптимизированного запроса ARPPU"""
import sys
import io
import time
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("Тестирую оптимизированный запрос ARPPU для 4rabet...")
pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

with engine.connect() as conn:
    with open('superset_queries/arppu_crorebet_trend_simple.sql', 'r', encoding='utf-8') as f:
        query = f.read()
    
    start = time.time()
    result = conn.execute(text(query))
    rows = result.fetchall()
    elapsed = time.time() - start
    
    print(f"✓ Запрос выполнен за {elapsed:.2f} секунд")
    print(f"Получено строк: {len(rows)}")
    print()
    print("Примеры результатов (первые 10):")
    print(f"{'Дата':<12} {'ARPPU':<12}")
    print("-" * 30)
    for row in rows[:10]:
        print(f"{str(row[0]):<12} {row[1]:<12.2f}")
    
    if len(rows) > 10:
        print(f"... и еще {len(rows) - 10} строк")

