# Решение проблемы таймаута 60 секунд

## ⚠️ ВАЖНО: Ошибка с connect_args

Если вы получили ошибку:
```
ERROR: (builtins.NoneType) None
[SQL: (psycopg2.ProgrammingError) invalid dsn: invalid connection option "connect_args"
```

**Это означает, что вы пытались добавить `connect_args` в SQLAlchemy URI, но это не работает в Superset UI!**

**Правильное решение:** Используйте **асинхронные запросы** (см. Решение 1, Способ A ниже).

---

## Проблема

```
Timeout error: We're having trouble loading this visualization. 
Queries are set to timeout after 60 seconds.
```

## Решения (от простого к сложному)

---

## Решение 1: Увеличить таймаут в настройках Database (РЕКОМЕНДУЕТСЯ)

Это самый простой и эффективный способ:

1. **Откройте Superset** → **Data** → **Databases**
2. Найдите вашу базу данных (например, "Ubidex Events DB")
3. **Кликните на название базы данных** для редактирования

### Способ A: Использовать асинхронные запросы (РЕКОМЕНДУЕТСЯ - РАБОТАЕТ ТОЧНО)

⚠️ **Важно:** Параметр `connect_args` нельзя передавать напрямую в URI строке в Superset UI. Используйте асинхронные запросы вместо этого.

4. Прокрутите вниз до раздела **"Query Execution Options"** (в "Advanced")
5. Включите чекбокс **"Asynchronous query execution"** ✅
   - Это позволит запросам выполняться в фоне
   - Избежит таймаута веб-сервера (60 секунд)
   - Запросы будут выполняться до таймаута базы данных (обычно больше 60 секунд)
6. Нажмите **"Save"**

### Способ B: Настроить таймаут через конфигурацию Superset

Конфигурация уже обновлена в `superset_config.py` со следующими настройками:

```python
# Query timeout settings (in seconds)
SQLLAB_TIMEOUT = 600  # 10 minutes for SQL Lab queries
SQLLAB_ASYNC_TIME_LIMIT_SEC = 600  # 10 minutes for async queries
SUPERSET_WEBSERVER_TIMEOUT = 600  # 10 minutes for web server requests
CHART_QUERY_TIMEOUT = 600  # 10 minutes for chart queries
```

**Как перезапустить Superset на Railway:**

1. **Через Railway Dashboard (РЕКОМЕНДУЕТСЯ):**
   - Откройте ваш проект на [Railway.app](https://railway.app)
   - Найдите сервис с Superset
   - Нажмите на **три точки (⋮)** рядом с сервисом
   - Выберите **"Restart"** или **"Redeploy"**
   - Дождитесь перезапуска (обычно 1-2 минуты)

2. **Через Git Push (если настроен автоматический деплой):**
   ```bash
   git add superset_config.py
   git commit -m "Update Superset timeout settings"
   git push
   ```
   Railway автоматически перезапустит контейнер после деплоя

3. **Через Railway CLI (если установлен):**
   ```bash
   railway restart
   ```

**Проверка:** После перезапуска откройте Superset и проверьте, что запросы больше не таймаутятся через 60 секунд.

### Способ C: Настроить таймаут на уровне PostgreSQL (для опытных пользователей)

Если у вас есть доступ к настройкам PostgreSQL, можно установить таймаут глобально:

```sql
ALTER DATABASE railway SET statement_timeout = '600000';  -- 10 минут в миллисекундах
```

**⚠️ ВНИМАНИЕ:** Не изменяйте SQLAlchemy URI с `connect_args` - это не работает в Superset UI!

### Способ D: Найти поле Query Timeout (если доступно)

4. Прокрутите вниз в разделе **"Advanced"**
5. Найдите поле **"Query Timeout"** или **"SQL Query Timeout"** (может быть в разных версиях Superset)
6. Введите значение в секундах:
   - `600` = 10 минут
   - `1200` = 20 минут
   - `1800` = 30 минут
7. Нажмите **"Save"**

**Опционально:** В разделе **"Query Execution Options"** можно также включить:
- **"Cancel query on window unload event"** ✅ - отменяет запрос, если пользователь закрыл вкладку

---

## Решение 2: Обновить конфигурацию Superset

Конфигурация уже обновлена в `superset_config.py`:

```python
SQLLAB_TIMEOUT = 600  # 10 minutes
SQLLAB_ASYNC_TIME_LIMIT_SEC = 600  # 10 minutes
SUPERSET_WEBSERVER_TIMEOUT = 600  # 10 minutes
```

**Чтобы применить изменения:**

1. **Если используете Docker:**
   ```bash
   docker-compose restart superset
   ```

2. **Если используете Railway или другой хостинг:**
   - Перезапустите контейнер Superset
   - Или дождитесь автоматического перезапуска

---

## Решение 3: Оптимизировать SQL запросы

Добавьте фильтры по дате прямо в SQL запрос, чтобы уменьшить объем обрабатываемых данных:

### Для недельного запроса:

Откройте `arppu_first_period_weekly.sql` и добавьте ограничение по дате:

```sql
-- Добавьте в начало CTE eligible_users:
WHERE event_type = 'deposit'
  AND converted_amount > 0
  AND external_user_id IS NOT NULL
  AND event_date <= CURRENT_DATE - INTERVAL '1 month'
  AND event_date >= '2024-01-01'  -- ← Добавьте минимальную дату
```

### Для месячного запроса:

Аналогично в `arppu_first_period_monthly.sql`:

```sql
-- Добавьте ограничение по дате:
AND event_date >= '2024-01-01'  -- ← Минимальная дата для анализа
```

**Рекомендация:** Установите минимальную дату на основе ваших данных (например, начало года или начало периода, который вас интересует).

---

## Решение 4: Создать материализованные представления

Для очень больших данных создайте материализованные представления:

### Для недельного анализа:

```sql
CREATE MATERIALIZED VIEW arppu_first_period_weekly_mv AS
-- Вставьте весь SQL из arppu_first_period_weekly.sql
;

-- Создайте индексы
CREATE INDEX idx_arppu_weekly_ftd ON arppu_first_period_weekly_mv(ftd_week_start);
CREATE INDEX idx_arppu_weekly_users ON arppu_first_period_weekly_mv(external_user_id);
```

### Для месячного анализа:

```sql
CREATE MATERIALIZED VIEW arppu_first_period_monthly_mv AS
-- Вставьте весь SQL из arppu_first_period_monthly.sql
;

-- Создайте индексы
CREATE INDEX idx_arppu_monthly_ftd ON arppu_first_period_monthly_mv(ftd_month_start);
CREATE INDEX idx_arppu_monthly_users ON arppu_first_period_monthly_mv(external_user_id);
```

### Обновление материализованных представлений:

```sql
-- Обновляйте вручную или по расписанию (например, раз в день):
REFRESH MATERIALIZED VIEW arppu_first_period_weekly_mv;
REFRESH MATERIALIZED VIEW arppu_first_period_monthly_mv;
```

### Использование в Superset:

1. Создайте новый Dataset на основе материализованного представления
2. Используйте его вместо исходного SQL запроса
3. Обновляйте представление вручную при необходимости

---

## Решение 5: Настроить кэширование

Настройте кэширование, чтобы избежать повторных запросов:

1. **В настройках Dataset:**
   - Найдите раздел **"Cache"**
   - Установите **Cache Timeout**: `86400` (24 часа)

2. **В настройках Chart:**
   - Найдите раздел **"Cache"** или **"Query Cache"**
   - Включите кэширование

3. **Отключите автообновление Dashboard:**
   - См. инструкцию в `ARPPU_FIRST_PERIOD_SETUP.md`, Шаг 8

---

## Решение 6: Оптимизировать индексы в PostgreSQL

Убедитесь, что есть индексы для ускорения запросов:

```sql
-- Индексы для user_events (если еще не созданы)
CREATE INDEX IF NOT EXISTS idx_user_events_ftd_lookup 
ON user_events(event_type, converted_amount, external_user_id, event_date) 
WHERE event_type = 'deposit' AND converted_amount > 0;

CREATE INDEX IF NOT EXISTS idx_user_events_date_range 
ON user_events(event_date) 
WHERE event_date <= CURRENT_DATE - INTERVAL '1 month';
```

---

## Проверка результата

После применения решений:

1. **Проверьте таймаут в настройках Database:**
   - Data → Databases → ваша БД → Advanced → Query Timeout
   - Должно быть `600` или больше

2. **Проверьте конфигурацию:**
   - Убедитесь, что `superset_config.py` обновлен
   - Перезапустите Superset

3. **Протестируйте запрос:**
   - Откройте Chart отдельно
   - Нажмите "Run Query"
   - Запрос должен выполняться дольше 60 секунд без таймаута

---

## Рекомендуемый порядок действий

1. ✅ **Сначала:** Увеличьте таймаут в настройках Database (Решение 1)
2. ✅ **Затем:** Оптимизируйте SQL запросы (Решение 3) - добавьте фильтры по дате
3. ✅ **Если все еще медленно:** Создайте материализованные представления (Решение 4)
4. ✅ **Для ускорения:** Настройте кэширование (Решение 5)

---

## Дополнительные советы

- **Мониторинг:** Следите за временем выполнения запросов в SQL Lab
- **Оптимизация:** Регулярно обновляйте статистику PostgreSQL: `ANALYZE user_events;`
- **Партиционирование:** Для очень больших таблиц рассмотрите партиционирование по дате

