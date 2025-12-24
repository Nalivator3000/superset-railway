#!/usr/bin/env python3
"""Проверка структуры таблицы google_sheets_campaigns"""
import sys
import io
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("Проверка структуры таблицы google_sheets_campaigns...")
print()

pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 
            campaignid, event_date, campaign_name, event_type, format, 
            views, clicks, spend, postview, cpa_pv
        FROM google_sheets_campaigns 
        LIMIT 5
    """))
    
    print("Примеры данных из таблицы:")
    print("-" * 100)
    for i, row in enumerate(result, 1):
        print(f"{i}. campaignID={row[0]}, date={row[1]}, name={row[2][:40] if row[2] else 'N/A'}")
        print(f"   type={row[3]}, format={row[4]}, views={row[5]}, clicks={row[6]}")
        print(f"   spend={row[7]}, postview={row[8]}, cpa_pv={row[9]}")
        print()

