#!/usr/bin/env python3
"""Проверка и создание индексов для ускорения запроса ARPPU"""
import sys
import io
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("Проверка индексов для запроса ARPPU...")
pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

with engine.connect() as conn:
    # Проверяем существующие индексы
    result = conn.execute(text("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'user_events' 
          AND schemaname = 'public'
        ORDER BY indexname
    """))
    print("Существующие индексы на user_events:")
    indexes = result.fetchall()
    if indexes:
        for idx in indexes:
            print(f"  - {idx[0]}")
    else:
        print("  Нет индексов")
    print()
    
    # Рекомендуемые индексы для ускорения запроса ARPPU
    recommended_indexes = [
        ("idx_user_events_type_amount_user", 
         "CREATE INDEX IF NOT EXISTS idx_user_events_type_amount_user ON public.user_events(event_type, converted_amount, external_user_id) WHERE event_type = 'deposit' AND converted_amount > 0 AND external_user_id IS NOT NULL"),
        ("idx_user_events_advertiser_date", 
         "CREATE INDEX IF NOT EXISTS idx_user_events_advertiser_date ON public.user_events(advertiser, event_date) WHERE advertiser IS NOT NULL"),
        ("idx_user_events_publisher_format", 
         "CREATE INDEX IF NOT EXISTS idx_user_events_publisher_format ON public.user_events(publisher_id, event_date) WHERE publisher_id IS NOT NULL AND publisher_id != 0"),
    ]
    
    print("Создание рекомендуемых индексов...")
    for idx_name, idx_sql in recommended_indexes:
        try:
            conn.execute(text(idx_sql))
            conn.commit()
            print(f"  ✓ Создан индекс: {idx_name}")
        except Exception as e:
            print(f"  ⚠ Ошибка при создании {idx_name}: {e}")
    
    print()
    print("Готово! Индексы должны ускорить запрос ARPPU.")

