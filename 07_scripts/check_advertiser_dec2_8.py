#!/usr/bin/env python3
"""Проверка статуса advertiser за 2-8 декабря"""
import sys
import io
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN advertiser = '4rabet' THEN 1 END) as fourrabet,
            COUNT(CASE WHEN advertiser = 'Crorebet' THEN 1 END) as crorebet,
            COUNT(CASE WHEN advertiser IS NULL THEN 1 END) as null_advertiser
        FROM user_events
        WHERE event_date >= '2025-12-02'::date
          AND event_date <= '2025-12-08'::date
    """))
    row = result.fetchone()
    print(f"Записи за 2-8 декабря:")
    print(f"  Всего: {row[0]:,}")
    print(f"  4rabet: {row[1]:,}")
    print(f"  Crorebet: {row[2]:,}")
    print(f"  Без advertiser: {row[3]:,}")
    print(f"  Процент с advertiser: {(row[0]-row[3])/row[0]*100:.1f}%")

