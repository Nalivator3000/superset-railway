#!/usr/bin/env python3
"""
Обновление advertiser из CSV файла pixels для записей за 2-8 декабря
"""
import pandas as pd
import sys
import io
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("ОБНОВЛЕНИЕ ADVERTISER ИЗ PIXELS CSV (2-8 ДЕКАБРЯ)")
print("=" * 80)
print()

# CSV file path
CSV_FILE = r"C:\Users\Nalivator3000\Downloads\pixels-019b379c-d78c-71d3-9d2a-4831948c32c5-12-19-2025-17-16-24-01.csv"
CHUNK_SIZE = 50000

if not os.path.exists(CSV_FILE):
    print(f"ОШИБКА: CSV файл не найден: {CSV_FILE}")
    sys.exit(1)

print(f"CSV файл: {CSV_FILE}")
print(f"Размер чанка: {CHUNK_SIZE:,} строк")
print()

# Connect to PostgreSQL
print("Подключение к PostgreSQL...")
pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

def process_chunk(chunk_df):
    """Обработка чанка данных для обновления advertiser"""
    # Выбираем нужные колонки
    required_cols = ['EXTERNAL_USER_ID', 'PIXEL_TS', 'ADVERTISER_ID']
    
    # Проверяем наличие колонок
    missing_cols = [col for col in required_cols if col not in chunk_df.columns]
    if missing_cols:
        print(f"⚠ Предупреждение: отсутствуют колонки: {missing_cols}")
        return pd.DataFrame()
    
    chunk_df = chunk_df[required_cols].copy()
    
    # Удаляем записи без EXTERNAL_USER_ID
    chunk_df = chunk_df[chunk_df['EXTERNAL_USER_ID'].notna()]
    
    # Обрабатываем дату
    chunk_df['PIXEL_TS'] = chunk_df['PIXEL_TS'].astype(str).str.replace(' UTC', '', regex=False)
    chunk_df['event_date'] = pd.to_datetime(chunk_df['PIXEL_TS'], errors='coerce', utc=True)
    chunk_df = chunk_df.dropna(subset=['event_date'])
    
    # Фильтруем по дате (2-8 декабря)
    chunk_df = chunk_df[
        (chunk_df['event_date'] >= pd.Timestamp('2025-12-02', tz='UTC')) &
        (chunk_df['event_date'] <= pd.Timestamp('2025-12-08 23:59:59', tz='UTC'))
    ]
    
    # Маппим ADVERTISER_ID в advertiser (1 = 4rabet, 2 = Crorebet)
    chunk_df['advertiser'] = chunk_df['ADVERTISER_ID'].map({1: '4rabet', 2: 'Crorebet'})
    
    # Удаляем записи, где advertiser не определен
    chunk_df = chunk_df[chunk_df['advertiser'].notna()]
    
    # Оставляем только external_user_id, event_date и advertiser
    chunk_df = chunk_df[['EXTERNAL_USER_ID', 'event_date', 'advertiser']].rename(columns={'EXTERNAL_USER_ID': 'external_user_id'})
    
    # Конвертируем дату в формат для SQL
    chunk_df['event_date'] = chunk_df['event_date'].dt.tz_localize(None)  # Убираем timezone для SQL
    
    return chunk_df

# Подсчет строк в CSV
print("Подсчет строк в CSV...")
try:
    total_rows = sum(1 for _ in open(CSV_FILE, 'r', encoding='utf-8')) - 1  # Минус заголовок
    print(f"Всего строк в CSV: {total_rows:,}")
except Exception as e:
    print(f"⚠ Не удалось подсчитать строки: {e}")
    total_rows = 0
print()

# Начинаем обработку
print("Начинаю обработку данных...")
print("Прогресс обновляется каждые 50k строк.\n")

rows_processed = 0
rows_updated = 0
start_time = datetime.now()

try:
    with engine.connect() as conn:
        for chunk_num, chunk in enumerate(pd.read_csv(
            CSV_FILE,
            chunksize=CHUNK_SIZE,
            low_memory=False
        ), 1):
            # Обрабатываем чанк
            processed_chunk = process_chunk(chunk)
            
            if len(processed_chunk) == 0:
                rows_processed += len(chunk)
                continue
            
            # Используем временную таблицу для эффективного обновления
            try:
                # Создаем временную таблицу
                processed_chunk.to_sql('temp_advertiser_update', conn, if_exists='replace', index=False, method='multi')
                
                # Обновляем advertiser в основной таблице по external_user_id + event_date
                update_sql = """
                    UPDATE public.user_events ue
                    SET advertiser = t.advertiser
                    FROM temp_advertiser_update t
                    WHERE ue.external_user_id = t.external_user_id
                      AND DATE(ue.event_date) = DATE(t.event_date)
                      AND ue.event_date >= '2025-12-02'::date
                      AND ue.event_date <= '2025-12-08'::date
                      AND ue.advertiser IS NULL
                """
                
                result = conn.execute(text(update_sql))
                rows_updated += result.rowcount
                conn.commit()
                
                # Удаляем временную таблицу
                conn.execute(text("DROP TABLE temp_advertiser_update"))
                conn.commit()
                
            except Exception as e:
                print(f"   ⚠ Ошибка при обновлении чанка {chunk_num}: {e}")
                # Удаляем временную таблицу если она есть
                try:
                    conn.execute(text("DROP TABLE IF EXISTS temp_advertiser_update"))
                except:
                    pass
                conn.rollback()
            
            rows_processed += len(chunk)
            
            # Прогресс
            if rows_processed % 50000 == 0 or chunk_num == 1:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = rows_processed / elapsed if elapsed > 0 else 0
                remaining = total_rows - rows_processed if total_rows > 0 else 0
                eta = remaining / rate / 60 if rate > 0 and remaining > 0 else 0
                
                print(f"Прогресс: {rows_processed:,} / {total_rows:,} ({rows_processed/total_rows*100:.1f}% если известен размер) | "
                      f"Скорость: {rate:.0f} строк/сек | "
                      f"Обновлено: {rows_updated:,}")

except KeyboardInterrupt:
    print("\n\nОбработка прервана пользователем.")
    sys.exit(1)
except Exception as e:
    print(f"\n\nОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

elapsed_total = (datetime.now() - start_time).total_seconds()
print("\n" + "=" * 80)
print("ОБНОВЛЕНИЕ ЗАВЕРШЕНО!")
print("=" * 80)
print(f"Обработано строк: {rows_processed:,}")
print(f"Обновлено записей: {rows_updated:,}")
print(f"Время: {elapsed_total/60:.1f} минут")
if elapsed_total > 0:
    print(f"Средняя скорость: {rows_processed/elapsed_total:.0f} строк/сек")
print()

# Финальная проверка
print("Проверка данных в БД...")
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

print()
print("=" * 80)
print("ГОТОВО!")
print("=" * 80)

