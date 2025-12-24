#!/usr/bin/env python3
"""
Установка advertiser = '4rabet' для всех записей до 2 декабря 2025
"""
import sys
import io
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("УСТАНОВКА ADVERTISER = '4rabet' ДЛЯ ЗАПИСЕЙ ДО 2 ДЕКАБРЯ 2025")
print("=" * 80)
print()

# Connect to PostgreSQL
print("1. Подключение к PostgreSQL...")
pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

with engine.connect() as conn:
    # Check current state
    print("2. Проверка текущего состояния...")
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN advertiser IS NOT NULL THEN 1 END) as with_advertiser,
            COUNT(CASE WHEN advertiser IS NULL THEN 1 END) as without_advertiser,
            COUNT(CASE WHEN event_date < '2025-12-02' AND advertiser IS NULL THEN 1 END) as to_update
        FROM public.user_events
    """))
    stats = result.fetchone()
    print(f"   Всего записей: {stats[0]:,}")
    print(f"   С advertiser: {stats[1]:,}")
    print(f"   Без advertiser: {stats[2]:,}")
    print(f"   К обновлению (до 2.12 без advertiser): {stats[3]:,}")
    print()
    
    # Update records before Dec 2
    print("3. Обновление записей до 2 декабря 2025...")
    result = conn.execute(text("""
        UPDATE public.user_events 
        SET advertiser = '4rabet' 
        WHERE event_date < '2025-12-02' 
          AND advertiser IS NULL
    """))
    conn.commit()
    updated = result.rowcount
    print(f"   ✓ Обновлено записей: {updated:,}")
    print()
    
    # Verify
    print("4. Проверка результата...")
    result = conn.execute(text("""
        SELECT 
            advertiser,
            COUNT(*) as cnt,
            MIN(event_date) as min_date,
            MAX(event_date) as max_date
        FROM public.user_events
        WHERE advertiser IS NOT NULL
        GROUP BY advertiser
        ORDER BY advertiser
    """))
    print("   Распределение по advertiser:")
    for row in result:
        print(f"     {row[0]}: {row[1]:,} записей (с {row[2]} по {row[3]})")
    
    # Check remaining NULLs
    result = conn.execute(text("""
        SELECT COUNT(*) 
        FROM public.user_events 
        WHERE advertiser IS NULL
    """))
    remaining = result.fetchone()[0]
    if remaining > 0:
        print(f"   ⚠ Осталось записей без advertiser: {remaining:,}")
        print("   (Это записи с 2 декабря и позже - нужно загрузить из CSV)")

print()
print("=" * 80)
print("ГОТОВО!")
print("=" * 80)

