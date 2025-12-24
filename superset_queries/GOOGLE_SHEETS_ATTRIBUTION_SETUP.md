# Настройка запросов для разделения атрибуций 1 HOUR и 24 HOURS

## Доступные запросы:

1. **`google_sheets_campaigns_1hour.sql`** - ТОЛЬКО данные с атрибуцией 1 час
2. **`google_sheets_campaigns_24hours.sql`** - ТОЛЬКО данные с атрибуцией 24 часа
3. **`google_sheets_campaigns_comparison.sql`** - Сводная таблица для сравнения обоих типов

## Вариант 1: Отдельные Dataset для каждого типа атрибуции

### Dataset для 1 HOUR:

1. **SQL Lab** → вставьте SQL из `google_sheets_campaigns_1hour.sql`
2. **Run** → проверьте выполнение
3. **Save** → **Save dataset** → название: `Google Sheets Campaigns - 1 Hour`
4. Создайте метрики (см. `GOOGLE_SHEETS_METRICS_SETUP.md`)

### Dataset для 24 HOURS:

1. **SQL Lab** → вставьте SQL из `google_sheets_campaigns_24hours.sql`
2. **Run** → проверьте выполнение
3. **Save** → **Save dataset** → название: `Google Sheets Campaigns - 24 Hours`
4. Создайте метрики (см. `GOOGLE_SHEETS_METRICS_SETUP.md`)

### Создание Chart для каждого типа:

**Chart для 1 HOUR:**
- **Explore** → выберите Dataset `Google Sheets Campaigns - 1 Hour`
- **Query Mode**: Aggregate
- **Group by**: `event_date`, `format`, `campaign_name`
- **Metrics**: `Total Spend`, `Total Clicks`, `CPC`, `CTR`
- **Save** → название: `Campaigns 1 Hour`

**Chart для 24 HOURS:**
- **Explore** → выберите Dataset `Google Sheets Campaigns - 24 Hours`
- **Query Mode**: Aggregate
- **Group by**: `event_date`, `format`, `campaign_name`
- **Metrics**: `Total Spend`, `Total Clicks`, `CPC`, `CTR`
- **Save** → название: `Campaigns 24 Hours`

## Вариант 2: Сводная таблица для сравнения

### Dataset для сравнения:

1. **SQL Lab** → вставьте SQL из `google_sheets_campaigns_comparison.sql`
2. **Run** → проверьте выполнение
3. **Save** → **Save dataset** → название: `Google Sheets Campaigns - Comparison`
4. Создайте метрики (см. `GOOGLE_SHEETS_METRICS_SETUP.md`)

### Создание Chart для сравнения:

1. **Explore** → выберите Dataset `Google Sheets Campaigns - Comparison`
2. **Query Mode**: Aggregate
3. **Group by**: 
   - `event_date` (дата)
   - `format` (формат рекламы)
   - `campaign_name` (название кампании)
   - `attribution_type` (1_hour / 24_hours) - **ВАЖНО для сравнения**
4. **Metrics**: 
   - `Total Spend`
   - `Total Clicks`
   - `Total Views`
   - `CPC`
   - `CTR`
   - `CPA PostView`
5. **Visualization Type**: 
   - **Table** - для детального сравнения
   - **Bar Chart** - для визуального сравнения (X-axis: `attribution_type`, Y-axis: `Total Spend`)
   - **Line Chart** - для трендов по датам (X-axis: `event_date`, Series: `attribution_type`)
6. **Save** → название: `Campaigns Comparison 1h vs 24h`

## Примеры использования:

### Пример 1: Сравнение трат по форматам (1h vs 24h)

**Chart Type**: Bar Chart
- **Group by**: `format`, `attribution_type`
- **Metrics**: `SUM(Total Spend)`
- **X-axis**: `format`
- **Series**: `attribution_type`
- **Y-axis**: `SUM(Total Spend)`

### Пример 2: Тренд CPC по датам (1h vs 24h)

**Chart Type**: Line Chart
- **Group by**: `event_date`, `attribution_type`
- **Metrics**: `AVG(CPC)`
- **X-axis**: `event_date`
- **Series**: `attribution_type`
- **Y-axis**: `AVG(CPC)`

### Пример 3: Сводная таблица по кампаниям

**Chart Type**: Table
- **Group by**: `campaign_name`, `attribution_type`
- **Metrics**: 
  - `SUM(Total Spend)`
  - `SUM(Total Clicks)`
  - `AVG(CPC)`
  - `AVG(CTR)`
  - `AVG(CPA PostView)`
- **Sort by**: `SUM(Total Spend)` DESC

## Фильтры на Dashboard:

1. **Time Range** для `event_date`
2. **Select** для `format` (banner, push, native, teaser)
3. **Select** для `campaign_name`
4. **Select** для `event_type` (ftd, rd)

**Примечание**: Если используете сводную таблицу (`comparison.sql`), фильтр по `attribution_type` не нужен - данные уже разделены по этому полю.

## Рекомендации:

- **Для детального анализа одного типа атрибуции**: используйте отдельные запросы (1hour.sql или 24hours.sql)
- **Для сравнения эффективности**: используйте сводную таблицу (comparison.sql)
- **Для Dashboard**: создайте отдельные Chart для каждого типа атрибуции или используйте сводную таблицу с группировкой по `attribution_type`

