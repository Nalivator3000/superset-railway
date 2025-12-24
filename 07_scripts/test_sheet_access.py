#!/usr/bin/env python3
"""Проверка доступа к таблице"""
import pandas as pd
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SHEET_ID = "1lLjbunQujlZ4yaKDakb_XPXLzGy_BZe-LjPi5P3o1fw"

print("Проверка доступа к таблице...")
print(f"Sheet ID: {SHEET_ID}")
print()

# Пробуем разные gid
for gid in [0, 1, 2, 3, 4, 5]:
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
        df = pd.read_csv(url)
        if len(df) > 0:
            print(f"gid={gid}: {len(df)} строк, колонки: {list(df.columns[:5])}")
            # Проверяем даты
            date_cols = [c for c in df.columns if 'date' in str(c).lower()]
            if date_cols:
                try:
                    df[date_cols[0]] = pd.to_datetime(df[date_cols[0]], errors='coerce')
                    print(f"  Даты: {df[date_cols[0]].min()} - {df[date_cols[0]].max()}")
                except:
                    pass
            print()
    except Exception as e:
        print(f"gid={gid}: ошибка - {e}")
        print()

