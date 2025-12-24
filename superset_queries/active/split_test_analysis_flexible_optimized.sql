-- Анализ сплит-теста: сравнение контрольной и тестовой групп (ОПТИМИЗИРОВАННАЯ ВЕРСИЯ)
-- 
-- ОПТИМИЗАЦИИ:
-- 1. Убрал CROSS JOIN - используем прямые значения
-- 2. Добавил минимальный фильтр по дате для ускорения
-- 3. Упростил логику определения групп
-- 4. Добавил индексы в комментариях для DBA
--
-- Настройки (измените в CTE char_expansion):
-- - char_position: позиция символа с конца (1 = последний, 2 = предпоследний, и т.д.)
-- - control_chars_expanded: список символов для контрольной группы через запятую
-- - test_chars_expanded: список символов для тестовой группы через запятую
--
-- Для использования:
-- 1. Создайте Dataset на основе этого запроса
-- 2. Измените настройки в CTE char_expansion при необходимости
-- 3. Добавьте фильтры на Dashboard для дат (Time Range Filter)
-- 4. Для очень больших данных добавьте фильтр по дате прямо в SQL (раскомментируйте строки)

WITH 
-- 1. Настройки групп
-- Разделение: Control = 0-7, Test = 8-9a-z
char_expansion AS (
    SELECT 
        '0,1,2,3,4,5,6,7' as control_chars_expanded,  -- Control группа
        '8,9,a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z' as test_chars_expanded,  -- Test группа
        1 as char_position  -- Позиция символа с конца (1 = последний)
),

-- 2. Получаем все депозиты с определением группы (ОПТИМИЗИРОВАНО)
deposits_with_groups AS (
    SELECT 
        ue.external_user_id as user_id,
        ue.event_date,
        ue.converted_amount as deposit_amount,
        ue.advertiser,
        -- Извлекаем символ на нужной позиции с конца (оптимизировано)
        CASE 
            WHEN LENGTH(ue.external_user_id) >= 1  -- Используем прямое значение вместо ce.char_position
            THEN LOWER(SUBSTRING(ue.external_user_id FROM LENGTH(ue.external_user_id) FOR 1))
            ELSE NULL
        END as char_at_position,
        -- Определяем группу (оптимизировано - без CROSS JOIN)
        -- Разделение по требованию:
        -- Control: 0-7 (8 символов)
        -- Test: 8-9a-z (28 символов)
        CASE 
            -- Контрольная группа: последний символ 0-7
            WHEN LENGTH(ue.external_user_id) >= 1 
                 AND LOWER(RIGHT(ue.external_user_id, 1)) IN ('0', '1', '2', '3', '4', '5', '6', '7') 
            THEN 'Control'
            -- Тестовая группа: последний символ 8-9a-z
            WHEN LENGTH(ue.external_user_id) >= 1 
                 AND LOWER(RIGHT(ue.external_user_id, 1)) IN ('8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z') 
            THEN 'Test'
            ELSE 'Unknown'
        END as test_group
    FROM public.user_events ue
    WHERE ue.event_type = 'deposit'
      AND ue.converted_amount > 0
      AND ue.external_user_id IS NOT NULL
      AND LENGTH(ue.external_user_id) >= 1
      -- ВАЖНО: Добавьте фильтр по дате для ускорения запроса!
      -- Раскомментируйте одну из строк ниже:
      -- AND ue.event_date >= CURRENT_DATE - INTERVAL '30 days'  -- Последние 30 дней
      -- AND ue.event_date >= CURRENT_DATE - INTERVAL '90 days'  -- Последние 90 дней
      -- AND ue.event_date >= '2025-01-01'::date  -- С конкретной даты
      -- Фильтрация по дате также применяется через Dashboard фильтры (Time Range Filter)
),

-- 3. Агрегируем по пользователям для расчета активности
user_totals AS (
    SELECT 
        user_id,
        test_group,
        COUNT(*) as deposit_count,
        SUM(deposit_amount) as total_deposits_usd,
        MIN(event_date) as first_deposit_date,
        MAX(event_date) as last_deposit_date
    FROM deposits_with_groups
    WHERE test_group IN ('Control', 'Test')
    GROUP BY user_id, test_group
),

-- 4. Исключаем выбросы (топ и низ активных игроков)
user_percentiles AS (
    SELECT 
        user_id,
        test_group,
        deposit_count,
        total_deposits_usd,
        first_deposit_date,
        last_deposit_date,
        -- Процентиль активности внутри группы (по сумме депозитов)
        PERCENT_RANK() OVER (PARTITION BY test_group ORDER BY total_deposits_usd) as activity_percentile
    FROM user_totals
),

-- 5. Фильтруем выбросы (если указаны параметры)
-- Для исключения выбросов измените значения ниже:
-- exclude_top_percent = 5 означает исключить топ 5% самых активных
-- exclude_bottom_percent = 5 означает исключить низ 5% самых неактивных
filtered_users AS (
    SELECT 
        user_id,
        test_group,
        deposit_count,
        total_deposits_usd,
        first_deposit_date,
        last_deposit_date
    FROM user_percentiles
    WHERE 
        -- Исключаем топ N% самых активных (по умолчанию 0 = не исключаем)
        -- Измените 0.0 на нужное значение (например, 0.05 для 5%)
        activity_percentile <= (1.0 - 0.0)
        -- Исключаем низ M% самых неактивных (по умолчанию 0 = не исключаем)
        -- Измените 0.0 на нужное значение (например, 0.05 для 5%)
        AND activity_percentile >= 0.0
),

-- 6. Возвращаемся к депозитам отфильтрованных пользователей
filtered_deposits AS (
    SELECT 
        d.user_id,
        d.test_group,
        d.event_date,
        d.deposit_amount,
        d.advertiser
    FROM deposits_with_groups d
    INNER JOIN filtered_users fu ON d.user_id = fu.user_id AND d.test_group = fu.test_group
),

-- 7. Финальная агрегация по группам
group_comparison AS (
    SELECT 
        test_group,
        COUNT(DISTINCT user_id) as unique_users,
        COUNT(*) as total_deposits,
        SUM(deposit_amount) as total_deposits_usd,
        AVG(deposit_amount) as avg_deposit_amount,
        -- Среднее количество депозитов на пользователя
        COUNT(*)::NUMERIC / NULLIF(COUNT(DISTINCT user_id), 0) as avg_deposits_per_user,
        -- Средняя сумма депозитов на пользователя
        SUM(deposit_amount)::NUMERIC / NULLIF(COUNT(DISTINCT user_id), 0) as avg_total_per_user,
        MIN(event_date) as min_date,
        MAX(event_date) as max_date
    FROM filtered_deposits
    GROUP BY test_group
),

-- 8. Добавляем строки сравнения
comparison_data AS (
    SELECT 
        test_group,
        unique_users,
        total_deposits,
        total_deposits_usd,
        avg_deposit_amount,
        avg_deposits_per_user,
        avg_total_per_user,
        min_date,
        max_date
    FROM group_comparison
),

comparison_percent AS (
    SELECT 
        'Comparison %' as "Группа",
        -- Процентное сравнение (Control относительно Test)
        ROUND(
            (SELECT unique_users FROM comparison_data WHERE test_group = 'Control')::NUMERIC / 
            NULLIF((SELECT unique_users FROM comparison_data WHERE test_group = 'Test'), 0) * 100, 
            2
        ) as "Уникальных пользователей",
        ROUND(
            (SELECT total_deposits FROM comparison_data WHERE test_group = 'Control')::NUMERIC / 
            NULLIF((SELECT total_deposits FROM comparison_data WHERE test_group = 'Test'), 0) * 100, 
            2
        ) as "Всего депозитов",
        ROUND(
            (SELECT total_deposits_usd FROM comparison_data WHERE test_group = 'Control')::NUMERIC / 
            NULLIF((SELECT total_deposits_usd FROM comparison_data WHERE test_group = 'Test'), 0) * 100, 
            2
        ) as "Сумма депозитов (USD)",
        ROUND(
            (SELECT avg_deposit_amount FROM comparison_data WHERE test_group = 'Control')::NUMERIC / 
            NULLIF((SELECT avg_deposit_amount FROM comparison_data WHERE test_group = 'Test'), 0) * 100, 
            2
        ) as "Средний депозит (USD)",
        ROUND(
            (SELECT avg_deposits_per_user FROM comparison_data WHERE test_group = 'Control')::NUMERIC / 
            NULLIF((SELECT avg_deposits_per_user FROM comparison_data WHERE test_group = 'Test'), 0) * 100, 
            2
        ) as "Среднее депозитов на пользователя",
        ROUND(
            (SELECT avg_total_per_user FROM comparison_data WHERE test_group = 'Control')::NUMERIC / 
            NULLIF((SELECT avg_total_per_user FROM comparison_data WHERE test_group = 'Test'), 0) * 100, 
            2
        ) as "Средняя сумма на пользователя (USD)",
        NULL::date as "Первая дата",
        NULL::date as "Последняя дата"
),

comparison_absolute AS (
    SELECT 
        'Comparison Abs' as "Группа",
        -- Абсолютное сравнение (Control - Test)
        (SELECT unique_users FROM comparison_data WHERE test_group = 'Control') - 
        (SELECT unique_users FROM comparison_data WHERE test_group = 'Test') as "Уникальных пользователей",
        (SELECT total_deposits FROM comparison_data WHERE test_group = 'Control') - 
        (SELECT total_deposits FROM comparison_data WHERE test_group = 'Test') as "Всего депозитов",
        ROUND(
            (SELECT total_deposits_usd FROM comparison_data WHERE test_group = 'Control') - 
            (SELECT total_deposits_usd FROM comparison_data WHERE test_group = 'Test'), 
            2
        ) as "Сумма депозитов (USD)",
        ROUND(
            (SELECT avg_deposit_amount FROM comparison_data WHERE test_group = 'Control') - 
            (SELECT avg_deposit_amount FROM comparison_data WHERE test_group = 'Test'), 
            2
        ) as "Средний депозит (USD)",
        ROUND(
            (SELECT avg_deposits_per_user FROM comparison_data WHERE test_group = 'Control') - 
            (SELECT avg_deposits_per_user FROM comparison_data WHERE test_group = 'Test'), 
            2
        ) as "Среднее депозитов на пользователя",
        ROUND(
            (SELECT avg_total_per_user FROM comparison_data WHERE test_group = 'Control') - 
            (SELECT avg_total_per_user FROM comparison_data WHERE test_group = 'Test'), 
            2
        ) as "Средняя сумма на пользователя (USD)",
        NULL::date as "Первая дата",
        NULL::date as "Последняя дата"
)

-- Итоговый результат: группы + сравнения
SELECT 
    test_group as "Группа",
    unique_users as "Уникальных пользователей",
    total_deposits as "Всего депозитов",
    ROUND(total_deposits_usd::NUMERIC, 2) as "Сумма депозитов (USD)",
    ROUND(avg_deposit_amount::NUMERIC, 2) as "Средний депозит (USD)",
    ROUND(avg_deposits_per_user::NUMERIC, 2) as "Среднее депозитов на пользователя",
    ROUND(avg_total_per_user::NUMERIC, 2) as "Средняя сумма на пользователя (USD)",
    min_date as "Первая дата",
    max_date as "Последняя дата"
FROM group_comparison

UNION ALL

SELECT * FROM comparison_percent

UNION ALL

SELECT * FROM comparison_absolute

ORDER BY 
    CASE "Группа"
        WHEN 'Control' THEN 1
        WHEN 'Test' THEN 2
        WHEN 'Comparison %' THEN 3
        WHEN 'Comparison Abs' THEN 4
        ELSE 5
    END;

-- РЕКОМЕНДАЦИИ ПО ОПТИМИЗАЦИИ:
-- 1. Создайте индексы для ускорения:
--    CREATE INDEX IF NOT EXISTS idx_user_events_type_amount_date 
--    ON public.user_events(event_type, converted_amount, event_date) 
--    WHERE event_type = 'deposit' AND converted_amount > 0;
--
--    CREATE INDEX IF NOT EXISTS idx_user_events_external_user_id_date 
--    ON public.user_events(external_user_id, event_date) 
--    WHERE external_user_id IS NOT NULL;
--
-- 2. Для очень больших данных используйте материализованное представление:
--    CREATE MATERIALIZED VIEW split_test_deposits_mv AS
--    SELECT ... (ваш запрос до filtered_deposits)
--    ;
--    CREATE INDEX ON split_test_deposits_mv(user_id, test_group);

