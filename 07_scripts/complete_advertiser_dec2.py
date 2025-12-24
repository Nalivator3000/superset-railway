#!/usr/bin/env python3
"""
Полное обновление advertiser для всех записей с 2 декабря:
1. Обновление из CSV файла (если есть)
2. Определение по WEBSITE (домену)
3. По умолчанию: 4rabet
"""
import sys
import io
import os
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("ПОЛНОЕ ОБНОВЛЕНИЕ ADVERTISER ДЛЯ ЗАПИСЕЙ С 2 ДЕКАБРЯ")
print("=" * 80)
print()

# Connect to PostgreSQL
print("Подключение к PostgreSQL...")
pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

with engine.connect() as conn:
    # Проверяем текущий статус
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN advertiser = '4rabet' THEN 1 END) as fourrabet,
            COUNT(CASE WHEN advertiser = 'Crorebet' THEN 1 END) as crorebet,
            COUNT(CASE WHEN advertiser IS NULL THEN 1 END) as null_advertiser
        FROM user_events
        WHERE event_date >= '2025-12-02'::date
    """))
    stats = result.fetchone()
    print(f"Записи с 2 декабря:")
    print(f"  Всего: {stats[0]:,}")
    print(f"  4rabet: {stats[1]:,}")
    print(f"  Crorebet: {stats[2]:,}")
    print(f"  Без advertiser: {stats[3]:,}")
    print()
    
    if stats[3] == 0:
        print("✓ Все записи уже имеют advertiser!")
        sys.exit(0)
    
    # Шаг 1: Обновляем по WEBSITE (домену)
    print("Шаг 1: Обновление по WEBSITE (домену)...")
    update_by_website_sql = """
        UPDATE public.user_events
        SET advertiser = CASE
            WHEN website ILIKE '%crorebet%' OR website ILIKE '%crore%' THEN 'Crorebet'
            WHEN website ILIKE '%4rabet%' OR website ILIKE '%4ra%' THEN '4rabet'
            ELSE NULL  -- Оставим NULL для дальнейшей обработки
        END
        WHERE event_date >= '2025-12-02'::date
          AND advertiser IS NULL
          AND website IS NOT NULL
    """
    
    result = conn.execute(text(update_by_website_sql))
    rows_updated_website = result.rowcount
    conn.commit()
    print(f"  Обновлено по WEBSITE: {rows_updated_website:,} записей")
    print()
    
    # Шаг 2: Устанавливаем 4rabet по умолчанию для всех оставшихся
    print("Шаг 2: Установка 4rabet по умолчанию для оставшихся записей...")
    update_default_sql = """
        UPDATE public.user_events
        SET advertiser = '4rabet'
        WHERE event_date >= '2025-12-02'::date
          AND advertiser IS NULL
    """
    
    result = conn.execute(text(update_default_sql))
    rows_updated_default = result.rowcount
    conn.commit()
    print(f"  Установлено 4rabet по умолчанию: {rows_updated_default:,} записей")
    print()
    
    # Финальная проверка
    print("Финальная проверка...")
    result = conn.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN advertiser = '4rabet' THEN 1 END) as fourrabet,
            COUNT(CASE WHEN advertiser = 'Crorebet' THEN 1 END) as crorebet,
            COUNT(CASE WHEN advertiser IS NULL THEN 1 END) as null_advertiser
        FROM user_events
        WHERE event_date >= '2025-12-02'::date
    """))
    final_stats = result.fetchone()
    print(f"Записи с 2 декабря (после обновления):")
    print(f"  Всего: {final_stats[0]:,}")
    print(f"  4rabet: {final_stats[1]:,} ({final_stats[1]/final_stats[0]*100:.1f}%)")
    print(f"  Crorebet: {final_stats[2]:,} ({final_stats[2]/final_stats[0]*100:.1f}%)")
    print(f"  Без advertiser: {final_stats[3]:,} ({final_stats[3]/final_stats[0]*100:.1f}%)")
    print()
    
    if final_stats[3] == 0:
        print("✓ Все записи с 2 декабря теперь имеют advertiser!")
    else:
        print(f"⚠ Осталось {final_stats[3]:,} записей без advertiser")

print()
print("=" * 80)
print("ГОТОВО!")
print("=" * 80)

