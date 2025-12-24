# Исправление проблемы зависания запроса сплит-теста

## Проблема

SQL запрос зависает и не завершается. Таймер не запускается, процесс "pending" бесконечно.

## Причины

1. **Отсутствие фильтров по дате** - запрос обрабатывает все данные из таблицы `user_events` (может быть миллионы записей)
2. **CROSS JOIN** - создает декартово произведение, что замедляет запрос
3. **Сложные вычисления** - PERCENT_RANK() и множественные JOIN'ы на больших данных
4. **Отсутствие индексов** - запрос не использует индексы эффективно

## Решения

### Решение 1: Добавить фильтр по дате в SQL (ОБЯЗАТЕЛЬНО!)

Откройте SQL запрос и раскомментируйте одну из строк фильтрации:

```sql
-- В CTE deposits_with_groups, после строки:
AND LENGTH(ue.external_user_id) >= ce.char_position

-- Добавьте (раскомментируйте):
AND ue.event_date >= CURRENT_DATE - INTERVAL '30 days'  -- Последние 30 дней
-- ИЛИ
AND ue.event_date >= CURRENT_DATE - INTERVAL '90 days'  -- Последние 90 дней
-- ИЛИ
AND ue.event_date >= '2025-01-01'::date  -- С конкретной даты
```

**Это критически важно!** Без фильтра по дате запрос будет обрабатывать все данные.

### Решение 2: Использовать оптимизированную версию

Используйте файл `split_test_analysis_flexible_optimized.sql`:
- Убран CROSS JOIN
- Упрощена логика определения групп
- Добавлены комментарии с рекомендациями по индексам

### Решение 3: Создать индексы

Выполните в SQL Lab или через psql:

```sql
-- Индекс для фильтрации депозитов
CREATE INDEX IF NOT EXISTS idx_user_events_type_amount_date 
ON public.user_events(event_type, converted_amount, event_date) 
WHERE event_type = 'deposit' AND converted_amount > 0;

-- Индекс для связи по user_id
CREATE INDEX IF NOT EXISTS idx_user_events_external_user_id_date 
ON public.user_events(external_user_id, event_date) 
WHERE external_user_id IS NOT NULL;
```

### Решение 4: Использовать материализованное представление (для очень больших данных)

Если данные не меняются часто, создайте материализованное представление:

```sql
-- Создайте представление с предрасчетом групп
CREATE MATERIALIZED VIEW split_test_deposits_mv AS
SELECT 
    ue.external_user_id as user_id,
    ue.event_date,
    ue.converted_amount as deposit_amount,
    CASE 
        WHEN LOWER(RIGHT(ue.external_user_id, 1)) IN ('0', '1', '2', '3', '4', '5', '6', '7') 
        THEN 'Control'
        WHEN LOWER(RIGHT(ue.external_user_id, 1)) IN ('8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z') 
        THEN 'Test'
        ELSE 'Unknown'
    END as test_group
FROM public.user_events ue
WHERE ue.event_type = 'deposit'
  AND ue.converted_amount > 0
  AND ue.external_user_id IS NOT NULL
  AND ue.event_date >= CURRENT_DATE - INTERVAL '90 days';  -- Фильтр по дате!

-- Создайте индексы
CREATE INDEX ON split_test_deposits_mv(user_id, test_group);
CREATE INDEX ON split_test_deposits_mv(event_date);

-- Обновляйте представление при необходимости
REFRESH MATERIALIZED VIEW split_test_deposits_mv;
```

Затем используйте это представление в основном запросе вместо `deposits_with_groups`.

## Рекомендуемый порядок действий

1. **СРОЧНО:** Добавьте фильтр по дате в SQL запрос (раскомментируйте строку)
2. **Проверьте:** Запрос должен выполняться быстрее
3. **Создайте индексы:** Для дальнейшего ускорения
4. **Если все еще медленно:** Используйте оптимизированную версию или материализованное представление

## Проверка производительности

После добавления фильтра по дате:

1. Запрос должен начать выполняться (таймер запустится)
2. Время выполнения должно быть разумным (< 1 минуты для 30 дней данных)
3. Результаты должны появиться в таблице

## Если проблема сохраняется

1. Уменьшите период данных (используйте 7 дней вместо 30)
2. Проверьте, что индексы созданы и используются
3. Используйте упрощенную версию без исключения выбросов (закомментируйте CTE filtered_users)
4. Обратитесь к DBA для проверки производительности базы данных

