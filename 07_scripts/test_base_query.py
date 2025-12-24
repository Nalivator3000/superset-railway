#!/usr/bin/env python3
"""Проверка базового запроса"""
import sys
import io
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("Проверка базового запроса...")
print()

pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

with open('superset_queries/google_sheets_campaigns_base.sql', 'r', encoding='utf-8') as f:
    query = f.read()

# Удаляем комментарии
query_clean = '\n'.join([line for line in query.split('\n') if not line.strip().startswith('--')])

try:
    with engine.connect() as conn:
        result = conn.execute(text(query_clean))
        rows = result.fetchall()
        
        print(f"✓ Запрос выполнен успешно!")
        print(f"Найдено строк: {len(rows):,}")
        print()
        
        if rows:
            print("Примеры данных (первые 3 строки):")
            print("-" * 100)
            for i, row in enumerate(rows[:3], 1):
                print(f"{i}. Дата: {row[0]}, Атрибуция: {row[1]}, Формат: {row[2]}")
                print(f"   Кампания: {row[3][:40] if row[3] else 'N/A'}...")
                print(f"   Spend: {row[9]:,.2f}, Clicks: {row[8]}, Views: {row[7]}")
                print()
            
            # Статистика
            total_spend = sum(row[9] or 0 for row in rows)
            total_clicks = sum(row[8] or 0 for row in rows)
            total_views = sum(row[7] or 0 for row in rows)
            print("Статистика:")
            print(f"  Общий Spend: {total_spend:,.2f}")
            print(f"  Общие Clicks: {total_clicks:,}")
            print(f"  Общие Views: {total_views:,}")
            if total_clicks > 0:
                print(f"  Средний CPC: {total_spend / total_clicks:.2f}")
            
except Exception as e:
    print(f"✗ Ошибка: {e}")
    import traceback
    traceback.print_exc()

