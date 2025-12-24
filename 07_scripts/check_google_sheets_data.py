#!/usr/bin/env python3
"""
Проверка загруженных данных из Google Sheets
Анализ структуры, пробелов по датам, дубликатов
"""
import sys
import io
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("ПРОВЕРКА ЗАГРУЖЕННЫХ ДАННЫХ ИЗ GOOGLE SHEETS")
print("=" * 80)
print()

pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

with engine.connect() as conn:
    # Общая статистика
    print("1. ОБЩАЯ СТАТИСТИКА:")
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
    print(f"   Всего строк: {stats[0]:,}")
    print(f"   Уникальных таблиц: {stats[1]}")
    print(f"   Типов атрибуции: {stats[2]}")
    print()
    
    # Статистика по таблицам
    print("2. СТАТИСТИКА ПО ТАБЛИЦАМ:")
    result = conn.execute(text("""
        SELECT 
            source_sheet_id,
            attribution_type,
            COUNT(*) as rows,
            MIN(event_date) as min_date,
            MAX(event_date) as max_date
        FROM google_sheets_campaigns
        WHERE event_date IS NOT NULL
        GROUP BY source_sheet_id, attribution_type
        ORDER BY source_sheet_id, attribution_type
    """))
    print("   Таблица | Тип атрибуции | Строк | Диапазон дат")
    print("   " + "-" * 70)
    for row in result:
        sheet_id = row[0][:20] + "..." if len(row[0]) > 20 else row[0]
        print(f"   {sheet_id} | {row[1]:12} | {row[2]:5} | {row[3]} - {row[4]}")
    print()
    
    # Проверка пробелов по датам
    print("3. ПРОВЕРКА ПРОБЕЛОВ ПО ДАТАМ:")
    result = conn.execute(text("""
        SELECT 
            DATE(event_date) as date,
            COUNT(*) as records,
            COUNT(DISTINCT source_sheet_id) as sheets,
            COUNT(DISTINCT attribution_type) as attr_types
        FROM google_sheets_campaigns
        WHERE event_date IS NOT NULL
        GROUP BY DATE(event_date)
        ORDER BY date
    """))
    daily_stats = result.fetchall()
    
    if daily_stats:
        dates = [row[0] for row in daily_stats]
        print(f"   Диапазон дат: {min(dates)} - {max(dates)}")
        print(f"   Уникальных дат: {len(dates)}")
        
        # Проверяем на пробелы
        from datetime import timedelta
        current_date = min(dates)
        end_date = max(dates)
        missing_dates = []
        
        while current_date <= end_date:
            if current_date not in dates:
                missing_dates.append(current_date)
            current_date += timedelta(days=1)
        
        if missing_dates:
            print(f"   ⚠ Пробелы по датам: {len(missing_dates)} дней")
            print(f"     Первые 10: {missing_dates[:10]}")
        else:
            print("   ✓ Пробелов по датам не обнаружено")
    print()
    
    # Проверка дубликатов
    print("4. ПРОВЕРКА ДУБЛИКАТОВ:")
    result = conn.execute(text("""
        SELECT 
            source_sheet_id,
            attribution_type,
            event_date,
            campaignid,
            COUNT(*) as cnt
        FROM google_sheets_campaigns
        WHERE event_date IS NOT NULL AND campaignid IS NOT NULL
        GROUP BY source_sheet_id, attribution_type, event_date, campaignid
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
        LIMIT 10
    """))
    duplicates = result.fetchall()
    if duplicates:
        print(f"   ⚠ Найдено {len(duplicates)} групп дубликатов")
        print("   Примеры:")
        for row in duplicates[:5]:
            print(f"     {row[0][:20]}... | {row[1]} | {row[2]} | campaignID={row[3]} | {row[4]} раз")
    else:
        print("   ✓ Дубликатов не обнаружено")
    print()
    
    # Структура данных
    print("5. СТРУКТУРА ДАННЫХ:")
    result = conn.execute(text("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'google_sheets_campaigns'
          AND table_schema = 'public'
        ORDER BY ordinal_position
    """))
    print("   Колонка | Тип")
    print("   " + "-" * 50)
    for row in result:
        print(f"   {row[0]:30} | {row[1]}")
    print()
    
    # Примеры данных
    print("6. ПРИМЕРЫ ДАННЫХ:")
    result = conn.execute(text("""
        SELECT 
            source_sheet_id,
            attribution_type,
            event_date,
            campaign_name,
            format,
            spend,
            clicks,
            views
        FROM google_sheets_campaigns
        WHERE event_date IS NOT NULL
        LIMIT 5
    """))
    print("   Таблица | Атрибуция | Дата | Кампания | Формат | Spend | Clicks | Views")
    print("   " + "-" * 90)
    for row in result:
        sheet_id = row[0][:10] + "..." if len(row[0]) > 10 else row[0]
        campaign = row[3][:20] + "..." if row[3] and len(str(row[3])) > 20 else (row[3] or "N/A")
        print(f"   {sheet_id} | {row[1]:10} | {row[2]} | {campaign} | {row[4] or 'N/A':6} | {row[5] or 'N/A':5} | {row[6] or 'N/A':6} | {row[7] or 'N/A':5}")

print("\n" + "=" * 80)
print("ГОТОВО!")
print("=" * 80)

