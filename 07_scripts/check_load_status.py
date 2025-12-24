#!/usr/bin/env python3
"""Проверка статуса загрузки"""
import sys
import io
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

with engine.connect() as conn:
    # Максимальная дата
    result = conn.execute(text("SELECT MAX(event_date) FROM user_events"))
    max_date = result.fetchone()[0]
    print(f"Максимальная дата в БД: {max_date}")
    
    # Количество записей с advertiser
    result = conn.execute(text("SELECT COUNT(*) FROM user_events WHERE advertiser IS NOT NULL"))
    with_ad = result.fetchone()[0]
    
    result = conn.execute(text("SELECT COUNT(*) FROM user_events"))
    total = result.fetchone()[0]
    
    print(f"Всего записей: {total:,}")
    print(f"С advertiser: {with_ad:,} ({with_ad/total*100:.1f}%)")
    
    # Распределение по advertiser
    result = conn.execute(text("SELECT advertiser, COUNT(*) FROM user_events WHERE advertiser IS NOT NULL GROUP BY advertiser"))
    print("\nРаспределение по advertiser:")
    for row in result:
        print(f"  {row[0]}: {row[1]:,}")
    
    # Записи с 2 декабря
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
    print(f"\nЗаписи с 2 декабря:")
    print(f"  Всего: {row[0]:,}")
    print(f"  4rabet: {row[1]:,}")
    print(f"  Crorebet: {row[2]:,}")
    print(f"  Без advertiser: {row[3]:,}")

