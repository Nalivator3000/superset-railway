#!/usr/bin/env python3
"""
Загрузка данных из Google Sheets в PostgreSQL
Автоматически находит листы с атрибуцией 1 hour и 24 hours
"""
import sys
import io
import os
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("ЗАГРУЗКА ДАННЫХ ИЗ GOOGLE SHEETS В POSTGRESQL")
print("=" * 80)
print()

# Список ссылок на таблицы (уникальные)
SHEET_URLS = [
    "https://docs.google.com/spreadsheets/d/1jynLi9Gl7UqToVRLsNasARRxYF-r-uRwqtgINfFN8UA",
    "https://docs.google.com/spreadsheets/d/1lLjbunQujlZ4yaKDakb_XPXLzGy_BZe-LjPi5P3o1fw",
    "https://docs.google.com/spreadsheets/d/1eclCXtEAdzWy0ZWyqrAf9XvMhWS08H_XOQAXVuilFv4",
    "https://docs.google.com/spreadsheets/d/1w9LNpKs8p0Zqr1srhNeSdUI1CY1OqetQiUgqLFCrz-w",
    "https://docs.google.com/spreadsheets/d/1qwsDRLZCW04MUyEhBYLrUPUIaZlmSoq8mzcto4BmhoY",
    "https://docs.google.com/spreadsheets/d/1QJdvNtCUCaTpIRhWG-Oo5VnRefZkvGYr_JNJzI90eDU",
    "https://docs.google.com/spreadsheets/d/1Y5GiZ63QQKsSnLj4sN2U0M3plBI3kfpBf6zHVES1m98",
    "https://docs.google.com/spreadsheets/d/1vF3mTm3Xe7GZz21CBzjn6XdWuciCSWKSHJmKV5WnnuA",
    "https://docs.google.com/spreadsheets/d/1d_byAZBRMKkprlOz80MwJIfRNGVRJfXr15c7kIwIBkk",
    "https://docs.google.com/spreadsheets/d/1o6Ht1NF5nQgL0kpBcvQ4i3pYIJ-4TPVq_eC9xKYCQqo",
    "https://docs.google.com/spreadsheets/d/1QKtnSFTZMHZ26CmzX7yI9gvCuy_PhUKDhqX5bB65P-E",
    "https://docs.google.com/spreadsheets/d/1SL0zk5E8HRrsvYbVb-mIXIsXFM7j1gb91Uneqq600jc",
]

def extract_sheet_id(url):
    """Извлечение ID таблицы из URL"""
    if '/spreadsheets/d/' in url:
        return url.split('/spreadsheets/d/')[1].split('/')[0]
    return None

def load_sheet_public(sheet_id, gid=0):
    """Загрузка публичного листа через CSV export"""
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(csv_url)
        return df
    except Exception as e:
        return None

def find_attribution_sheets(sheet_id):
    """Поиск листов с атрибуцией 1 hour и 24 hours"""
    found = {}
    all_valid_sheets = []
    
    # Пробуем разные gid (расширенный список)
    for gid in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 30, 40, 50, 100, 200]:
        df = load_sheet_public(sheet_id, gid)
        if df is not None and len(df) > 0:
            # Проверяем, что это данные о кампаниях
            cols_lower = [str(c).lower() for c in df.columns]
            has_campaign_data = any(keyword in ' '.join(cols_lower) for keyword in 
                                  ['campaign', 'spend', 'click', 'view', 'impression', 'format', 'event_date', 'eventdate'])
            
            if has_campaign_data:
                all_valid_sheets.append({'gid': gid, 'df': df, 'cols': cols_lower})
    
    # Если нашли листы, пробуем определить тип атрибуции
    if len(all_valid_sheets) >= 2:
        # Берем первые два найденных листа
        found['1_hour'] = {'gid': all_valid_sheets[0]['gid'], 'df': all_valid_sheets[0]['df']}
        found['24_hours'] = {'gid': all_valid_sheets[1]['gid'], 'df': all_valid_sheets[1]['df']}
    elif len(all_valid_sheets) == 1:
        # Если только один лист, используем его для обоих типов (пользователь может исправить позже)
        found['1_hour'] = {'gid': all_valid_sheets[0]['gid'], 'df': all_valid_sheets[0]['df']}
        found['24_hours'] = {'gid': all_valid_sheets[0]['gid'], 'df': all_valid_sheets[0]['df']}
    
    return found

def normalize_column_names(df):
    """Нормализация названий колонок для PostgreSQL"""
    df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('-', '_')
    df.columns = df.columns.str.replace('[^a-z0-9_]', '', regex=True)
    return df

def process_sheet_data(df, sheet_id, attribution_type):
    """Обработка данных из листа с добавлением метаданных"""
    df = df.copy()
    df = normalize_column_names(df)
    
    # Добавляем метаданные
    df['source_sheet_id'] = sheet_id
    df['attribution_type'] = attribution_type
    df['loaded_at'] = datetime.now()
    
    return df

def create_table_if_not_exists(conn):
    """Создание таблицы для хранения данных из Google Sheets"""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS google_sheets_campaigns (
        id SERIAL PRIMARY KEY,
        source_sheet_id TEXT,
        attribution_type TEXT,
        loaded_at TIMESTAMP
    );
    """
    conn.execute(text(create_table_sql))
    conn.commit()
    print("✓ Таблица google_sheets_campaigns создана/проверена")

def add_columns_if_needed(conn, df):
    """Добавление недостающих колонок в таблицу"""
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'google_sheets_campaigns'
          AND table_schema = 'public'
    """))
    existing_columns = {row[0] for row in result}
    metadata_columns = {'id', 'source_sheet_id', 'attribution_type', 'loaded_at'}
    
    for col in df.columns:
        if col not in existing_columns and col not in metadata_columns:
            col_type = 'TEXT'
            if df[col].dtype in ['int64', 'int32']:
                col_type = 'BIGINT'
            elif df[col].dtype in ['float64', 'float32']:
                col_type = 'NUMERIC'
            elif df[col].dtype == 'bool':
                col_type = 'BOOLEAN'
            elif 'date' in col.lower() or 'time' in col.lower():
                col_type = 'TIMESTAMP'
            
            try:
                conn.execute(text(f"ALTER TABLE google_sheets_campaigns ADD COLUMN IF NOT EXISTS {col} {col_type}"))
                conn.commit()
                print(f"  ✓ Добавлена колонка: {col} ({col_type})")
            except Exception as e:
                print(f"  ⚠ Ошибка при добавлении колонки {col}: {e}")

# Подключение к PostgreSQL
print("Подключение к PostgreSQL...")
pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

all_loaded_data = []
successful_sheets = []
failed_sheets = []

with engine.connect() as conn:
    create_table_if_not_exists(conn)
    
    for sheet_url in SHEET_URLS:
        sheet_id = extract_sheet_id(sheet_url)
        if not sheet_id:
            print(f"⚠ Не удалось извлечь ID из URL: {sheet_url}")
            continue
        
        print(f"\n{'='*80}")
        print(f"Обработка таблицы: {sheet_id}")
        print('='*80)
        
        # Ищем листы с атрибуцией
        found_sheets = find_attribution_sheets(sheet_id)
        
        if not found_sheets:
            print(f"  ⚠ Не удалось найти листы с данными о кампаниях")
            failed_sheets.append(sheet_id)
            continue
        
        print(f"  Найдено листов: {len(found_sheets)}")
        
        sheet_data = []
        for attr_type, info in found_sheets.items():
            df = info['df']
            print(f"  Лист (атрибуция {attr_type}, gid={info['gid']}): {len(df)} строк, {len(df.columns)} колонок")
            
            # Обрабатываем данные
            processed_df = process_sheet_data(df, sheet_id, attr_type)
            sheet_data.append(processed_df)
        
        if sheet_data:
            # Объединяем данные из всех листов этой таблицы
            combined = pd.concat(sheet_data, ignore_index=True)
            all_loaded_data.append(combined)
            successful_sheets.append(sheet_id)
            print(f"  ✓ Подготовлено {len(combined)} строк для загрузки")
    
    # Загружаем все данные
    if all_loaded_data:
        print(f"\n{'='*80}")
        print("ЗАГРУЗКА В POSTGRESQL")
        print('='*80)
        
        final_df = pd.concat(all_loaded_data, ignore_index=True)
        print(f"Всего строк для загрузки: {len(final_df)}")
        print(f"Всего колонок: {len(final_df.columns)}")
        
        # Добавляем недостающие колонки
        print("\nПроверка структуры таблицы...")
        add_columns_if_needed(conn, final_df)
        
        # Загружаем данные
        print("\nЗагрузка данных...")
        try:
            final_df.to_sql('google_sheets_campaigns', conn, if_exists='append', index=False, method='multi')
            conn.commit()
            print(f"  ✓ Загружено {len(final_df)} строк")
        except Exception as e:
            print(f"  ⚠ Ошибка: {e}")
            # Пробуем добавить недостающие колонки и загрузить снова
            add_columns_if_needed(conn, final_df)
            final_df.to_sql('google_sheets_campaigns', conn, if_exists='append', index=False, method='multi')
            conn.commit()
            print(f"  ✓ Загружено {len(final_df)} строк (после добавления колонок)")
        
        # Проверяем загруженные данные
        print("\nПроверка загруженных данных...")
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT source_sheet_id) as unique_sheets,
                COUNT(DISTINCT attribution_type) as attribution_types,
                MIN(loaded_at) as first_load,
                MAX(loaded_at) as last_load
            FROM google_sheets_campaigns
        """))
        stats = result.fetchone()
        print(f"  Всего строк в БД: {stats[0]:,}")
        print(f"  Уникальных таблиц: {stats[1]}")
        print(f"  Типов атрибуции: {stats[2]}")
        
        # Проверяем пробелы по датам
        date_cols_result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'google_sheets_campaigns'
              AND (column_name LIKE '%date%' OR column_name LIKE '%event_date%')
        """))
        date_cols = [row[0] for row in date_cols_result]
        
        if date_cols:
            date_col = date_cols[0]
            print(f"\nПроверка пробелов по датам (колонка: {date_col})...")
            result = conn.execute(text(f"""
                SELECT 
                    DATE({date_col}) as date,
                    COUNT(*) as records
                FROM google_sheets_campaigns
                WHERE {date_col} IS NOT NULL
                GROUP BY DATE({date_col})
                ORDER BY date
            """))
            daily_stats = result.fetchall()
            
            if daily_stats:
                dates = [row[0] for row in daily_stats]
                print(f"  Диапазон дат: {min(dates)} - {max(dates)}")
                print(f"  Уникальных дат: {len(dates)}")
                
                # Проверяем на пробелы
                from datetime import timedelta
                all_dates = pd.date_range(min(dates), max(dates), freq='D')
                missing = [d for d in all_dates if d.date() not in dates]
                if missing:
                    print(f"  ⚠ Пробелы по датам: {len(missing)} дней")
                    print(f"    Примеры: {missing[:10]}")
                else:
                    print("  ✓ Пробелов по датам не обнаружено")

print("\n" + "=" * 80)
print("ГОТОВО!")
print("=" * 80)
print(f"Успешно загружено таблиц: {len(successful_sheets)}")
print(f"Не удалось загрузить: {len(failed_sheets)}")
if failed_sheets:
    print(f"  Неудачные: {failed_sheets}")

