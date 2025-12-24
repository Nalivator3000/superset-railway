# Настройка загрузки данных из Google Sheets

## Вариант 1: Публичные таблицы (проще, не требует авторизации)

Если ваши Google Sheets имеют публичный доступ, можно загружать данные через CSV export.

### Шаг 1: Подготовка Google Sheets

1. Откройте Google Sheet
2. **File** → **Share** → **Change to anyone with the link**
3. Скопируйте ссылку на таблицу

### Шаг 2: Найти GID листов (опционально, но рекомендуется)

GID (ID листа) можно найти в URL Google Sheet:
- Откройте нужный лист в Google Sheets
- Посмотрите на URL: `https://docs.google.com/spreadsheets/d/SHEET_ID/edit#gid=123456789`
- Число после `#gid=` - это GID листа

**Пример:**
- Лист "1 hour" имеет gid=0
- Лист "24 hours" имеет gid=123456789

### Шаг 3: Загрузка данных

```powershell
cd C:\Users\Nalivator3000\Cursor\ubidex_analysis\ubidex_analysis
$env:DATABASE_URL="postgresql://postgres:...@yamabiko.proxy.rlwy.net:47136/railway"

# Для одной таблицы (без указания gid - загрузит первый лист дважды)
python 07_scripts\load_google_sheets_to_postgresql.py `
  --sheets "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID" `
  --sheet-names "1 hour" "24 hours" `
  --attribution-types "1_hour" "24_hours"

# С указанием gid листов (РЕКОМЕНДУЕТСЯ)
python 07_scripts\load_google_sheets_to_postgresql.py `
  --sheets "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID" `
  --sheet-names "1 hour" "24 hours" `
  --attribution-types "1_hour" "24_hours" `
  --sheet-gids 0 123456789

# Для нескольких таблиц
python 07_scripts\load_google_sheets_to_postgresql.py `
  --sheets "https://docs.google.com/spreadsheets/d/SHEET_ID_1" "https://docs.google.com/spreadsheets/d/SHEET_ID_2" `
  --sheet-names "1 hour" "24 hours" `
  --attribution-types "1_hour" "24_hours" `
  --sheet-gids 0 123456789
```

**Примечание:** 
- Если названия листов отличаются, укажите их: `--sheet-names "Лист1" "Лист2"`
- Если не указать `--sheet-gids`, скрипт попробует загрузить первый лист (gid=0) для всех указанных названий

## Вариант 2: С авторизацией через Google API (для приватных таблиц)

### Шаг 1: Установка зависимостей

```powershell
pip install gspread google-auth
```

### Шаг 2: Создание credentials

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте проект (или выберите существующий)
3. Включите **Google Sheets API** и **Google Drive API**
4. Создайте Service Account:
   - **IAM & Admin** → **Service Accounts** → **Create Service Account**
   - Скачайте JSON ключ
5. Поделитесь Google Sheet с email из Service Account (найди в JSON файле, поле `client_email`)

### Шаг 3: Загрузка данных

```powershell
python 07_scripts\load_google_sheets_to_postgresql.py `
  --sheets "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID" `
  --sheet-names "1 hour" "24 hours" `
  --attribution-types "1_hour" "24_hours" `
  --use-gspread `
  --credentials "path/to/credentials.json"
```

## Структура данных

Данные загружаются в таблицу `google_sheets_campaigns` со следующими колонками:

- **Метаданные:**
  - `source_sheet_id` - ID исходной Google таблицы
  - `sheet_name` - название листа
  - `attribution_type` - тип атрибуции ('1_hour' или '24_hours')
  - `loaded_at` - дата загрузки

- **Данные из Google Sheets:**
  - Все колонки из исходных таблиц (названия нормализуются автоматически)
  - Например: `campaign`, `spend`, `impressions`, `clicks`, `format`, и т.д.

## Создание Dataset в Superset

1. **Superset** → **Datasets** → **+ Dataset**
2. **Database**: выберите вашу БД (Ubidex Events DB)
3. **Schema**: `public`
4. **Table**: `google_sheets_campaigns`
5. Нажмите **"Create dataset and create chart"**

## Создание Chart

1. **Chart Type**: Table (для табличного отчета)
2. **Query Mode**: Aggregate
3. **Dimensions**: 
   - `campaign` - название кампании
   - `format` - формат рекламы
   - `attribution_type` - тип атрибуции (1_hour / 24_hours)
   - `source_sheet_id` - источник данных
4. **Metrics**:
   - `SUM(spend)` - общие траты
   - `SUM(impressions)` - общие показы
   - `SUM(clicks)` - общие клики
   - `AVG(ctr)` - средний CTR (если есть колонка ctr)
5. **Filters** (на Dashboard):
   - Select для `attribution_type` (1_hour / 24_hours)
   - Select для `format` (POP, PUSH, VIDEO, и т.д.)
   - Select для `campaign` (выбор кампаний)
   - Numeric для `spend` (минимальные траты)

## Обновление данных

Для обновления данных просто запустите скрипт заново. Данные будут добавлены с новой меткой времени `loaded_at`.

Если нужно заменить данные полностью:
```sql
TRUNCATE TABLE google_sheets_campaigns;
```
Затем запустите скрипт загрузки.

## Поиск правильных GID листов

Если скрипт загружает один и тот же лист для обоих типов атрибуции, нужно найти правильные gid:

1. Откройте Google Sheet
2. Переключитесь на лист "1 hour" (или "1 час")
3. Посмотрите на URL: `https://docs.google.com/spreadsheets/d/SHEET_ID/edit#gid=123456789`
4. Запомните gid для листа "1 hour"
5. Переключитесь на лист "24 hours" (или "24 часа")
6. Посмотрите на URL и запомните gid для листа "24 hours"

Затем используйте скрипт с указанием gid:
```powershell
python 07_scripts\load_google_sheets_to_postgresql.py `
  --sheets "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID" `
  --sheet-names "1 hour" "24 hours" `
  --attribution-types "1_hour" "24_hours" `
  --sheet-gids 123456789 987654321
```

## Проверка загруженных данных

```powershell
python 07_scripts\check_google_sheets_data.py
```

Этот скрипт покажет:
- Общую статистику
- Статистику по каждой таблице
- Пробелы по датам
- Дубликаты
- Структуру данных

