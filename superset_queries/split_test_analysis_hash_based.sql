-- Анализ сплит-теста: сравнение контрольной и тестовой групп (НА ОСНОВЕ ХЕША)
-- 
-- Использует хеш от user_id для равномерного распределения 25/75
-- Работает независимо от формата user_id (цифры, буквы, смешанные)
--
-- Преимущества:
-- - Гарантированное распределение 25/75
-- - Работает с любым форматом user_id
-- - Не зависит от распределения символов
--
-- Для использования:
-- 1. Создайте Dataset на основе этого запроса
-- 2. Добавьте фильтры на Dashboard для дат (Time Range Filter)
-- 3. Для очень больших данных добавьте фильтр по дате прямо в SQL

WITH 
-- 1. Получаем все депозиты с определением группы на основе хеша
deposits_with_groups AS (
    SELECT 
        ue.external_user_id as user_id,
        ue.event_date,
        ue.converted_amount as deposit_amount,
        ue.advertiser,
        -- Определяем группу на основе хеша (гарантирует 25/75 распределение)
        CASE 
            -- Control: остаток от деления хеша на 4 = 0 (25%)
            WHEN ABS(HASHTEXT(ue.external_user_id)) % 4 < 1 
            THEN 'Control'
            -- Test: остаток от деления хеша на 4 = 1, 2, 3 (75%)
            ELSE 'Test'
        END as test_group
    FROM public.user_events ue
    WHERE ue.event_type = 'deposit'
      AND ue.converted_amount > 0
      AND ue.external_user_id IS NOT NULL
      AND LENGTH(ue.external_user_id) >= 1
      -- ВАЖНО: Добавьте фильтр по дате для ускорения запроса!
      -- Раскомментируйте одну из строк ниже:
      AND ue.event_date >= CURRENT_DATE - INTERVAL '30 days'  -- Последние 30 дней
      -- AND ue.event_date >= CURRENT_DATE - INTERVAL '90 days'  -- Последние 90 дней
      -- AND ue.event_date >= '2025-01-01'::date  -- С конкретной даты
      -- Фильтрация по дате также применяется через Dashboard фильтры (Time Range Filter)
),

-- 2. Агрегируем по пользователям для расчета активности
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

-- 3. Исключаем выбросы (топ и низ активных игроков)
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

-- 4. Фильтруем выбросы (если указаны параметры)
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

-- 5. Возвращаемся к депозитам отфильтрованных пользователей
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

-- 6. Финальная агрегация по группам
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
)

-- Итоговый результат
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
ORDER BY test_group;

