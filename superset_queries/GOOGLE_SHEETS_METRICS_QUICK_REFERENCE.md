# Быстрая справка: SQL выражения для метрик

## ⚠️ ВАЖНО: Как копировать SQL выражения

1. **Копируйте ТОЛЬКО содержимое** между строками (без блоков кода ```sql)
2. **НЕ добавляйте** `AS`, запятые, или другие конструкции
3. **Вставляйте** выражение точно как указано ниже

## Простые метрики (SUM)

### Total Spend
```
SUM(total_spend)
```

### Total Clicks
```
SUM(total_clicks)
```

### Total Views
```
SUM(total_views)
```

### Total PostView
```
SUM(total_postview)
```

### Total PostClick
```
SUM(total_postclick)
```

## Вычисляемые метрики (Custom SQL)

### CPC (Cost Per Click)
```
SUM(total_spend) / NULLIF(SUM(total_clicks), 0)
```

### CPM (Cost Per Mille)
```
SUM(total_spend) / NULLIF(SUM(total_views), 0) * 1000
```

### CTR (Click Through Rate)
```
SUM(total_views) / NULLIF(SUM(total_clicks), 0)
```

### CPA PostView
```
SUM(total_spend) / NULLIF(SUM(total_postview), 0)
```

### CPA PostClick
```
SUM(total_spend) / NULLIF(SUM(total_postclick), 0)
```

## Метрики из исходных данных (AVG)

### Avg CPA PV
```
AVG(avg_cpa_pv)
```

### Avg CPA PC
```
AVG(avg_cpa_pc)
```

## Примеры НЕПРАВИЛЬНОГО использования:

❌ `SUM(total_spend) AS total_spend` - НЕ добавляйте AS!
❌ `SUM(total_spend),` - НЕ добавляйте запятые!
❌ ```sql SUM(total_spend) ``` - НЕ копируйте блоки кода!
❌ `SELECT SUM(total_spend)` - НЕ добавляйте SELECT!

## Примеры ПРАВИЛЬНОГО использования:

✅ `SUM(total_spend)` - только выражение
✅ `SUM(total_spend) / NULLIF(SUM(total_clicks), 0)` - вычисляемое выражение
✅ `AVG(avg_cpa_pv)` - только выражение

## Как использовать:

1. Скопируйте нужное выражение из списка выше
2. В Superset: Edit Dataset → Metrics → + Add item
3. Вставьте скопированное выражение в поле **SQL expression**
4. Заполните **Metric Key** и **Label**
5. Сохраните

