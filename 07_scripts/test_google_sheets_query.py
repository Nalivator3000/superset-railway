#!/usr/bin/env python3
"""Проверка SQL запроса для Google Sheets"""
import sys
import io
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("Проверка SQL запроса...")
print()

pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

# Читаем упрощенный запрос
with open('superset_queries/google_sheets_campaigns_simple.sql', 'r', encoding='utf-8') as f:
    query = f.read()

# Удаляем комментарии для выполнения
query_lines = []
for line in query.split('\n'):
    if not line.strip().startswith('--'):
        query_lines.append(line)
query_clean = '\n'.join(query_lines)

try:
    with engine.connect() as conn:
        result = conn.execute(text(query_clean))
        rows = result.fetchall()
        
        print(f"✓ Запрос выполнен успешно!")
        print(f"Найдено строк: {len(rows):,}")
        print()
        
        if rows:
            print("Примеры данных (первые 5 строк):")
            print("-" * 100)
            for i, row in enumerate(rows[:5], 1):
                print(f"{i}. Дата: {row[0]}, Атрибуция: {row[1]}, Формат: {row[2]}, Кампания: {row[3][:30] if row[3] else 'N/A'}...")
                print(f"   Spend: {row[7]}, Clicks: {row[5]}, Views: {row[6]}, CPC: {row[10]}")
                print()
            
            # Статистика
            print("Статистика:")
            total_spend = sum(row[7] or 0 for row in rows)
            total_clicks = sum(row[5] or 0 for row in rows)
            total_views = sum(row[6] or 0 for row in rows)
            print(f"  Общий Spend: {total_spend:,.2f}")
            print(f"  Общие Clicks: {total_clicks:,}")
            print(f"  Общие Views: {total_views:,}")
            
except Exception as e:
    print(f"✗ Ошибка при выполнении запроса: {e}")
    import traceback
    traceback.print_exc()

