#!/usr/bin/env python3
"""Проверка диапазона дат в базе данных"""
import sys
import io
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

with engine.connect() as conn:
    # Минимальная и максимальная дата
    result = conn.execute(text("""
        SELECT 
            MIN(event_date) as min_date,
            MAX(event_date) as max_date,
            COUNT(*) as total_records
        FROM user_events
    """))
    row = result.fetchone()
    print(f"Диапазон дат в базе данных:")
    print(f"  От: {row[0]}")
    print(f"  До: {row[1]}")
    print(f"  Всего записей: {row[2]:,}")
    print()
    
    # Распределение по месяцам
    result = conn.execute(text("""
        SELECT 
            TO_CHAR(event_date, 'YYYY-MM') as month,
            COUNT(*) as records,
            COUNT(CASE WHEN advertiser IS NOT NULL THEN 1 END) as with_advertiser,
            COUNT(CASE WHEN advertiser IS NULL THEN 1 END) as without_advertiser
        FROM user_events
        GROUP BY TO_CHAR(event_date, 'YYYY-MM')
        ORDER BY month DESC
        LIMIT 12
    """))
    print("Последние 12 месяцев:")
    print(f"{'Месяц':<12} {'Всего':<12} {'С advertiser':<15} {'Без advertiser':<15}")
    print("-" * 60)
    for row in result:
        print(f"{row[0]:<12} {row[1]:>11,} {row[2]:>14,} {row[3]:>14,}")
    print()
    
    # Статистика по датам после 2 декабря
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN advertiser = '4rabet' THEN 1 END) as fourrabet,
            COUNT(CASE WHEN advertiser = 'Crorebet' THEN 1 END) as crorebet,
            COUNT(CASE WHEN advertiser IS NULL THEN 1 END) as null_advertiser
        FROM user_events
        WHERE event_date >= '2025-12-02'
    """))
    row = result.fetchone()
    print(f"Записи с 2 декабря 2025:")
    print(f"  Всего: {row[0]:,}")
    print(f"  4rabet: {row[1]:,}")
    print(f"  Crorebet: {row[2]:,}")
    print(f"  Без advertiser: {row[3]:,}")

