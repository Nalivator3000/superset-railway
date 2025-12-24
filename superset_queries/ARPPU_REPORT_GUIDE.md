# Руководство: Отчет по ARPPU (Average Revenue Per Paying User)

## Описание

Отчет показывает средний ARPPU (средняя сумма депозитов в USD на платящего пользователя) с разбивкой по различным атрибутам.

## Файл SQL запроса

`superset_queries/arppu_by_attributes_simple.sql`

## Доступные разбивки

1. **Publisher** - по паблишеру (publisher_id)
2. **Format** - по формату рекламы (POP, PUSH, VIDEO, BANNER, NATIVE, OTHER)
3. **Campaign** - по рекламной кампании (campaign_id)
4. **Site** - по сайту (website)
5. **Region** - по региону (country)
6. **All users** - все пользователи (включая неатрибутированных)

## Разделение по брендам

- **4rabet** - определяется по полю `advertiser` в таблице `user_events`
- **Crorebet** - определяется по полю `advertiser` в таблице `user_events`
- Если `advertiser` NULL, используется fallback по website (4rabet/crorebet)
- Доступно с 2 декабря 2025

### Загрузка данных об Advertiser из CSV

Если в таблице `user_events` еще нет данных в колонке `advertiser`, загрузите их из CSV:

```powershell
cd C:\Users\Nalivator3000\Cursor\ubidex_analysis\ubidex_analysis
$env:DATABASE_URL="postgresql://postgres:...@yamabiko.proxy.rlwy.net:47136/railway"
$env:PYTHONIOENCODING="utf-8"

# Если CSV содержит event_id и Advertiser:
python 07_scripts\load_advertiser_from_csv.py --csv "path/to/file.csv" --link-column event_id --advertiser-column Advertiser

# Если CSV содержит external_user_id, event_date и Advertiser:
python 07_scripts\load_advertiser_from_csv.py --csv "path/to/file.csv" --link-column external_user_id --advertiser-column Advertiser --date-column event_date

# Если CSV содержит ubidex_id и Advertiser:
python 07_scripts\load_advertiser_from_csv.py --csv "path/to/file.csv" --link-column ubidex_id --advertiser-column Advertiser
```

**Важно:** Убедитесь, что CSV файл содержит колонки для связи с `user_events` (event_id, external_user_id или ubidex_id) и колонку с названием advertiser (по умолчанию "Advertiser").

## Создание Dataset в Superset

1. Открой **SQL Lab → SQL Editor**
2. Выбери базу данных **Ubidex Events DB**
3. Скопируй SQL из `arppu_by_attributes_simple.sql`
4. Нажми **Run** для проверки
5. Нажми **Save → Save as dataset**
   - Название: `ARPPU by Attributes`
   - Сохрани

## Создание Chart

1. После сохранения датасета нажми **Explore**
2. Тип визуализации: **Table** (для детальной таблицы) или **Bar Chart** (для графиков)
3. Настройки:
   - **Query mode**: `Raw records` (для таблицы) или `Aggregate` (для графика)
   - **Columns** (для таблицы):
     - `breakdown_type` - тип разбивки
     - `brand` - бренд
     - `breakdown_value` - значение разбивки (паблишер, формат, и т.д.)
     - `paying_users` - количество платящих пользователей
     - `total_deposits` - общее количество депозитов
     - `total_revenue_usd` - общая выручка в USD
     - `arppu_usd` - средний ARPPU в USD
     - `avg_deposits_per_user` - среднее количество депозитов на пользователя
   - **Sort by**: `arppu_usd DESC` (по убыванию ARPPU)
4. Сохрани чарт и добавь на дашборд

## Настройка фильтров на Dashboard

### 1. Фильтр по дате (Time Range)

**Важно:** Так как данные агрегированы по пользователям, для правильной фильтрации по дате лучше использовать фильтр на уровне SQL или параметризованную версию запроса.

**Вариант 1 (рекомендуется):** Используй фильтр на уровне SQL в Chart Builder:
- В Chart Builder → **Filters** → **Add filter**
- **Column**: `min_event_date` или `max_event_date`
- **Operator**: `>=` для начала периода, `<=` для конца периода
- Или используй **Custom SQL filter**: `min_event_date >= '2025-11-01' AND max_event_date <= '2025-11-30'`

**Вариант 2:** Используй Native Filter на дашборде:
- **Type**: `Time range` или `Date`
- **Dataset**: `ARPPU by Attributes`
- **Column**: `min_event_date` (для начала периода) или `max_event_date` (для конца периода)
- **Scoping**: Примени к чарту ARPPU

### 2. Фильтр по бренду (Select)

- **Type**: `Select` / `Dropdown`
- **Dataset**: `ARPPU by Attributes`
- **Column**: `brand`
- **Scoping**: Примени к чарту ARPPU

### 3. Фильтр по типу разбивки (Select)

- **Type**: `Select` / `Dropdown`
- **Dataset**: `ARPPU by Attributes`
- **Column**: `breakdown_type`
- **Scoping**: Примени к чарту ARPPU

### 4. Фильтр по минимальному количеству депозитов (Numeric)

- **Type**: `Numeric` / `Range`
- **Dataset**: `ARPPU by Attributes`
- **Column**: `total_deposits`
- **Operator**: `>=` (больше или равно)
- **Scoping**: Примени к чарту ARPPU

### 5. Фильтр по минимальному ARPPU (Numeric)

- **Type**: `Numeric` / `Range`
- **Dataset**: `ARPPU by Attributes`
- **Column**: `arppu_usd`
- **Operator**: `>=` (больше или равно)
- **Scoping**: Примени к чарту ARPPU

## Примеры использования

### Пример 1: ARPPU по паблишерам за ноябрь 2025 (4rabet)

1. Установи фильтр **Time Range**: `2025-11-01` до `2025-11-30`
2. Установи фильтр **Brand**: `4rabet`
3. Установи фильтр **Breakdown Type**: `Publisher`
4. Установи фильтр **Min Deposits**: `>= 10` (опционально)

### Пример 2: ARPPU по форматам за декабрь 2025 (оба бренда)

1. Установи фильтр **Time Range**: `2025-12-01` до `2025-12-31`
2. Установи фильтр **Breakdown Type**: `Format`
3. Установи фильтр **Min ARPPU**: `>= 50` (опционально)

### Пример 3: Общий ARPPU всех пользователей

1. Установи фильтр **Breakdown Type**: `All users`
2. Установи фильтр **Brand**: выбери нужный бренд или оставь все

## Примечания

- **Format** извлекается из таблицы `publisher_spend` (если есть данные) или из `sub_id`
- **OS и Browser** пока не включены в разбивки, так как эти поля отсутствуют в `user_events`
- Для "All users" учитываются все пользователи, включая неатрибутированных (publisher_id = 0 или NULL)
- Бренд определяется автоматически по полю `website`

