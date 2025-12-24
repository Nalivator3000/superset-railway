#!/usr/bin/env python3
"""
Загрузка таблицы с указанным gid
"""
import sys
import io
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SHEET_ID = "1lLjbunQujlZ4yaKDakb_XPXLzGy_BZe-LjPi5P3o1fw"
KNOWN_GID = 1485335909  # Из URL

def load_sheet_public(sheet_id, gid=0):
    """Загрузка публичного листа через CSV export"""
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
print("ЗАГРУЗКА ТАБЛИЦЫ С УКАЗАННЫМ GID")
print("=" * 80)
print(f"Sheet ID: {SHEET_ID}")
print(f"Известный gid: {KNOWN_GID}")
print()

# Загружаем известный лист
print(f"Загрузка листа с gid={KNOWN_GID}...")
df_known = load_sheet_public(SHEET_ID, KNOWN_GID)
if df_known is None:
    print("  ⚠ Не удалось загрузить лист с известным gid")
    sys.exit(1)

print(f"  ✓ Загружено {len(df_known)} строк, {len(df_known.columns)} колонок")

# Проверяем даты
date_cols = [c for c in df_known.columns if 'date' in str(c).lower()]
if date_cols:
    try:
        df_known[date_cols[0]] = pd.to_datetime(df_known[date_cols[0]], errors='coerce')
        print(f"  Даты: {df_known[date_cols[0]].min()} - {df_known[date_cols[0]].max()}")
    except:
        pass

# Ищем второй лист (пробуем разные gid)
print("\nПоиск второго листа...")
found_gids = [KNOWN_GID]
for gid in [0, 1, 2, 3, 4, 5, 10, 20, 30, 50, 100, 200, 500, 1000, 1485335908, 1485335910]:
    if gid == KNOWN_GID:
        continue
    
    df = load_sheet_public(SHEET_ID, gid)
    if df is not None and len(df) > 0:
        cols_lower = [str(c).lower() for c in df.columns]
        has_campaign_data = any(keyword in ' '.join(cols_lower) for keyword in 
                              ['campaign', 'spend', 'click', 'view', 'format', 'event_date'])
        
        if has_campaign_data:
            # Проверяем, что это не тот же лист (сравниваем количество строк)
            if len(df) != len(df_known):
                print(f"  ✓ Найден второй лист: gid={gid}, {len(df)} строк")
                found_gids.append(gid)
                df_second = df
                break
            # Или проверяем по датам, если они отличаются
            elif date_cols:
                try:
                    df[date_cols[0]] = pd.to_datetime(df[date_cols[0]], errors='coerce')
                    if df[date_cols[0]].min() != df_known[date_cols[0]].min() or \
                       df[date_cols[0]].max() != df_known[date_cols[0]].max():
                        print(f"  ✓ Найден второй лист: gid={gid}, {len(df)} строк (даты отличаются)")
                        found_gids.append(gid)
                        df_second = df
                        break
                except:
                    pass

# Если не нашли второй лист, используем тот же gid (возможно, это объединенный лист)
if len(found_gids) == 1:
    print("  ⚠ Второй лист не найден, используем один лист для обоих типов атрибуции")
    df_second = df_known.copy()

# Загружаем в БД
print("\nЗагрузка в PostgreSQL...")
pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

with engine.connect() as conn:
    all_data = []
    
    # Обрабатываем первый лист (24_hours, так как gid из URL обычно для 24h)
    df_24h = df_known.copy()
    df_24h.columns = df_24h.columns.str.lower().str.replace(' ', '_').str.replace('-', '_')
    df_24h.columns = df_24h.columns.str.replace('[^a-z0-9_]', '', regex=True)
    df_24h['source_sheet_id'] = SHEET_ID
    df_24h['attribution_type'] = '24_hours'
    df_24h['loaded_at'] = datetime.now()
    all_data.append(df_24h)
    print(f"  Подготовлено {len(df_24h)} строк для 24_hours (gid={found_gids[0]})")
    
    # Обрабатываем второй лист (1_hour)
    df_1h = df_second.copy()
    df_1h.columns = df_1h.columns.str.lower().str.replace(' ', '_').str.replace('-', '_')
    df_1h.columns = df_1h.columns.str.replace('[^a-z0-9_]', '', regex=True)
    df_1h['source_sheet_id'] = SHEET_ID
    df_1h['attribution_type'] = '1_hour'
    df_1h['loaded_at'] = datetime.now()
    all_data.append(df_1h)
    print(f"  Подготовлено {len(df_1h)} строк для 1_hour (gid={found_gids[1] if len(found_gids) > 1 else found_gids[0]})")
    
    # Объединяем
    final_df = pd.concat(all_data, ignore_index=True)
    print(f"  Всего строк: {len(final_df)}")
    
    # Удаляем старые данные для этой таблицы (если есть)
    print("\nУдаление старых данных для этой таблицы...")
    result = conn.execute(text(f"""
        DELETE FROM google_sheets_campaigns 
        WHERE source_sheet_id = '{SHEET_ID}'
    """))
    deleted = result.rowcount
    conn.commit()
    print(f"  Удалено {deleted} старых записей")
    
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
        print(f"\n  ✓ Загружено {len(final_df)} строк")
    except Exception as e:
        print(f"  ⚠ Ошибка: {e}")
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

