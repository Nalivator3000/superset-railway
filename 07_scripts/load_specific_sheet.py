#!/usr/bin/env python3
"""
Загрузка конкретной таблицы с поиском правильных листов
"""
import sys
import io
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SHEET_ID = "1lLjbunQujlZ4yaKDakb_XPXLzGy_BZe-LjPi5P3o1fw"

def load_sheet_public(sheet_id, gid=0):
    """Загрузка публичного листа через CSV export"""
    # Пробуем разные форматы URL
    urls = [
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}",
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}&usp=sharing",
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}",
    ]
    
    for url in urls:
        try:
            df = pd.read_csv(url)
            if df is not None and len(df) > 0:
                return df
        except Exception as e:
            continue
    
    return None

print("=" * 80)
print("ПОИСК ЛИСТОВ В ТАБЛИЦЕ")
print("=" * 80)
print(f"Sheet ID: {SHEET_ID}")
print()

# Пробуем разные gid
found_sheets = {}
for gid in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 30, 40, 50, 100, 200, 500, 1000]:
    df = load_sheet_public(SHEET_ID, gid)
    if df is not None and len(df) > 0:
        cols_lower = [str(c).lower() for c in df.columns]
        has_campaign_data = any(keyword in ' '.join(cols_lower) for keyword in 
                              ['campaign', 'spend', 'click', 'view', 'impression', 'format', 'event_date', 'eventdate'])
        
        if has_campaign_data:
            # Проверяем диапазон дат
            date_cols = [c for c in df.columns if 'date' in str(c).lower()]
            date_range = "N/A"
            if date_cols:
                try:
                    df[date_cols[0]] = pd.to_datetime(df[date_cols[0]], errors='coerce')
                    date_range = f"{df[date_cols[0]].min()} - {df[date_cols[0]].max()}"
                except:
                    pass
            
            print(f"  gid={gid}: {len(df)} строк, {len(df.columns)} колонок, даты: {date_range}")
            found_sheets[gid] = df

print(f"\nНайдено листов с данными: {len(found_sheets)}")
print()

# Если нашли листы, пробуем определить тип атрибуции
if len(found_sheets) >= 2:
    gids = sorted(found_sheets.keys())
    print(f"Используем gid={gids[0]} для 1_hour и gid={gids[1]} для 24_hours")
    
    # Загружаем в БД
    print("\nЗагрузка в PostgreSQL...")
    pg_uri = get_postgres_connection_string()
    engine = create_engine(pg_uri)
    
    with engine.connect() as conn:
        all_data = []
        
        # Обрабатываем лист 1_hour
        df_1h = found_sheets[gids[0]].copy()
        df_1h.columns = df_1h.columns.str.lower().str.replace(' ', '_').str.replace('-', '_')
        df_1h.columns = df_1h.columns.str.replace('[^a-z0-9_]', '', regex=True)
        df_1h['source_sheet_id'] = SHEET_ID
        df_1h['attribution_type'] = '1_hour'
        df_1h['loaded_at'] = datetime.now()
        all_data.append(df_1h)
        print(f"  Подготовлено {len(df_1h)} строк для 1_hour (gid={gids[0]})")
        
        # Обрабатываем лист 24_hours
        df_24h = found_sheets[gids[1]].copy()
        df_24h.columns = df_24h.columns.str.lower().str.replace(' ', '_').str.replace('-', '_')
        df_24h.columns = df_24h.columns.str.replace('[^a-z0-9_]', '', regex=True)
        df_24h['source_sheet_id'] = SHEET_ID
        df_24h['attribution_type'] = '24_hours'
        df_24h['loaded_at'] = datetime.now()
        all_data.append(df_24h)
        print(f"  Подготовлено {len(df_24h)} строк для 24_hours (gid={gids[1]})")
        
        # Объединяем
        final_df = pd.concat(all_data, ignore_index=True)
        print(f"  Всего строк: {len(final_df)}")
        
        # Добавляем недостающие колонки
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'google_sheets_campaigns'
              AND table_schema = 'public'
        """))
        existing_columns = {row[0] for row in result}
        metadata_columns = {'id', 'source_sheet_id', 'attribution_type', 'loaded_at'}
        
        for col in final_df.columns:
            if col not in existing_columns and col not in metadata_columns:
                col_type = 'TEXT'
                if final_df[col].dtype in ['int64', 'int32']:
                    col_type = 'BIGINT'
                elif final_df[col].dtype in ['float64', 'float32']:
                    col_type = 'NUMERIC'
                elif final_df[col].dtype == 'bool':
                    col_type = 'BOOLEAN'
                elif 'date' in col.lower() or 'time' in col.lower():
                    col_type = 'TIMESTAMP'
                
                try:
                    conn.execute(text(f"ALTER TABLE google_sheets_campaigns ADD COLUMN IF NOT EXISTS {col} {col_type}"))
                    conn.commit()
                except Exception as e:
                    print(f"  ⚠ Ошибка при добавлении колонки {col}: {e}")
        
        # Загружаем данные
        try:
            final_df.to_sql('google_sheets_campaigns', conn, if_exists='append', index=False, method='multi')
            conn.commit()
            print(f"  ✓ Загружено {len(final_df)} строк")
        except Exception as e:
            print(f"  ⚠ Ошибка: {e}")
            # Пробуем еще раз
            final_df.to_sql('google_sheets_campaigns', conn, if_exists='append', index=False, method='multi')
            conn.commit()
            print(f"  ✓ Загружено {len(final_df)} строк (повторная попытка)")
        
        # Проверяем загруженные данные
        result = conn.execute(text(f"""
            SELECT 
                attribution_type,
                COUNT(*) as rows,
                MIN(event_date) as min_date,
                MAX(event_date) as max_date
            FROM google_sheets_campaigns
            WHERE source_sheet_id = '{SHEET_ID}'
            GROUP BY attribution_type
        """))
        print("\nЗагруженные данные:")
        for row in result:
            print(f"  {row[0]}: {row[1]} строк, даты: {row[2]} - {row[3]}")

print("\n" + "=" * 80)
print("ГОТОВО!")
print("=" * 80)

