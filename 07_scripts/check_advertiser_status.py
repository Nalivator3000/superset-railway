#!/usr/bin/env python3
"""Проверка статуса advertiser"""
import sys
import io
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

with engine.connect() as conn:
    total = conn.execute(text('SELECT COUNT(*) FROM user_events')).fetchone()[0]
    with_ad = conn.execute(text("SELECT COUNT(*) FROM user_events WHERE advertiser IS NOT NULL")).fetchone()[0]
    without_ad = conn.execute(text("SELECT COUNT(*) FROM user_events WHERE advertiser IS NULL")).fetchone()[0]
    before_dec2 = conn.execute(text("SELECT COUNT(*) FROM user_events WHERE event_date < '2025-12-02' AND advertiser IS NULL")).fetchone()[0]
    
    print(f'Всего записей: {total:,}')
    print(f'С advertiser: {with_ad:,} ({with_ad/total*100:.1f}%)')
    print(f'Без advertiser: {without_ad:,} ({without_ad/total*100:.1f}%)')
    print(f'К обновлению (до 2.12.2025): {before_dec2:,}')
    
    if with_ad > 0:
        result = conn.execute(text("SELECT advertiser, COUNT(*) as cnt FROM user_events WHERE advertiser IS NOT NULL GROUP BY advertiser ORDER BY cnt DESC"))
        print('\nРаспределение:')
        for row in result:
            print(f'  {row[0]}: {row[1]:,}')

