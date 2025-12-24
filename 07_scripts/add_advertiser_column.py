#!/usr/bin/env python3
"""
Добавление колонки advertiser в таблицу user_events и загрузка данных из CSV
"""
import pandas as pd
import sys
import io
import os
import argparse
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("ДОБАВЛЕНИЕ КОЛОНКИ ADVERTISER В USER_EVENTS")
print("=" * 80)
print()

# Connect to PostgreSQL
print("1. Подключение к PostgreSQL...")
pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

with engine.connect() as conn:
    # Check if column exists
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema='public' 
          AND table_name='user_events' 
          AND column_name='advertiser'
    """))
    exists = result.fetchone() is not None
    
    if exists:
        print("   ✓ Колонка 'advertiser' уже существует")
    else:
        print("   Добавляю колонку 'advertiser'...")
        conn.execute(text("ALTER TABLE public.user_events ADD COLUMN advertiser VARCHAR(50)"))
        conn.commit()
        print("   ✓ Колонка добавлена")
    
    # Create index for better performance
    print("2. Создание индекса...")
    try:
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_events_advertiser ON public.user_events(advertiser)"))
        conn.commit()
        print("   ✓ Индекс создан")
    except Exception as e:
        print(f"   (Индекс уже существует или ошибка: {e})")

print()

# Check if CSV file is provided
parser = argparse.ArgumentParser(description='Add advertiser column and load data from CSV')
parser.add_argument('--csv', type=str, help='Path to CSV file with advertiser data', default=None)
args = parser.parse_args()

if args.csv and os.path.exists(args.csv):
    print("3. Загрузка данных об Advertiser из CSV...")
    print(f"   Файл: {args.csv}")
    
    # Read CSV - нужно понять структуру
    # Предполагаем, что CSV содержит колонки для связи с user_events
    # Например: event_id, advertiser или external_user_id, advertiser, event_date
    try:
        df = pd.read_csv(args.csv)
        print(f"   Загружено строк: {len(df)}")
        print(f"   Колонки: {', '.join(df.columns)}")
        print()
        
        # Нужно понять структуру CSV - какие колонки есть
        # Возможные варианты:
        # 1. event_id, advertiser
        # 2. external_user_id, event_date, advertiser
        # 3. ubidex_id, advertiser
        
        # Пока выводим структуру для анализа
        print("   Структура CSV (первые 5 строк):")
        print(df.head().to_string())
        print()
        print("   ВАЖНО: Нужно указать, какие колонки использовать для связи с user_events")
        print("   Запустите скрипт с параметрами --link-column и --advertiser-column")
        print("   Например: python add_advertiser_column.py --csv file.csv --link-column event_id --advertiser-column Advertiser")
        
    except Exception as e:
        print(f"   ✗ Ошибка при чтении CSV: {e}")
else:
    print("3. CSV файл не указан или не найден")
    print("   Использование:")
    print("   python add_advertiser_column.py --csv path/to/file.csv")
    print()
    print("   После добавления колонки можно обновить данные:")
    print("   UPDATE public.user_events SET advertiser = '4rabet' WHERE website ILIKE '%4rabet%';")
    print("   UPDATE public.user_events SET advertiser = 'Crorebet' WHERE website ILIKE '%crorebet%';")

print()
print("=" * 80)
print("ГОТОВО!")
print("=" * 80)

