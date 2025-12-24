#!/usr/bin/env python3
"""
Очистка Superset: удаление всех чартов кроме указанных двух
"""
import sys
import io
import os
from sqlalchemy import create_engine, text
from db_utils import get_postgres_connection_string

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("ОЧИСТКА SUPERSET: УДАЛЕНИЕ НЕИСПОЛЬЗУЕМЫХ ЧАРТОВ")
print("=" * 80)
print()

# Чарты, которые нужно сохранить
KEEP_CHARTS = ["Publishers Ubidex", "Reactivation all"]

# Подключение к БД Superset
print("Поиск БД Superset...")

# Сначала пробуем текущую БД (на Railway может быть та же БД)
base_uri = get_postgres_connection_string()
engine = None

# Пробуем разные варианты имени БД
db_candidates = []
if '/ubidex' in base_uri:
    db_candidates.append(base_uri.replace('/ubidex', '/superset'))
    db_candidates.append(base_uri)  # Может быть та же БД
elif '/railway' in base_uri:
    db_candidates.append(base_uri.replace('/railway', '/superset'))
    db_candidates.append(base_uri)  # Может быть та же БД
else:
    # Пробуем добавить /superset
    if not base_uri.endswith('/'):
        base_uri += '/'
    db_candidates.append(base_uri + 'superset')
    db_candidates.append(base_uri[:-1])  # Текущая БД

# Также пробуем из переменной окружения
if os.environ.get("SUPERSET_DATABASE_URL"):
    db_candidates.insert(0, os.environ.get("SUPERSET_DATABASE_URL"))

for db_url in db_candidates:
    try:
        test_engine = create_engine(db_url)
        with test_engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'slices'
            """))
            if result.fetchone()[0] > 0:
                engine = test_engine
                print(f"✓ Найдена БД Superset: {db_url.split('@')[1] if '@' in db_url else db_url}")
                break
    except Exception as e:
        continue

if not engine:
    print("⚠ Не удалось найти БД Superset автоматически.")
    print()
    print("Укажите строку подключения к БД Superset:")
    print("  export SUPERSET_DATABASE_URL='postgresql://user:pass@host:port/superset'")
    print()
    print("Или запустите скрипт с параметром:")
    print("  python cleanup_superset_charts.py 'postgresql://user:pass@host:port/superset'")
    sys.exit(1)

# Работаем с найденной БД
with engine.connect() as conn:
    # Находим ID чартов, которые нужно сохранить
    print()
    print("Поиск чартов для сохранения...")
    keep_chart_ids = []
    for chart_name in KEEP_CHARTS:
        result = conn.execute(text("""
            SELECT id, slice_name 
            FROM slices 
            WHERE slice_name = :name
        """), {"name": chart_name})
        row = result.fetchone()
        if row:
            keep_chart_ids.append(row[0])
            print(f"  ✓ Найден: '{row[1]}' (ID: {row[0]})")
        else:
            print(f"  ⚠ Не найден: '{chart_name}'")
    
    if not keep_chart_ids:
        print("\n⚠ Не найдено ни одного чарта для сохранения!")
        print("   Проверьте названия чартов в Superset.")
        sys.exit(1)
    
    print()
    
    # Находим все чарты
    result = conn.execute(text("SELECT id, slice_name FROM slices ORDER BY id"))
    all_charts = result.fetchall()
    
    print(f"Всего чартов в системе: {len(all_charts)}")
    print(f"Чартов для сохранения: {len(keep_chart_ids)}")
    print(f"Чартов для удаления: {len(all_charts) - len(keep_chart_ids)}")
    print()
    
    # Показываем список чартов для удаления
    charts_to_delete = [c for c in all_charts if c[0] not in keep_chart_ids]
    if charts_to_delete:
        print("Чарты для удаления:")
        for chart_id, chart_name in charts_to_delete:
            print(f"  - {chart_name} (ID: {chart_id})")
        print()
    
    # Подтверждение
    response = input(f"Удалить {len(charts_to_delete)} чартов? (yes/no): ")
    if response.lower() != 'yes':
        print("Отменено.")
        sys.exit(0)
    
    print()
    print("Удаление чартов...")
    
    # Удаляем чарты (сначала удаляем связи, потом сами чарты)
    deleted_count = 0
    
    for chart_id, chart_name in charts_to_delete:
        try:
            # 1. Удаляем связи с дашбордами
            conn.execute(text("DELETE FROM dashboard_slices WHERE slice_id = :id"), {"id": chart_id})
            
            # 2. Удаляем связанные query (если есть)
            conn.execute(text("""
                DELETE FROM query 
                WHERE id IN (
                    SELECT query_id FROM slices WHERE id = :id AND query_id IS NOT NULL
                )
            """), {"id": chart_id})
            
            # 3. Удаляем сам чарт
            conn.execute(text("DELETE FROM slices WHERE id = :id"), {"id": chart_id})
            conn.commit()
            
            deleted_count += 1
            print(f"  ✓ Удален: {chart_name} (ID: {chart_id})")
            
        except Exception as e:
            print(f"  ⚠ Ошибка при удалении {chart_name} (ID: {chart_id}): {e}")
            conn.rollback()
    
    print()
    print(f"Удалено чартов: {deleted_count}")
    
    # Проверяем дашборды без чартов
    print()
    print("Проверка дашбордов...")
    result = conn.execute(text("""
        SELECT d.id, d.dashboard_title, COUNT(ds.slice_id) as chart_count
        FROM dashboards d
        LEFT JOIN dashboard_slices ds ON d.id = ds.dashboard_id
        GROUP BY d.id, d.dashboard_title
        ORDER BY d.id
    """))
    dashboards = result.fetchall()
    
    print(f"Всего дашбордов: {len(dashboards)}")
    empty_dashboards = [d for d in dashboards if d[2] == 0]
    
    if empty_dashboards:
        print(f"Дашбордов без чартов: {len(empty_dashboards)}")
        print("Пустые дашборды:")
        for dash_id, dash_name, _ in empty_dashboards:
            print(f"  - {dash_name} (ID: {dash_id})")
        
        response = input(f"\nУдалить {len(empty_dashboards)} пустых дашбордов? (yes/no): ")
        if response.lower() == 'yes':
            for dash_id, dash_name, _ in empty_dashboards:
                try:
                    conn.execute(text("DELETE FROM dashboards WHERE id = :id"), {"id": dash_id})
                    conn.commit()
                    print(f"  ✓ Удален дашборд: {dash_name} (ID: {dash_id})")
                except Exception as e:
                    print(f"  ⚠ Ошибка при удалении дашборда {dash_name}: {e}")
                    conn.rollback()
    
    # Проверяем размер БД
    print()
    print("Проверка размера БД...")
    result = conn.execute(text("""
        SELECT 
            pg_size_pretty(pg_database_size(current_database())) as db_size,
            (SELECT COUNT(*) FROM slices) as charts_count,
            (SELECT COUNT(*) FROM dashboards) as dashboards_count
    """))
    stats = result.fetchone()
    print(f"Размер БД: {stats[0]}")
    print(f"Осталось чартов: {stats[1]}")
    print(f"Осталось дашбордов: {stats[2]}")

print()
print("=" * 80)
print("ГОТОВО!")
print("=" * 80)
print()
print("Рекомендации:")
print("1. Перезапустите Superset для очистки кэша")
print("2. Проверьте, что нужные чарты работают корректно")
print("3. При необходимости выполните VACUUM ANALYZE для освобождения места")
