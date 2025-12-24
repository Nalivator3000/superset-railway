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
print("Подключение к PostgreSQL...")
pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

with engine.connect() as conn:
    # Check current state
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
    print(f"   К обновлению (до 2.12.2025): {stats[3]:,}")
    print()
    
    if stats[3] > 0:
        print("Обновляю записи по частям (чтобы избежать проблем с диском)...")
        print("   Это может занять несколько минут...")
        
        # Update in chunks by date ranges
        total_updated = 0
        chunk_days = 7  # Update 7 days at a time
        
        # Get date range
        result = conn.execute(text("""
            SELECT MIN(event_date) as min_date, MAX(event_date) as max_date
            FROM public.user_events
            WHERE event_date < '2025-12-02' AND advertiser IS NULL
        """))
        date_range = result.fetchone()
        
        if date_range[0]:
            from datetime import datetime, timedelta
            current_date = date_range[0]
            end_date = min(date_range[1] or datetime(2025, 12, 2), datetime(2025, 12, 2))
            
            while current_date < end_date:
                chunk_end = min(current_date + timedelta(days=chunk_days), end_date)
                
                try:
                    result = conn.execute(text("""
                        UPDATE public.user_events 
                        SET advertiser = '4rabet' 
                        WHERE event_date >= :start_date 
                          AND event_date < :end_date
                          AND advertiser IS NULL
                    """), {
                        'start_date': current_date,
                        'end_date': chunk_end
                    })
                    conn.commit()
                    chunk_updated = result.rowcount
                    total_updated += chunk_updated
                    print(f"   Обновлено: {total_updated:,}/{stats[3]:,} ({current_date.date()} - {chunk_end.date()})", end='\r')
                except Exception as e:
                    print(f"\n   ⚠ Ошибка при обновлении {current_date.date()}: {e}")
                    print("   Продолжаю...")
                    conn.rollback()
                
                current_date = chunk_end
            
            print()
            print(f"   ✓ Всего обновлено записей: {total_updated:,}")
        else:
            print("   Нет записей для обновления")
    else:
        print("   Нет записей для обновления")
    
    print()
    
    # Verify
    result = conn.execute(text("""
        SELECT advertiser, COUNT(*) as cnt 
        FROM public.user_events 
        WHERE advertiser IS NOT NULL 
        GROUP BY advertiser 
        ORDER BY cnt DESC
    """))
    print("Распределение по advertiser после обновления:")
    for row in result:
        print(f"   {row[0]}: {row[1]:,} записей")

print()
print("=" * 80)
print("ГОТОВО!")
print("=" * 80)

