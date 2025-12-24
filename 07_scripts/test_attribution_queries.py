#!/usr/bin/env python3
"""Проверка запросов для разделения атрибуций"""
import sys
import io
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("Проверка запросов для разделения атрибуций...")
print()

pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

queries = [
    ('1 HOUR', 'google_sheets_campaigns_1hour.sql'),
    ('24 HOURS', 'google_sheets_campaigns_24hours.sql'),
    ('COMPARISON', 'google_sheets_campaigns_comparison.sql'),
]

for name, filename in queries:
    print(f"{'='*80}")
    print(f"Проверка: {name}")
    print('='*80)
    
    with open(f'superset_queries/{filename}', 'r', encoding='utf-8') as f:
        query = f.read()
    
    # Удаляем комментарии
    query_clean = '\n'.join([line for line in query.split('\n') if not line.strip().startswith('--')])
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query_clean))
            rows = result.fetchall()
            
            print(f"✓ Запрос выполнен успешно!")
            print(f"  Найдено строк: {len(rows):,}")
            
            if rows:
                # Проверяем диапазон дат
                dates = [row[0] for row in rows if row[0]]
                if dates:
                    print(f"  Диапазон дат: {min(dates)} - {max(dates)}")
                
                # Проверяем форматы
                formats = set(row[1] for row in rows if row[1])
                print(f"  Уникальных форматов: {len(formats)}")
                print(f"  Форматы: {', '.join(sorted(formats)[:5])}...")
                
                # Статистика по spend
                total_spend = sum(row[6] or 0 for row in rows)
                total_clicks = sum(row[5] or 0 for row in rows)
                total_views = sum(row[4] or 0 for row in rows)
                print(f"  Общий Spend: {total_spend:,.2f}")
                print(f"  Общие Clicks: {total_clicks:,}")
                print(f"  Общие Views: {total_views:,}")
                
                # Для comparison проверяем типы атрибуции
                if 'COMPARISON' in name:
                    attribution_types = set(row[1] for row in rows if len(row) > 1 and row[1])
                    print(f"  Типы атрибуции: {', '.join(sorted(attribution_types))}")
            
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    print()

print("="*80)
print("ГОТОВО!")
print("="*80)

