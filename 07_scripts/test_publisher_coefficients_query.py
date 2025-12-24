#!/usr/bin/env python3
"""Проверка запроса publisher_coefficients_by_period_simple.sql"""
import sys
import io
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("Проверка связывания publisher_spend с user_events...")
pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

with engine.connect() as conn:
    # Проверяем связывание
    result = conn.execute(text("""
        SELECT 
            COUNT(DISTINCT ps.publisher_id) as publishers,
            COUNT(DISTINCT ps.month) as months,
            COUNT(DISTINCT ue.advertiser) as advertisers
        FROM publisher_spend ps
        INNER JOIN public.user_events ue 
            ON ue.publisher_id = ps.publisher_id
            AND DATE_TRUNC('month', ue.event_date) = TO_DATE(ps.month || '-01', 'YYYY-MM-DD')
        WHERE ps.publisher_id != 0
          AND ue.advertiser IS NOT NULL
    """))
    row = result.fetchone()
    print(f"  Паблишеров: {row[0]}")
    print(f"  Месяцев: {row[1]}")
    print(f"  Advertisers: {row[2]}")
    print()
    
    # Проверяем распределение по брендам
    result = conn.execute(text("""
        SELECT 
            ue.advertiser,
            COUNT(DISTINCT ps.publisher_id) as publishers,
            COUNT(*) as events
        FROM publisher_spend ps
        INNER JOIN public.user_events ue 
            ON ue.publisher_id = ps.publisher_id
            AND DATE_TRUNC('month', ue.event_date) = TO_DATE(ps.month || '-01', 'YYYY-MM-DD')
        WHERE ps.publisher_id != 0
          AND ue.advertiser IS NOT NULL
        GROUP BY ue.advertiser
        ORDER BY events DESC
    """))
    print("Распределение по брендам:")
    for row in result:
        print(f"  {row[0]}: {row[1]} паблишеров, {row[2]:,} событий")
    print()
    
    # Тестируем сам запрос (первые 10 строк)
    print("Тестирую запрос (первые 10 строк)...")
    with open('superset_queries/publisher_coefficients_by_period_simple.sql', 'r', encoding='utf-8') as f:
        query = f.read()
    
    result = conn.execute(text(query))
    rows = result.fetchmany(10)
    
    if rows:
        print("✓ Запрос выполняется успешно!")
        print(f"\nПримеры результатов (первые 10):")
        print(f"{'Publisher ID':<12} {'Brand':<10} {'Format':<8} {'Month':<8} {'Coefficient':<12} {'Recommendation':<20}")
        print("-" * 80)
        for row in rows:
            print(f"{str(row[0]):<12} {str(row[4]):<10} {str(row[2]):<8} {str(row[3]):<8} {str(row[7]):<12} {str(row[9]):<20}")
    else:
        print("⚠ Запрос вернул 0 строк")

