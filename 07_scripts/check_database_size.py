#!/usr/bin/env python3
"""Проверка размера таблиц в БД"""
import sys
import io
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("АНАЛИЗ РАЗМЕРА БД")
print("=" * 80)
print()

pg_uri = get_postgres_connection_string()
engine = create_engine(pg_uri)

with engine.connect() as conn:
    # Общий размер БД
    result = conn.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()))"))
    db_size = result.fetchone()[0]
    print(f"Общий размер БД: {db_size}")
    print()
    
    # Размер таблиц
    print("Размер таблиц (топ 10):")
    result = conn.execute(text("""
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
            pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS indexes_size,
            pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        LIMIT 10
    """))
    
    print(f"{'Таблица':<30} {'Общий размер':<15} {'Таблица':<15} {'Индексы':<15}")
    print("-" * 80)
    for row in result:
        print(f"{row[1]:<30} {row[2]:<15} {row[3]:<15} {row[4]:<15}")
    
    print()
    
    # Количество записей в основных таблицах
    print("Количество записей в основных таблицах:")
    tables_to_check = ['user_events', 'publisher_spend', 'slices', 'dashboards', 'query']
    for table in tables_to_check:
        try:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.fetchone()[0]
            print(f"  {table}: {count:,} записей")
        except:
            pass
    
    print()
    
    # Размер метаданных Superset
    print("Размер метаданных Superset:")
    result = conn.execute(text("""
        SELECT 
            pg_size_pretty(SUM(pg_total_relation_size(schemaname||'.'||tablename))) AS total_size
        FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename IN ('slices', 'dashboards', 'query', 'table_columns', 'table_metrics', 'databases', 'tables')
    """))
    superset_size = result.fetchone()[0]
    print(f"  Метаданные Superset: {superset_size}")
    
    # Размер данных приложения
    print()
    print("Размер данных приложения:")
    result = conn.execute(text("""
        SELECT 
            pg_size_pretty(SUM(pg_total_relation_size(schemaname||'.'||tablename))) AS total_size
        FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename IN ('user_events', 'publisher_spend', 'reactivations_materialized')
    """))
    app_data_size = result.fetchone()[0]
    print(f"  Данные приложения: {app_data_size}")

print()
print("=" * 80)

