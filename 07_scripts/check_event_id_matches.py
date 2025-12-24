#!/usr/bin/env python3
"""Проверка совпадений event_id между CSV и БД"""
import sys
import io
import pandas as pd
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

CSV_FILE = r"C:\Users\Nalivator3000\Downloads\pixels-019b379c-d78c-71d3-9d2a-4831948c32c5-12-19-2025-17-16-24-01.csv"

print("Загружаю event_id из CSV...")
csv_df = pd.read_csv(CSV_FILE, usecols=['EVENT_ID'], nrows=10000)
csv_event_ids = set(csv_df['EVENT_ID'].dropna().astype(str))
print(f"Event IDs в CSV (первые 10k строк): {len(csv_event_ids)}")

print("\nЗагружаю event_id из БД...")
pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT event_id 
        FROM user_events 
        WHERE event_date >= '2025-12-02'::date 
          AND event_date <= '2025-12-08'::date 
        LIMIT 10000
    """))
    db_event_ids = set([str(row[0]) for row in result if row[0]])
    print(f"Event IDs в БД (первые 10k): {len(db_event_ids)}")
    
    matches = csv_event_ids & db_event_ids
    print(f"\nСовпадений: {len(matches)}")
    
    if len(matches) == 0:
        print("\n⚠ Нет совпадений по event_id!")
        print("Проверяю альтернативные варианты связывания...")
        
        # Проверяем по external_user_id + дата
        csv_sample = pd.read_csv(CSV_FILE, usecols=['EXTERNAL_USER_ID', 'PIXEL_TS'], nrows=100)
        csv_sample['PIXEL_TS'] = pd.to_datetime(csv_sample['PIXEL_TS'], errors='coerce')
        csv_sample = csv_sample.dropna()
        print(f"\nПримеры из CSV:")
        print(csv_sample.head())
        
        result = conn.execute(text("""
            SELECT external_user_id, event_date 
            FROM user_events 
            WHERE event_date >= '2025-12-02'::date 
              AND event_date <= '2025-12-08'::date 
            LIMIT 10
        """))
        print(f"\nПримеры из БД:")
        for row in result:
            print(f"  {row[0]}, {row[1]}")

