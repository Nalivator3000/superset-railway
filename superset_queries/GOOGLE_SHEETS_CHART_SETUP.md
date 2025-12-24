# Настройка Chart для анализа данных из Google Sheets

## Файлы SQL запросов:

1. **`google_sheets_campaigns_analysis.sql`** - Полный отчет со всеми метриками
2. **`google_sheets_campaigns_simple.sql`** - Упрощенная версия для быстрого анализа

## Шаг 1: Создание Dataset

1. Откройте **Superset** → **SQL Lab**
2. Скопируйте SQL из файла `google_sheets_campaigns_simple.sql` (или `google_sheets_campaigns_analysis.sql`)
3. Вставьте SQL в редактор
4. Нажмите **Run** для проверки запроса
5. Если запрос выполнился успешно, нажмите **Save** → **Save dataset**
6. Введите название: `Google Sheets Campaigns Analysis`
7. Выберите **Database**: ваша БД (Ubidex Events DB)
8. Нажмите **Save**

## Шаг 2: Создание Chart

1. После сохранения Dataset нажмите **Explore** (или создайте Chart через **Charts** → **+ Chart**)
2. Выберите **Dataset**: `Google Sheets Campaigns Analysis`
3. Выберите **Visualization Type**: 
   - **Table** - для табличного отчета
   - **Bar Chart** - для сравнения по форматам/кампаниям
   - **Line Chart** - для трендов по датам
   - **Pivot Table** - для сводной таблицы

### Настройки Chart Builder:

#### Для Table:
- **Query Mode**: Aggregate
- **Group by**: 
  - `event_date` (дата)
  - `campaign_name` (название кампании)
  - `format` (формат рекламы)
  - `attribution_type` (1_hour / 24_hours)
- **Metrics**:
  - `SUM(total_spend)` - общие траты
  - `SUM(total_clicks)` - общие клики
  - `SUM(total_views)` - общие показы
  - `AVG(cpc)` - средний CPC
  - `AVG(ctr)` - средний CTR
  - `AVG(cpa_pv)` - средний CPA PostView

#### Для Bar Chart (сравнение по форматам):
- **Query Mode**: Aggregate
- **Group by**: `format`
- **Metrics**: `SUM(total_spend)`, `SUM(total_clicks)`
- **X-axis**: `format`
- **Y-axis**: `SUM(total_spend)`

#### Для Line Chart (тренд по датам):
- **Query Mode**: Aggregate
- **Group by**: `event_date`
- **Metrics**: `SUM(total_spend)`, `SUM(total_clicks)`
- **X-axis**: `event_date`
- **Y-axis**: `SUM(total_spend)`

4. Нажмите **Run** для предпросмотра
5. Нажмите **Save** → **Save chart** → название: `Google Sheets Campaigns - Overview`

## Шаг 3: Создание Dashboard

1. При сохранении Chart выберите **"+ Add to new dashboard"** или создайте отдельно:
   - **Dashboards** → **+ Dashboard** → название: `Google Sheets Campaigns`

## Шаг 4: Добавление фильтров на Dashboard

1. Откройте созданный Dashboard → **Edit Dashboard** → **+ Filter**

### Фильтр 1: Диапазон дат
- **Filter Type**: Time Range
- **Dataset**: `Google Sheets Campaigns Analysis`
- **Column**: `event_date`
- **Scoping**: **Apply to specific charts** → отметьте ваш Chart
- **Save**

### Фильтр 2: Тип атрибуции
- **Filter Type**: Select
- **Dataset**: `Google Sheets Campaigns Analysis`
- **Column**: `attribution_type`
- **Default Value**: `All` (или выберите `1_hour` / `24_hours`)
- **Scoping**: **Apply to specific charts** → отметьте ваш Chart
- **Save**

### Фильтр 3: Формат рекламы
- **Filter Type**: Select
- **Dataset**: `Google Sheets Campaigns Analysis`
- **Column**: `format`
- **Default Value**: `All`
- **Scoping**: **Apply to specific charts** → отметьте ваш Chart
- **Save**

### Фильтр 4: Название кампании
- **Filter Type**: Select (или Text)
- **Dataset**: `Google Sheets Campaigns Analysis`
- **Column**: `campaign_name`
- **Default Value**: `All`
- **Scoping**: **Apply to specific charts** → отметьте ваш Chart
- **Save**

### Фильтр 5: Минимальный Spend (опционально)
- **Filter Type**: Numeric
- **Dataset**: `Google Sheets Campaigns Analysis`
- **Column**: `total_spend`
- **Operator**: `>=`
- **Default Value**: `0`
- **Scoping**: **Apply to specific charts** → отметьте ваш Chart
- **Save**

## Шаг 5: Настройка визуализации

1. В режиме редактирования Dashboard:
   - Перетащите Chart для изменения размера
   - Настройте ширину (можно растянуть на весь экран)
   - Сохраните изменения

## Примеры использования:

### 1. Сравнение эффективности форматов
- **Chart Type**: Bar Chart
- **Group by**: `format`
- **Metrics**: `SUM(total_spend)`, `SUM(total_clicks)`
- **Filters**: выберите период и тип атрибуции

### 2. Тренд трат по датам
- **Chart Type**: Line Chart
- **Group by**: `event_date`
- **Metrics**: `SUM(total_spend)`
- **Filters**: выберите формат и кампанию

### 3. Топ кампаний по тратам
- **Chart Type**: Table
- **Group by**: `campaign_name`
- **Metrics**: `SUM(total_spend)`, `SUM(total_clicks)`, `AVG(cpc)`
- **Sort by**: `SUM(total_spend)` DESC
- **Row Limit**: 20

### 4. Сравнение атрибуций (1 hour vs 24 hours)
- **Chart Type**: Bar Chart
- **Group by**: `attribution_type`
- **Metrics**: `SUM(total_spend)`, `SUM(total_clicks)`
- **Filters**: выберите период и формат

## Полезные метрики:

- **total_spend** - общие траты
- **total_clicks** - общие клики
- **total_views** - общие показы
- **cpc** - Cost Per Click (траты / клики)
- **cpm** - Cost Per Mille (траты на 1000 показов)
- **ctr** - Click Through Rate (показы / клики)
- **cpa_pv** - CPA PostView (траты / PostView конверсии)
- **cpa_pc** - CPA PostClick (траты / PostClick конверсии)

## Примечания:

- Данные загружаются из таблицы `google_sheets_campaigns`
- Поля `spend`, `cpa_pv`, `cpa_pc` очищаются от запятых и конвертируются в NUMERIC
- Значения "inf" в CPA полях обрабатываются как NULL
- Фильтрация по датам выполняется через Dashboard фильтры

