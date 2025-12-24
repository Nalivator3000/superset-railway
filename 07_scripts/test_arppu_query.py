#!/usr/bin/env python3
"""Проверка запроса arppu_by_attributes_simple.sql"""
import sys
import io
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("Проверка запроса ARPPU...")
pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

with engine.connect() as conn:
    # Проверяем, что advertiser используется корректно
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total_deposits,
            COUNT(CASE WHEN advertiser = '4rabet' THEN 1 END) as fourrabet,
            COUNT(CASE WHEN advertiser = 'Crorebet' THEN 1 END) as crorebet,
            COUNT(CASE WHEN advertiser IS NULL THEN 1 END) as null_advertiser
        FROM public.user_events
        WHERE event_type = 'deposit'
          AND converted_amount > 0
          AND external_user_id IS NOT NULL
          AND event_date >= '2025-12-02'::date
    """))
    row = result.fetchone()
    print(f"Депозиты с 2 декабря:")
    print(f"  Всего: {row[0]:,}")
    print(f"  4rabet: {row[1]:,}")
    print(f"  Crorebet: {row[2]:,}")
    print(f"  Без advertiser: {row[3]:,}")
    print()
    
    # Тестируем сам запрос (первые 20 строк)
    print("Тестирую запрос ARPPU (первые 20 строк)...")
    with open('superset_queries/arppu_by_attributes_simple.sql', 'r', encoding='utf-8') as f:
        query = f.read()
    
    result = conn.execute(text(query))
    rows = result.fetchmany(20)
    
    if rows:
        print("✓ Запрос выполняется успешно!")
        print(f"\nПримеры результатов (первые 20):")
        print(f"{'Breakdown':<15} {'Brand':<10} {'Value':<30} {'ARPPU':<12} {'Users':<10} {'Deposits':<10}")
        print("-" * 100)
        for row in rows:
            breakdown = str(row[0])[:14]
            brand = str(row[1])[:9]
            value = str(row[2])[:29] if row[2] else 'NULL'
            arppu = f"{row[11]:.2f}" if row[11] else "0.00"
            users = f"{row[9]:,}" if row[9] else "0"
            deposits = f"{row[10]:,}" if row[10] else "0"
            print(f"{breakdown:<15} {brand:<10} {value:<30} {arppu:<12} {users:<10} {deposits:<10}")
        
        # Проверяем распределение по брендам
        print("\nПроверка распределения по брендам в результатах...")
        result = conn.execute(text(query))
        all_rows = result.fetchall()
        
        brands = {}
        for row in all_rows:
            brand = row[1]
            if brand not in brands:
                brands[brand] = 0
            brands[brand] += 1
        
        print("Распределение по брендам в результатах:")
        for brand, count in sorted(brands.items()):
            print(f"  {brand}: {count} строк")
    else:
        print("⚠ Запрос вернул 0 строк")

