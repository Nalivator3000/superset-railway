# Настройка метрик для Google Sheets Campaigns в Superset

## Проблема:
Ошибка `invalid input syntax for type numeric: "quotient(sumspendsumPostView)"` возникает, когда Superset пытается автоматически создать метрики из вычисляемых полей в SQL запросе.

## Решение:
Используйте базовый запрос без вычисляемых метрик и создавайте их вручную в Superset.

## Шаг 1: Создание Dataset

1. **SQL Lab** → вставьте SQL из `google_sheets_campaigns_base.sql`
2. **Run** → проверьте выполнение
3. **Save** → **Save dataset** → название: `Google Sheets Campaigns Base`

## Шаг 2: Создание метрик в Superset

1. Откройте созданный Dataset → **Edit dataset**
2. Перейдите в раздел **Metrics**
3. Удалите все автоматически созданные метрики (если есть)
4. Создайте метрики вручную, нажав **+ Add a new metric**

### Метрика 1: Total Spend
- **Metric Name**: `Total Spend`
- **Metric Type**: `Simple`
- **Column**: `total_spend`
- **Aggregation Function**: `SUM`
- **Save**

### Метрика 2: Total Clicks
- **Metric Name**: `Total Clicks`
- **Metric Type**: `Simple`
- **Column**: `total_clicks`
- **Aggregation Function**: `SUM`
- **Save**

### Метрика 3: Total Views
- **Metric Name**: `Total Views`
- **Metric Type**: `Simple`
- **Column**: `total_views`
- **Aggregation Function**: `SUM`
- **Save**

### Метрика 4: Total PostView
- **Metric Name**: `Total PostView`
- **Metric Type**: `Simple`
- **Column**: `total_postview`
- **Aggregation Function**: `SUM`
- **Save**

### Метрика 5: Total PostClick
- **Metric Name**: `Total PostClick`
- **Metric Type**: `Simple`
- **Column**: `total_postclick`
- **Aggregation Function**: `SUM`
- **Save**

### Метрика 6: CPC (Cost Per Click) - **Custom SQL**
- **Metric Name**: `CPC`
- **Metric Type**: **Custom SQL**
- **SQL Expression**: 
  ```sql
  SUM(total_spend) / NULLIF(SUM(total_clicks), 0)
  ```
- **Save**

### Метрика 7: CPM (Cost Per Mille) - **Custom SQL**
- **Metric Name**: `CPM`
- **Metric Type**: **Custom SQL**
- **SQL Expression**: 
  ```sql
  SUM(total_spend) / NULLIF(SUM(total_views), 0) * 1000
  ```
- **Save**

### Метрика 8: CTR (Click Through Rate) - **Custom SQL**
- **Metric Name**: `CTR`
- **Metric Type**: **Custom SQL**
- **SQL Expression**: 
  ```sql
  SUM(total_views) / NULLIF(SUM(total_clicks), 0)
  ```
- **Save**

### Метрика 9: CPA PostView - **Custom SQL**
- **Metric Name**: `CPA PostView`
- **Metric Type**: **Custom SQL**
- **SQL Expression**: 
  ```sql
  SUM(total_spend) / NULLIF(SUM(total_postview), 0)
  ```
- **Save**

### Метрика 10: CPA PostClick - **Custom SQL**
- **Metric Name**: `CPA PostClick`
- **Metric Type**: **Custom SQL**
- **SQL Expression**: 
  ```sql
  SUM(total_spend) / NULLIF(SUM(total_postclick), 0)
  ```
- **Save**

### Метрика 11: Avg CPA PV (из исходных данных)
- **Metric Name**: `Avg CPA PV`
- **Metric Type**: `Simple`
- **Column**: `avg_cpa_pv`
- **Aggregation Function**: `AVG`
- **Save**

### Метрика 12: Avg CPA PC (из исходных данных)
- **Metric Name**: `Avg CPA PC`
- **Metric Type**: `Simple`
- **Column**: `avg_cpa_pc`
- **Aggregation Function**: `AVG`
- **Save**

## Шаг 3: Создание Chart

1. **Explore** → выберите Dataset `Google Sheets Campaigns Base`
2. **Query Mode**: **Aggregate**
3. **Group by**: выберите нужные измерения:
   - `event_date` (для трендов)
   - `format` (для сравнения форматов)
   - `campaign_name` (для сравнения кампаний)
   - `attribution_type` (1_hour / 24_hours)
4. **Metrics**: используйте созданные метрики:
   - `Total Spend`
   - `Total Clicks`
   - `Total Views`
   - `CPC`
   - `CPM`
   - `CTR`
   - `CPA PostView`
5. **Run** → проверьте результат
6. **Save** → **Save chart**

## Шаг 4: Добавление фильтров на Dashboard

1. Откройте Dashboard → **Edit Dashboard** → **+ Filter**

### Фильтр 1: Диапазон дат
- **Filter Type**: Time Range
- **Dataset**: `Google Sheets Campaigns Base`
- **Column**: `event_date`
- **Scoping**: Apply to specific charts → отметьте ваш Chart

### Фильтр 2: Тип атрибуции
- **Filter Type**: Select
- **Dataset**: `Google Sheets Campaigns Base`
- **Column**: `attribution_type`
- **Scoping**: Apply to specific charts → отметьте ваш Chart

### Фильтр 3: Формат
- **Filter Type**: Select
- **Dataset**: `Google Sheets Campaigns Base`
- **Column**: `format`
- **Scoping**: Apply to specific charts → отметьте ваш Chart

## Альтернативный способ (если Custom SQL не работает):

Если Custom SQL метрики не работают, используйте простые метрики и создавайте вычисляемые колонки в Chart:

1. В Chart Builder → **Customize** → **Custom SQL**
2. Добавьте вычисляемые колонки:
   ```sql
   CASE 
       WHEN SUM(total_clicks) > 0 
       THEN SUM(total_spend) / SUM(total_clicks)
       ELSE NULL
   END as cpc
   ```

Но лучше использовать метрики через Custom SQL, как описано выше.

## Проверка:

После создания всех метрик, проверьте Dataset:
- Все метрики должны отображаться в списке
- Custom SQL метрики должны иметь тип "Custom SQL"
- При создании Chart все метрики должны быть доступны для выбора

