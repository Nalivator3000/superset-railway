#!/usr/bin/env python3
"""
Загрузка данных из Google Sheets в PostgreSQL
Поддерживает несколько таблиц с двумя листами (1 час и 24 часа атрибуции)
"""
import sys
import io
import os
import argparse
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("ЗАГРУЗКА ДАННЫХ ИЗ GOOGLE SHEETS В POSTGRESQL")
print("=" * 80)
print()

# Проверяем наличие библиотек для работы с Google Sheets
try:
    import gspread
    from google.oauth2.service_account import Credentials
    HAS_GSPREAD = True
except ImportError:
    HAS_GSPREAD = False
    print("⚠ Библиотека gspread не установлена.")
    print("   Установите: pip install gspread google-auth")
    print()
    print("   Альтернатива: используйте публичные CSV ссылки из Google Sheets")
    print("   Формат: https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}")
    print()

def load_from_public_csv(sheet_url, sheet_name=None, sheet_gid=None):
    """
    Загрузка данных из публичного Google Sheet через CSV export
    sheet_url: полная ссылка на Google Sheet или только ID
    sheet_name: название листа (для информации, не используется в CSV export)
    sheet_gid: ID листа (gid) - можно найти в URL листа или использовать 0 для первого листа
    """
    # Извлекаем ID таблицы из URL
    if '/spreadsheets/d/' in sheet_url:
        sheet_id = sheet_url.split('/spreadsheets/d/')[1].split('/')[0]
        # Пробуем извлечь gid из URL, если есть
        if '#gid=' in sheet_url:
            sheet_gid = sheet_url.split('#gid=')[1].split('&')[0]
    elif len(sheet_url) == 44:  # Если передан только ID
        sheet_id = sheet_url
    else:
        raise ValueError(f"Неверный формат URL: {sheet_url}")
    
    # Если gid не указан, используем 0 (первый лист)
    if sheet_gid is None:
        sheet_gid = 0
    
    # Загружаем через CSV export с указанием gid
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={sheet_gid}"
    
    try:
        df = pd.read_csv(csv_url)
        return df, sheet_id
    except Exception as e:
        raise Exception(f"Не удалось загрузить данные: {e}. Проверьте, что таблица публичная и gid указан правильно.")

def load_from_gspread(sheet_url, sheet_name, credentials_path):
    """
    Загрузка данных через gspread API (требует credentials)
    """
    if not HAS_GSPREAD:
        raise ImportError("gspread не установлен")
    
    # Загружаем credentials
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
    client = gspread.authorize(creds)
    
    # Открываем таблицу
    if '/spreadsheets/d/' in sheet_url:
        sheet_id = sheet_url.split('/spreadsheets/d/')[1].split('/')[0]
    else:
        sheet_id = sheet_url
    
    spreadsheet = client.open_by_key(sheet_id)
    worksheet = spreadsheet.worksheet(sheet_name)
    
    # Получаем данные
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    
    return df, sheet_id

def normalize_column_names(df):
    """Нормализация названий колонок для PostgreSQL"""
    # Приводим к нижнему регистру, заменяем пробелы на подчеркивания
    df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('-', '_')
    # Удаляем специальные символы
    df.columns = df.columns.str.replace('[^a-z0-9_]', '', regex=True)
    return df

def process_sheet_data(df, sheet_id, sheet_name, attribution_type):
    """Обработка данных из листа с добавлением метаданных"""
    df = df.copy()
    
    # Добавляем метаданные
    df['source_sheet_id'] = sheet_id
    df['sheet_name'] = sheet_name
    df['attribution_type'] = attribution_type  # '1_hour' или '24_hours'
    df['loaded_at'] = datetime.now()
    
    return df

def create_table_if_not_exists(conn):
    """Создание таблицы для хранения данных из Google Sheets"""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS google_sheets_campaigns (
        id SERIAL PRIMARY KEY,
        source_sheet_id TEXT,
        sheet_name TEXT,
        attribution_type TEXT,
        loaded_at TIMESTAMP
    );
    """
    
    conn.execute(text(create_table_sql))
    conn.commit()
    print("✓ Таблица google_sheets_campaigns создана/проверена")

def add_columns_if_needed(conn, df):
    """Добавление недостающих колонок в таблицу на основе данных DataFrame"""
    # Получаем список существующих колонок
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'google_sheets_campaigns'
          AND table_schema = 'public'
    """))
    existing_columns = {row[0] for row in result}
    
    # Колонки, которые всегда есть
    metadata_columns = {'id', 'source_sheet_id', 'sheet_name', 'attribution_type', 'loaded_at'}
    
    # Добавляем недостающие колонки
    for col in df.columns:
        if col not in existing_columns and col not in metadata_columns:
            # Определяем тип колонки на основе данных
            col_type = 'TEXT'  # По умолчанию TEXT
            
            # Пробуем определить тип
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

def load_sheet_to_postgresql(sheet_url, sheet_names, attribution_types, conn, use_gspread=False, credentials_path=None, sheet_gids=None):
    """
    Загрузка данных из Google Sheet в PostgreSQL
    
    sheet_url: URL или ID Google Sheet
    sheet_names: список названий листов ['1 hour', '24 hours'] или ['Sheet1', 'Sheet2']
    attribution_types: список типов атрибуции ['1_hour', '24_hours']
    sheet_gids: список gid листов (опционально, для публичных таблиц)
    """
    all_data = []
    
    for idx, (sheet_name, attr_type) in enumerate(zip(sheet_names, attribution_types)):
        print(f"\nЗагрузка листа: '{sheet_name}' (атрибуция: {attr_type})...")
        
        try:
            if use_gspread and credentials_path:
                df, sheet_id = load_from_gspread(sheet_url, sheet_name, credentials_path)
            else:
                gid = sheet_gids[idx] if sheet_gids and idx < len(sheet_gids) else None
                df, sheet_id = load_from_public_csv(sheet_url, sheet_name, gid)
            
            print(f"  Загружено строк: {len(df)}")
            print(f"  Колонки: {', '.join(df.columns[:5].tolist())}...")
            
            # Нормализуем названия колонок
            df = normalize_column_names(df)
            
            # Добавляем метаданные
            df = process_sheet_data(df, sheet_id, sheet_name, attr_type)
            
            all_data.append(df)
            
        except Exception as e:
            print(f"  ⚠ Ошибка при загрузке листа '{sheet_name}': {e}")
            continue
    
    if not all_data:
        print("\n⚠ Не удалось загрузить данные ни из одного листа")
        return
    
    # Объединяем все данные
    print("\nОбъединение данных...")
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"  Всего строк: {len(combined_df)}")
    print(f"  Всего колонок: {len(combined_df.columns)}")
    
    # Добавляем недостающие колонки в таблицу
    print("\nПроверка структуры таблицы...")
    add_columns_if_needed(conn, combined_df)
    
    # Загружаем в PostgreSQL
    print("\nЗагрузка в PostgreSQL...")
    try:
        # Используем метод 'append' для добавления данных
        combined_df.to_sql('google_sheets_campaigns', conn, if_exists='append', index=False, method='multi')
        conn.commit()
        print(f"  ✓ Загружено {len(combined_df)} строк")
    except Exception as e:
        print(f"  ⚠ Ошибка при загрузке в БД: {e}")
        # Если ошибка из-за структуры таблицы, пробуем добавить колонки и загрузить снова
        if 'column' in str(e).lower() or 'does not exist' in str(e).lower():
            print("  Добавляю недостающие колонки...")
            add_columns_if_needed(conn, combined_df)
            # Загружаем снова
            combined_df.to_sql('google_sheets_campaigns', conn, if_exists='append', index=False, method='multi')
            conn.commit()
            print(f"  ✓ Загружено {len(combined_df)} строк")

def main():
    parser = argparse.ArgumentParser(description='Load data from Google Sheets to PostgreSQL')
    parser.add_argument('--sheets', required=True, nargs='+', 
                       help='URLs или IDs Google Sheets (можно несколько)')
    parser.add_argument('--sheet-names', nargs='+', default=['1 hour', '24 hours'],
                       help='Названия листов (по умолчанию: "1 hour" "24 hours")')
    parser.add_argument('--attribution-types', nargs='+', default=['1_hour', '24_hours'],
                       help='Типы атрибуции (по умолчанию: "1_hour" "24_hours")')
    parser.add_argument('--sheet-gids', nargs='+', type=int,
                       help='GID листов для публичных таблиц (опционально, например: 0 123456789)')
    parser.add_argument('--use-gspread', action='store_true',
                       help='Использовать gspread API (требует credentials)')
    parser.add_argument('--credentials', 
                       help='Путь к файлу credentials.json для Google API')
    
    args = parser.parse_args()
    
    if len(args.sheet_names) != len(args.attribution_types):
        print("⚠ ОШИБКА: Количество названий листов должно совпадать с количеством типов атрибуции")
        sys.exit(1)
    
    # Подключение к PostgreSQL
    print("Подключение к PostgreSQL...")
    pg_uri = get_postgres_connection_string()
    engine = create_engine(pg_uri)
    
    with engine.connect() as conn:
        # Создаем таблицу
        create_table_if_not_exists(conn)
        
        # Загружаем данные из каждой таблицы
        for sheet_url in args.sheets:
            print(f"\n{'='*80}")
            print(f"Обработка таблицы: {sheet_url}")
            print('='*80)
            
            load_sheet_to_postgresql(
                sheet_url,
                args.sheet_names,
                args.attribution_types,
                conn,
                use_gspread=args.use_gspread,
                credentials_path=args.credentials,
                sheet_gids=args.sheet_gids
            )
    
    print("\n" + "=" * 80)
    print("ГОТОВО!")
    print("=" * 80)
    print()
    print("Данные загружены в таблицу: google_sheets_campaigns")
    print("Теперь можно создать Dataset в Superset на основе этой таблицы")

if __name__ == "__main__":
    main()

