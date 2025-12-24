-- Анализ ARPPU и среднего количества депозитов за первый месяц
-- ОПТИМИЗИРОВАННАЯ ВЕРСИЯ: сначала находим подходящих пользователей, потом считаем только по ним
-- Только для пользователей с FTD минимум месяц назад
-- Группировка по месяцам FTD
-- 
-- Для использования:
-- 1. Создайте Dataset на основе этого запроса
-- 2. Создайте метрики: 
--    - ARPPU Month 1: AVG(arppu_month1)
--    - Avg Deposits Month 1: AVG(avg_deposits_month1)
--    - Total Revenue Month 1: SUM(total_revenue_month1)
--    - Total Deposits Month 1: SUM(total_deposits_month1)
-- 3. Dimensions: ftd_month_start
-- 4. Визуализация: Line Chart или Bar Chart

WITH 
-- 1. Находим FTD только для пользователей, у которых FTD был минимум месяц назад
-- Это сразу фильтрует данные и ускоряет запрос
eligible_users AS (
    SELECT 
        external_user_id,
        MIN(event_date) as ftd_date,
        DATE_TRUNC('month', MIN(event_date))::date as ftd_month_start
    FROM public.user_events
    WHERE event_type = 'deposit'
      AND converted_amount > 0
      AND external_user_id IS NOT NULL
      AND event_date <= CURRENT_DATE - INTERVAL '1 month'  -- Фильтр сразу по дате
    GROUP BY external_user_id
    HAVING MIN(event_date) <= CURRENT_DATE - INTERVAL '1 month'  -- Дополнительная проверка
),

-- 2. Получаем только депозиты за первый месяц для подходящих пользователей
-- Фильтруем по дате сразу, чтобы не сканировать всю таблицу
user_month1_deposits AS (
    SELECT 
        eu.external_user_id,
        eu.ftd_date,
        eu.ftd_month_start,
        ue.event_date,
        ue.converted_amount
    FROM eligible_users eu
    INNER JOIN public.user_events ue 
        ON ue.external_user_id = eu.external_user_id
        AND ue.event_type = 'deposit'
        AND ue.converted_amount > 0
        AND ue.event_date >= eu.ftd_date  -- Только депозиты от FTD
        AND ue.event_date < eu.ftd_date + INTERVAL '30 days'  -- Только первый месяц
),

-- 3. Агрегируем по пользователям
user_month1_stats AS (
    SELECT 
        external_user_id,
        ftd_month_start,
        COUNT(*) as total_deposits_month1,
        SUM(converted_amount) as total_revenue_month1
    FROM user_month1_deposits
    GROUP BY external_user_id, ftd_month_start
)

-- 4. Финальная агрегация по месяцам FTD
SELECT 
    ftd_month_start,
    COUNT(DISTINCT external_user_id) as users_count,
    SUM(total_deposits_month1) as total_deposits_month1,
    SUM(total_revenue_month1) as total_revenue_month1,
    -- ARPPU за первый месяц
    CASE 
        WHEN COUNT(DISTINCT external_user_id) > 0 
        THEN SUM(total_revenue_month1)::NUMERIC / COUNT(DISTINCT external_user_id)
        ELSE 0
    END as arppu_month1,
    -- Среднее количество депозитов за первый месяц
    CASE 
        WHEN COUNT(DISTINCT external_user_id) > 0 
        THEN SUM(total_deposits_month1)::NUMERIC / COUNT(DISTINCT external_user_id)
        ELSE 0
    END as avg_deposits_month1
FROM user_month1_stats
GROUP BY ftd_month_start
ORDER BY ftd_month_start;

