# Исправление ошибки PostgreSQL в Superset

## Проблема:
```
PostgreSQL Error: invalid input syntax for type numeric: "quotient(sumspendsumPostView)"
```

Эта ошибка возникает, когда Superset пытается автоматически создать метрики из вычисляемых полей.

## Решение:

### 1. Используйте исправленные запросы:
- `google_sheets_campaigns_simple.sql` - упрощенная версия (РЕКОМЕНДУЕТСЯ)
- `google_sheets_campaigns_analysis.sql` - полная версия

### 2. При создании Dataset в Superset:

1. **SQL Lab** → вставьте SQL из `google_sheets_campaigns_simple.sql`
2. **Run** → проверьте, что запрос выполняется без ошибок
3. **Save** → **Save dataset**
4. **ВАЖНО**: После сохранения Dataset, перейдите в **Edit dataset**
5. В разделе **Metrics** удалите все автоматически созданные метрики
6. Создайте метрики вручную:

#### Рекомендуемые метрики:

**Суммы:**
- `total_spend` - тип: `SUM`, колонка: `total_spend`
- `total_clicks` - тип: `SUM`, колонка: `total_clicks`
- `total_views` - тип: `SUM`, колонка: `total_views`
- `total_postview` - тип: `SUM`, колонка: `total_postview`
- `total_postclick` - тип: `SUM`, колонка: `total_postclick`

**Средние:**
- `avg_cpc` - тип: `AVG`, колонка: `cpc`
- `avg_cpm` - тип: `AVG`, колонка: `cpm`
- `avg_ctr` - тип: `AVG`, колонка: `ctr`
- `avg_cpa_pv` - тип: `AVG`, колонка: `cpa_pv`

**Счетчики:**
- `count_records` - тип: `COUNT`, колонка: `records_count`

### 3. При создании Chart:

1. **Explore** → выберите Dataset
2. **Query Mode**: **Aggregate** (НЕ Raw records!)
3. **Group by**: выберите нужные измерения (event_date, format, campaign_name и т.д.)
4. **Metrics**: используйте только созданные вручную метрики
5. **Run** → проверьте результат

### 4. Если ошибка все еще возникает:

1. Убедитесь, что используете **Query Mode: Aggregate**
2. Не используйте вычисляемые поля напрямую как метрики
3. Создайте метрики вручную в настройках Dataset
4. Используйте только простые агрегации (SUM, AVG, COUNT) для числовых полей

### 5. Альтернативный подход (если проблема сохраняется):

Используйте запрос без вычисляемых полей, а метрики создавайте в Superset:

```sql
SELECT 
    DATE(event_date) as event_date,
    attribution_type,
    format,
    campaign_name,
    campaignid,
    event_type,
    
    COUNT(*) as records_count,
    SUM(COALESCE(views, 0)) as total_views,
    SUM(COALESCE(clicks, 0)) as total_clicks,
    SUM(
        CASE 
            WHEN spend IS NULL OR spend = '' OR TRIM(spend) = '' THEN 0
            ELSE CAST(REPLACE(REPLACE(TRIM(spend), ',', '.'), ' ', '') AS NUMERIC)
        END
    ) as total_spend,
    SUM(COALESCE(postview, 0)) as total_postview,
    SUM(COALESCE(postclick, 0)) as total_postclick

FROM google_sheets_campaigns
WHERE event_date IS NOT NULL
  AND campaign_name IS NOT NULL
GROUP BY 
    DATE(event_date),
    attribution_type,
    format,
    campaign_name,
    campaignid,
    event_type
ORDER BY 
    event_date DESC;
```

Затем создайте вычисляемые метрики в Superset:
- **CPC**: `SUM(total_spend) / SUM(total_clicks)`
- **CPM**: `SUM(total_spend) / SUM(total_views) * 1000`
- **CTR**: `SUM(total_views) / SUM(total_clicks)`
- **CPA PV**: `SUM(total_spend) / SUM(total_postview)`

## Проверка запроса:

Перед использованием в Superset, проверьте запрос:

```powershell
python 07_scripts\test_google_sheets_query.py
```

Если запрос выполняется без ошибок, можно использовать в Superset.

