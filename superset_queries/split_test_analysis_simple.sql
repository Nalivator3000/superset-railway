-- Анализ сплит-теста: УПРОЩЕННАЯ ВЕРСИЯ БЕЗ СЛОЖНЫХ ВЫЧИСЛЕНИЙ
-- Используйте эту версию, если запрос зависает
-- 
-- Настройки (измените при необходимости):
-- - char_position: позиция символа с конца (1 = последний)
-- - control_chars: символы для контрольной группы
-- - test_chars: символы для тестовой группы
--
-- ВАЖНО: Обязательно добавьте фильтр по дате!

WITH 
-- 1. Получаем депозиты с определением группы (упрощенно)
deposits_with_groups AS (
    SELECT 
        ue.external_user_id as user_id,
        ue.event_date,
        ue.converted_amount as deposit_amount,
        -- Определяем группу по последнему символу (упрощенно)
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
      AND LENGTH(ue.external_user_id) >= 1
      -- ОБЯЗАТЕЛЬНО: Добавьте фильтр по дате!
      AND ue.event_date >= CURRENT_DATE - INTERVAL '30 days'  -- Последние 30 дней
      -- ИЛИ используйте конкретную дату:
      -- AND ue.event_date >= '2025-12-01'::date
),

-- 2. Агрегируем по пользователям (БЕЗ исключения выбросов для упрощения)
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

-- 3. Финальная агрегация по группам (БЕЗ сложных вычислений процентилей)
group_comparison AS (
    SELECT 
        test_group,
        COUNT(DISTINCT user_id) as unique_users,
        SUM(deposit_count) as total_deposits,
        SUM(total_deposits_usd) as total_deposits_usd,
        AVG(total_deposits_usd / NULLIF(deposit_count, 0)) as avg_deposit_amount,
        AVG(deposit_count)::NUMERIC as avg_deposits_per_user,
        AVG(total_deposits_usd)::NUMERIC as avg_total_per_user,
        MIN(first_deposit_date) as min_date,
        MAX(last_deposit_date) as max_date
    FROM user_totals
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

