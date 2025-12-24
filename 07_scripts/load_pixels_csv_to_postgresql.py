#!/usr/bin/env python3
"""
Загрузка данных из CSV файла pixels в PostgreSQL с обновлением advertiser
"""
import pandas as pd
import sys
import io
import os
from datetime import datetime
from datetime import timezone
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("ЗАГРУЗКА ДАННЫХ ИЗ PIXELS CSV В POSTGRESQL")
print("=" * 80)
print()

# CSV file path
CSV_FILE = r"C:\Users\Nalivator3000\Downloads\pixels-019b375b-b97e-7560-8e6a-35d27c7cb891-12-19-2025-16-05-16-01.csv"
CHUNK_SIZE = 50000
END_DATE = datetime(2025, 12, 18, 23, 59, 59, tzinfo=timezone.utc)  # До 18.12.2025 включительно

if not os.path.exists(CSV_FILE):
    print(f"ОШИБКА: CSV файл не найден: {CSV_FILE}")
    sys.exit(1)

print(f"CSV файл: {CSV_FILE}")
print(f"Размер чанка: {CHUNK_SIZE:,} строк")
print(f"Фильтр по дате: до {END_DATE.strftime('%Y-%m-%d %H:%M:%S')} включительно")
print()

# Connect to PostgreSQL
print("Подключение к PostgreSQL...")
pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

def process_chunk(chunk_df):
    """Обработка чанка данных"""
    # Выбираем нужные колонки
    columns_mapping = {
        'EVENT_ID': 'event_id',
        'EXTERNAL_USER_ID': 'external_user_id',
        'UBIDEX_ID': 'ubidex_id',
        'TYPE': 'event_type',
        'PIXEL_TS': 'event_date',  # Используем PIXEL_TS как основную дату
        'PUBLISHER_ID': 'publisher_id',
        'CAMPAIGN_ID': 'campaign_id',
        'SUB_ID': 'sub_id',
        'AFFILIATE_ID': 'affiliate_id',
        'DEPOSIT_AMOUNT': 'deposit_amount',
        'CURRENCY': 'currency',
        'CONVERTED_AMOUNT': 'converted_amount',
        'CONVERTED_CURRENCY': 'converted_currency',
        'WEBSITE': 'website',
        'COUNTRY': 'country',
        'TRANSACTION_ID': 'transaction_id',
        'ADVERTISER_ID': 'advertiser_id'  # Для маппинга в advertiser
    }
    
    # Выбираем только существующие колонки
    available_cols = {k: v for k, v in columns_mapping.items() if k in chunk_df.columns}
    chunk_df = chunk_df[list(available_cols.keys())].copy()
    chunk_df.columns = [available_cols[col] for col in chunk_df.columns]
    
    # Обрабатываем дату
    # Сначала проверяем, есть ли EVENT_TS в исходных данных
    if 'EVENT_TS' in chunk_df.columns and chunk_df['event_date'].isna().any():
        # Заполняем пустые PIXEL_TS из EVENT_TS
        chunk_df['event_date'] = chunk_df['event_date'].fillna(chunk_df['EVENT_TS'])
    
    if 'event_date' in chunk_df.columns:
        # Убираем ' UTC' из строки даты
        chunk_df['event_date'] = chunk_df['event_date'].astype(str).str.replace(' UTC', '', regex=False)
        # Парсим дату (поддерживаем разные форматы)
        chunk_df['event_date'] = pd.to_datetime(chunk_df['event_date'], errors='coerce', utc=True)
        # Фильтруем по дате (до 18.12.2025 включительно)
        chunk_df = chunk_df[chunk_df['event_date'] <= END_DATE]
        # Удаляем записи без даты
        chunk_df = chunk_df.dropna(subset=['event_date'])
    
    # Маппим ADVERTISER_ID в advertiser (1 = 4rabet, 2 = Crorebet)
    if 'advertiser_id' in chunk_df.columns:
        chunk_df['advertiser'] = chunk_df['advertiser_id'].map({1: '4rabet', 2: 'Crorebet'})
        chunk_df = chunk_df.drop(columns=['advertiser_id'])
    else:
        chunk_df['advertiser'] = None
    
    # Удаляем временные колонки, если они есть
    if 'EVENT_TS' in chunk_df.columns:
        chunk_df = chunk_df.drop(columns=['EVENT_TS'])
    
    # Конвертируем числовые поля
    if 'publisher_id' in chunk_df.columns:
        chunk_df['publisher_id'] = pd.to_numeric(chunk_df['publisher_id'], errors='coerce').astype('Int64')
    if 'campaign_id' in chunk_df.columns:
        chunk_df['campaign_id'] = pd.to_numeric(chunk_df['campaign_id'], errors='coerce').astype('Int64')
    if 'deposit_amount' in chunk_df.columns:
        chunk_df['deposit_amount'] = pd.to_numeric(chunk_df['deposit_amount'], errors='coerce')
    if 'converted_amount' in chunk_df.columns:
        chunk_df['converted_amount'] = pd.to_numeric(chunk_df['converted_amount'], errors='coerce')
    
    # Конвертируем ubidex_id в строку
    if 'ubidex_id' in chunk_df.columns:
        chunk_df['ubidex_id'] = chunk_df['ubidex_id'].astype(str)
    
    # Заменяем NaN на None для SQL NULL
    chunk_df = chunk_df.where(pd.notnull(chunk_df), None)
    
    # Удаляем записи без event_id (если они есть)
    if 'event_id' in chunk_df.columns:
        chunk_df = chunk_df[chunk_df['event_id'].notna()]
    
    return chunk_df

# Проверяем количество строк в CSV
print("Подсчет строк в CSV...")
total_rows = sum(1 for _ in open(CSV_FILE, 'r', encoding='utf-8')) - 1  # Минус заголовок
print(f"Всего строк в CSV: {total_rows:,}")
print()

# Начинаем загрузку
print("Начинаю загрузку данных...")
print("Прогресс обновляется каждые 100k строк.\n")

rows_processed = 0
rows_inserted = 0
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
            
            # Подготавливаем данные для вставки
            # Определяем колонки для вставки
            base_columns = [
                'event_id', 'external_user_id', 'ubidex_id', 'event_type', 'event_date',
                'publisher_id', 'campaign_id', 'sub_id', 'affiliate_id',
                'deposit_amount', 'currency', 'converted_amount', 'converted_currency',
                'website', 'country', 'transaction_id', 'advertiser'
            ]
            
            # Выбираем только существующие колонки
            insert_columns = [col for col in base_columns if col in processed_chunk.columns]
            chunk_data = processed_chunk[insert_columns].copy()
            
            # Используем временную таблицу для эффективного UPSERT
            columns_str = ', '.join(insert_columns)
            
            try:
                # Создаем временную таблицу
                chunk_data.to_sql('temp_user_events_load', conn, if_exists='replace', index=False, method='multi')
                
                # Обновляем существующие записи
                update_columns = [col for col in insert_columns if col != 'event_id']
                update_set = ', '.join([f'{col} = t.{col}' for col in update_columns])
                
                update_sql = f"""
                    UPDATE public.user_events ue
                    SET {update_set}
                    FROM temp_user_events_load t
                    WHERE ue.event_id = t.event_id
                """
                result_update = conn.execute(text(update_sql))
                rows_updated += result_update.rowcount
                
                # Вставляем новые записи (которых еще нет)
                insert_sql = f"""
                    INSERT INTO public.user_events ({columns_str})
                    SELECT {columns_str} FROM temp_user_events_load t
                    WHERE NOT EXISTS (
                        SELECT 1 FROM public.user_events ue WHERE ue.event_id = t.event_id
                    )
                """
                result_insert = conn.execute(text(insert_sql))
                rows_inserted += result_insert.rowcount
                
                # Удаляем временную таблицу
                conn.execute(text("DROP TABLE temp_user_events_load"))
                conn.commit()
                
            except Exception as e:
                # Если ошибка, используем простую вставку
                print(f"   ⚠ Предупреждение при UPSERT: {e}")
                print("   Использую простую вставку...")
                
                # Удаляем временную таблицу если она есть
                try:
                    conn.execute(text("DROP TABLE IF EXISTS temp_user_events_load"))
                except:
                    pass
                
                # Простая вставка (дубликаты будут пропущены)
                chunk_data.to_sql('user_events', conn, if_exists='append', index=False, method='multi')
                conn.commit()
                rows_inserted += len(chunk_data)
            
            rows_processed += len(chunk)
            
            # Прогресс
            if rows_processed % 100000 == 0 or chunk_num == 1:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = rows_processed / elapsed if elapsed > 0 else 0
                remaining = total_rows - rows_processed
                eta = remaining / rate / 60 if rate > 0 else 0
                
                print(f"Прогресс: {rows_processed:,} / {total_rows:,} ({rows_processed/total_rows*100:.1f}%) | "
                      f"Скорость: {rate:.0f} строк/сек | ETA: {eta:.0f} мин | "
                      f"Вставлено: {rows_inserted:,}")

except KeyboardInterrupt:
    print("\n\nЗагрузка прервана пользователем.")
    sys.exit(1)
except Exception as e:
    print(f"\n\nОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

elapsed_total = (datetime.now() - start_time).total_seconds()
print("\n" + "=" * 80)
print("ЗАГРУЗКА ЗАВЕРШЕНА!")
print("=" * 80)
print(f"Обработано строк: {rows_processed:,}")
print(f"Вставлено/обновлено записей: {rows_inserted:,}")
print(f"Время: {elapsed_total/60:.1f} минут")
print(f"Средняя скорость: {rows_processed/elapsed_total:.0f} строк/сек")
print()

# Финальная проверка
print("Проверка данных в БД...")
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM public.user_events WHERE event_date >= '2025-12-02'"))
    count_after_dec2 = result.fetchone()[0]
    
    result = conn.execute(text("SELECT COUNT(*) FROM public.user_events WHERE advertiser IS NOT NULL"))
    count_with_advertiser = result.fetchone()[0]
    
    result = conn.execute(text("SELECT advertiser, COUNT(*) FROM public.user_events WHERE advertiser IS NOT NULL GROUP BY advertiser"))
    advertiser_dist = result.fetchall()
    
    print(f"Записей с 2 декабря: {count_after_dec2:,}")
    print(f"Записей с advertiser: {count_with_advertiser:,}")
    print("Распределение по advertiser:")
    for row in advertiser_dist:
        print(f"  {row[0]}: {row[1]:,}")

print()
print("=" * 80)
print("ГОТОВО!")
print("=" * 80)

