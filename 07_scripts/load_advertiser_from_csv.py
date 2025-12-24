#!/usr/bin/env python3
"""
Загрузка данных об Advertiser из CSV в таблицу user_events
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
print("ЗАГРУЗКА ДАННЫХ ОБ ADVERTISER ИЗ CSV В USER_EVENTS")
print("=" * 80)
print()

parser = argparse.ArgumentParser(description='Load advertiser data from CSV to user_events')
parser.add_argument('--csv', type=str, required=True, help='Path to CSV file with advertiser data')
parser.add_argument('--link-column', type=str, default='event_id', 
                    help='Column name in CSV to link with user_events (default: event_id). Options: event_id, external_user_id, ubidex_id')
parser.add_argument('--advertiser-column', type=str, default='Advertiser',
                    help='Column name in CSV containing advertiser value (default: Advertiser)')
parser.add_argument('--date-column', type=str, default=None,
                    help='Optional: Column name in CSV for event_date (if linking by external_user_id + date)')
args = parser.parse_args()

# Check CSV file
if not os.path.exists(args.csv):
    print(f"ОШИБКА: CSV файл не найден: {args.csv}")
    sys.exit(1)

print(f"1. Загружаю CSV файл: {args.csv}")
try:
    df = pd.read_csv(args.csv)
    print(f"   Загружено строк: {len(df)}")
    print(f"   Колонки: {', '.join(df.columns)}")
    print()
except Exception as e:
    print(f"   ✗ Ошибка при чтении CSV: {e}")
    sys.exit(1)

# Check required columns
if args.advertiser_column not in df.columns:
    print(f"ОШИБКА: Колонка '{args.advertiser_column}' не найдена в CSV")
    print(f"   Доступные колонки: {', '.join(df.columns)}")
    sys.exit(1)

if args.link_column not in df.columns:
    print(f"ОШИБКА: Колонка '{args.link_column}' не найдена в CSV")
    print(f"   Доступные колонки: {', '.join(df.columns)}")
    sys.exit(1)

# Prepare data
print("2. Подготовка данных...")
df = df[[args.link_column, args.advertiser_column]].copy()
if args.date_column and args.date_column in df.columns:
    df[args.date_column] = pd.to_datetime(df[args.date_column], errors='coerce')
    df = df[[args.link_column, args.date_column, args.advertiser_column]].copy()

# Remove rows with missing values
df = df.dropna(subset=[args.link_column, args.advertiser_column])
df[args.advertiser_column] = df[args.advertiser_column].astype(str).str.strip()

# Normalize advertiser values
df[args.advertiser_column] = df[args.advertiser_column].str.replace('4rabet', '4rabet', case=False, regex=False)
df[args.advertiser_column] = df[args.advertiser_column].str.replace('crorebet', 'Crorebet', case=False, regex=False)

print(f"   Готово к загрузке: {len(df)} строк")
print(f"   Уникальные advertiser значения: {df[args.advertiser_column].unique()}")
print()

# Connect to PostgreSQL
print("3. Подключение к PostgreSQL...")
pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

# Check if advertiser column exists
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema='public' 
          AND table_name='user_events' 
          AND column_name='advertiser'
    """))
    if result.fetchone() is None:
        print("   Добавляю колонку 'advertiser'...")
        conn.execute(text("ALTER TABLE public.user_events ADD COLUMN advertiser VARCHAR(50)"))
        conn.commit()
        print("   ✓ Колонка добавлена")
    else:
        print("   ✓ Колонка 'advertiser' существует")

print()

# Update data using temporary table (faster for large datasets)
print("4. Обновление данных в PostgreSQL...")
print("   Использую временную таблицу для пакетного обновления...")

with engine.connect() as conn:
    # Create temporary table
    conn.execute(text("""
        CREATE TEMP TABLE temp_advertiser_data (
            link_value TEXT,
            event_date TIMESTAMP,
            advertiser VARCHAR(50)
        )
    """))
    conn.commit()
    
    # Prepare data for temp table
    temp_data = []
    for _, row in df.iterrows():
        if args.date_column and args.date_column in df.columns:
            temp_data.append({
                'link_value': str(row[args.link_column]),
                'event_date': row[args.date_column],
                'advertiser': row[args.advertiser_column]
            })
        else:
            temp_data.append({
                'link_value': str(row[args.link_column]),
                'event_date': None,
                'advertiser': row[args.advertiser_column]
            })
    
    # Insert into temp table
    temp_df = pd.DataFrame(temp_data)
    temp_df.to_sql('temp_advertiser_data', engine, if_exists='append', index=False, method='multi')
    
    # Update user_events using JOIN with temp table
    if args.link_column == 'event_id':
        result = conn.execute(text("""
            UPDATE public.user_events ue
            SET advertiser = t.advertiser
            FROM temp_advertiser_data t
            WHERE ue.event_id = t.link_value
        """))
    elif args.link_column == 'external_user_id':
        if args.date_column:
            result = conn.execute(text("""
                UPDATE public.user_events ue
                SET advertiser = t.advertiser
                FROM temp_advertiser_data t
                WHERE ue.external_user_id = t.link_value
                  AND DATE(ue.event_date) = DATE(t.event_date)
            """))
        else:
            result = conn.execute(text("""
                UPDATE public.user_events ue
                SET advertiser = t.advertiser
                FROM temp_advertiser_data t
                WHERE ue.external_user_id = t.link_value
            """))
    elif args.link_column == 'ubidex_id':
        result = conn.execute(text("""
            UPDATE public.user_events ue
            SET advertiser = t.advertiser
            FROM temp_advertiser_data t
            WHERE ue.ubidex_id = t.link_value
        """))
    else:
        print(f"   ✗ Неподдерживаемая колонка для связи: {args.link_column}")
        print("   Поддерживаемые: event_id, external_user_id, ubidex_id")
        conn.execute(text("DROP TABLE IF EXISTS temp_advertiser_data"))
        conn.commit()
        sys.exit(1)
    
    total_updated = result.rowcount
    conn.commit()
    
    # Drop temp table
    conn.execute(text("DROP TABLE IF EXISTS temp_advertiser_data"))
    conn.commit()
    
    print(f"   ✓ Обновлено записей: {total_updated:,}")

print()
print()

# Verify update
print("5. Проверка обновления...")
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT advertiser, COUNT(*) as cnt 
        FROM public.user_events 
        WHERE advertiser IS NOT NULL 
        GROUP BY advertiser 
        ORDER BY cnt DESC
    """))
    print("   Распределение по advertiser:")
    for row in result:
        print(f"     {row[0]}: {row[1]:,} записей")

print()
print("=" * 80)
print("ДАННЫЕ ОБ ADVERTISER УСПЕШНО ЗАГРУЖЕНЫ!")
print("=" * 80)
print()
print("Использование:")
print(f"  python load_advertiser_from_csv.py --csv file.csv --link-column event_id --advertiser-column Advertiser")
print(f"  python load_advertiser_from_csv.py --csv file.csv --link-column external_user_id --advertiser-column Advertiser --date-column event_date")
print()

