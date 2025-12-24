#!/usr/bin/env python3
"""
Анализ структуры Google Sheets перед загрузкой
Проверяет структуру, дубликаты, пробелы по датам
"""
import sys
import io
import pandas as pd
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("АНАЛИЗ GOOGLE SHEETS")
print("=" * 80)
print()

# Список ссылок на таблицы
SHEET_URLS = [
    "https://docs.google.com/spreadsheets/d/1jynLi9Gl7UqToVRLsNasARRxYF-r-uRwqtgINfFN8UA/edit?usp=sharing",
    "https://docs.google.com/spreadsheets/d/1lLjbunQujlZ4yaKDakb_XPXLzGy_BZe-LjPi5P3o1fw/edit?usp=sharing",
    "https://docs.google.com/spreadsheets/d/1eclCXtEAdzWy0ZWyqrAf9XvMhWS08H_XOQAXVuilFv4/edit?usp=sharing",
    "https://docs.google.com/spreadsheets/d/1X_q6OCONQXjTc256Q5_GqH8qW7E0JsWCacqVdOCTU7U/edit?gid=848261804#gid=848261804",
    "https://docs.google.com/spreadsheets/d/1w9LNpKs8p0Zqr1srhNeSdUI1CY1OqetQiUgqLFCrz-w/edit?usp=sharing",
    "https://docs.google.com/spreadsheets/d/1qwsDRLZCW04MUyEhBYLrUPUIaZlmSoq8mzcto4BmhoY/edit?usp=sharing",
    "https://docs.google.com/spreadsheets/d/1QJdvNtCUCaTpIRhWG-Oo5VnRefZkvGYr_JNJzI90eDU/edit?gid=1754370729#gid=1754370729",
    "https://docs.google.com/spreadsheets/d/1Y5GiZ63QQKsSnLj4sN2U0M3plBI3kfpBf6zHVES1m98/edit?usp=sharing",
    "https://docs.google.com/spreadsheets/d/1QJdvNtCUCaTpIRhWG-Oo5VnRefZkvGYr_JNJzI90eDU/edit?gid=1754370729#gid=1754370729",
    "https://docs.google.com/spreadsheets/d/1X_q6OCONQXjTc256Q5_GqH8qW7E0JsWCacqVdOCTU7U/edit?usp=drivesdk",
    "https://docs.google.com/spreadsheets/d/1vF3mTm3Xe7GZz21CBzjn6XdWuciCSWKSHJmKV5WnnuA/edit?usp=sharing",
    "https://docs.google.com/spreadsheets/d/1d_byAZBRMKkprlOz80MwJIfRNGVRJfXr15c7kIwIBkk/edit?usp=sharing",
    "https://docs.google.com/spreadsheets/d/1d_byAZBRMKkprlOz80MwJIfRNGVRJfXr15c7kIwIBkk/edit?usp=sharing",
    "https://docs.google.com/spreadsheets/d/1X_q6OCONQXjTc256Q5_GqH8qW7E0JsWCacqVdOCTU7U/edit?gid=848261804#gid=848261804",
    "https://docs.google.com/spreadsheets/d/1o6Ht1NF5nQgL0kpBcvQ4i3pYIJ-4TPVq_eC9xKYCQqo/edit?usp=sharing",
    "https://docs.google.com/spreadsheets/d/1QKtnSFTZMHZ26CmzX7yI9gvCuy_PhUKDhqX5bB65P-E/edit?usp=sharing",
    "https://docs.google.com/spreadsheets/d/1SL0zk5E8HRrsvYbVb-mIXIsXFM7j1gb91Uneqq600jc/edit?usp=sharing",
]

def extract_sheet_id(url):
    """Извлечение ID таблицы из URL"""
    if '/spreadsheets/d/' in url:
        return url.split('/spreadsheets/d/')[1].split('/')[0]
    return None

def extract_gid(url):
    """Извлечение GID из URL"""
    if '#gid=' in url:
        return url.split('#gid=')[1].split('&')[0].split('#')[0]
    return None

def load_sheet_public(sheet_id, gid=None):
    """Загрузка публичного листа через CSV export"""
    if gid is None:
        gid = 0
    
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    try:
        df = pd.read_csv(csv_url)
        return df
    except Exception as e:
        return None

def find_sheet_gids(sheet_id):
    """Попытка найти листы с атрибуцией 1 hour и 24 hours"""
    # Пробуем стандартные gid
    common_gids = [0, 1, 2, 3, 4, 5]
    found_sheets = {}
    
    for gid in common_gids:
        try:
            df = load_sheet_public(sheet_id, gid)
            if df is not None and len(df) > 0:
                # Пробуем определить тип атрибуции по названию листа или данным
                # Обычно это видно в заголовке или в названии колонок
                sheet_name = f"Sheet_{gid}"
                
                # Проверяем, есть ли колонки с датами и кампаниями
                cols_lower = [str(c).lower() for c in df.columns]
                if any('date' in c or 'campaign' in c or 'spend' in c for c in cols_lower):
                    found_sheets[gid] = {
                        'name': sheet_name,
                        'rows': len(df),
                        'columns': list(df.columns)
                    }
        except:
            pass
    
    return found_sheets

def analyze_sheet_structure(sheet_id, sheet_url):
    """Анализ структуры одной таблицы"""
    print(f"\nТаблица: {sheet_id}")
    print(f"URL: {sheet_url[:80]}...")
    
    # Извлекаем gid из URL, если есть
    gid_from_url = extract_gid(sheet_url)
    
    # Пробуем загрузить с gid из URL
    if gid_from_url:
        df = load_sheet_public(sheet_id, gid_from_url)
        if df is not None:
            print(f"  ✓ Загружен лист с gid={gid_from_url}")
            print(f"    Строк: {len(df)}")
            print(f"    Колонки: {', '.join(df.columns[:10].tolist())}...")
            
            # Проверяем наличие колонки с датой
            date_cols = [c for c in df.columns if 'date' in str(c).lower()]
            if date_cols:
                print(f"    Колонка с датой: {date_cols[0]}")
                if len(df) > 0:
                    try:
                        df[date_cols[0]] = pd.to_datetime(df[date_cols[0]], errors='coerce')
                        date_range = df[date_cols[0]].dropna()
                        if len(date_range) > 0:
                            print(f"    Диапазон дат: {date_range.min()} - {date_range.max()}")
                    except:
                        pass
            
            return {
                'sheet_id': sheet_id,
                'gid': gid_from_url,
                'df': df,
                'columns': list(df.columns),
                'row_count': len(df)
            }
    
    # Если не получилось, пробуем найти листы
    print("  Поиск листов...")
    found = find_sheet_gids(sheet_id)
    if found:
        print(f"  Найдено листов: {len(found)}")
        for gid, info in found.items():
            print(f"    gid={gid}: {info['rows']} строк, колонок: {len(info['columns'])}")
    
    return None

# Убираем дубликаты из списка URL
unique_sheets = {}
for url in SHEET_URLS:
    sheet_id = extract_sheet_id(url)
    if sheet_id:
        if sheet_id not in unique_sheets:
            unique_sheets[sheet_id] = url
        else:
            print(f"⚠ Дубликат: {sheet_id}")

print(f"\nВсего уникальных таблиц: {len(unique_sheets)}")
print(f"Дубликатов: {len(SHEET_URLS) - len(unique_sheets)}")
print()

# Анализируем каждую таблицу
all_data = []
sheet_info = []

for sheet_id, url in unique_sheets.items():
    info = analyze_sheet_structure(sheet_id, url)
    if info:
        sheet_info.append(info)
        if info['df'] is not None:
            info['df']['source_sheet_id'] = sheet_id
            all_data.append(info['df'])

print("\n" + "=" * 80)
print("СВОДКА")
print("=" * 80)
print(f"Успешно загружено таблиц: {len(sheet_info)}")

if all_data:
    # Объединяем все данные для анализа
    print("\nОбъединение данных для анализа...")
    combined = pd.concat(all_data, ignore_index=True)
    print(f"Всего строк: {len(combined)}")
    print(f"Всего колонок: {len(combined.columns)}")
    
    # Проверяем на дубликаты
    print("\nПроверка на дубликаты...")
    # Ищем колонку с датой
    date_cols = [c for c in combined.columns if 'date' in str(c).lower()]
    if date_cols:
        date_col = date_cols[0]
        # Пробуем найти уникальные комбинации
        id_cols = [c for c in combined.columns if 'id' in str(c).lower() or 'campaign' in str(c).lower()]
        if id_cols and date_col:
            key_cols = [date_col] + id_cols[:2]  # Берем первые 2 ID колонки
            duplicates = combined.duplicated(subset=key_cols, keep=False)
            dup_count = duplicates.sum()
            print(f"  Найдено дубликатов: {dup_count}")
            if dup_count > 0:
                print("  Примеры дубликатов:")
                print(combined[duplicates][key_cols].head(10))
    
    # Проверяем пробелы по датам
    print("\nПроверка пробелов по датам...")
    if date_cols:
        date_col = date_cols[0]
        try:
            combined[date_col] = pd.to_datetime(combined[date_col], errors='coerce')
            date_range = combined[date_col].dropna()
            if len(date_range) > 0:
                print(f"  Диапазон дат: {date_range.min()} - {date_range.max()}")
                # Группируем по датам
                daily_counts = date_range.groupby(date_range.dt.date).size()
                print(f"  Уникальных дат: {len(daily_counts)}")
                print(f"  Минимум записей в день: {daily_counts.min()}")
                print(f"  Максимум записей в день: {daily_counts.max()}")
                print(f"  Среднее записей в день: {daily_counts.mean():.1f}")
                
                # Проверяем на пробелы (дни без данных)
                all_dates = pd.date_range(date_range.min(), date_range.max(), freq='D')
                missing_dates = all_dates[~all_dates.isin(daily_counts.index)]
                if len(missing_dates) > 0:
                    print(f"  ⚠ Пробелы по датам: {len(missing_dates)} дней без данных")
                    print(f"    Примеры: {missing_dates[:10].tolist()}")
                else:
                    print("  ✓ Пробелов по датам не обнаружено")
        except Exception as e:
            print(f"  ⚠ Ошибка при анализе дат: {e}")

print("\n" + "=" * 80)
print("ГОТОВО!")
print("=" * 80)

