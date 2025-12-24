#!/usr/bin/env python3
"""Тест упрощенного запроса ARPPU для Crorebet"""
import sys
import io
import time
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("Тестирую упрощенный запрос ARPPU для Crorebet...")
pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

with engine.connect() as conn:
    with open('superset_queries/arppu_crorebet_trend_simple.sql', 'r', encoding='utf-8') as f:
        query = f.read()
    
    start = time.time()
    result = conn.execute(text(query))
    rows = result.fetchmany(20)
    elapsed = time.time() - start
    
    print(f"✓ Запрос выполнен за {elapsed:.2f} секунд")
    print(f"Получено строк: {len(rows)}")
    print()
    print("Примеры результатов (первые 10):")
    print(f"{'Дата':<12} {'ARPPU':<12} {'Users':<10} {'Deposits':<10} {'Revenue':<15}")
    print("-" * 70)
    for row in rows[:10]:
        print(f"{str(row[0]):<12} {row[4]:<12.2f} {row[1]:<10} {row[2]:<10} {row[3]:<15.2f}")

