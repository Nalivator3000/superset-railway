-- Анализ ARPPU и среднего количества депозитов за первую неделю
-- ОПТИМИЗИРОВАННАЯ ВЕРСИЯ: сначала находим подходящих пользователей, потом считаем только по ним
-- Только для пользователей с FTD минимум месяц назад
-- Группировка по неделям FTD
-- 
-- Для использования:
-- 1. Создайте Dataset на основе этого запроса
-- 2. Создайте метрики: 
--    - ARPPU Week 1: AVG(arppu_week1)
--    - Avg Deposits Week 1: AVG(avg_deposits_week1)
--    - Total Revenue Week 1: SUM(total_revenue_week1)
--    - Total Deposits Week 1: SUM(total_deposits_week1)
-- 3. Dimensions: ftd_week_start
-- 4. Визуализация: Line Chart или Bar Chart

WITH 
-- 1. Находим FTD только для пользователей, у которых FTD был минимум месяц назад
-- Это сразу фильтрует данные и ускоряет запрос
eligible_users AS (
    SELECT 
        external_user_id,
        MIN(event_date) as ftd_date,
        DATE_TRUNC('week', MIN(event_date))::date as ftd_week_start
    FROM public.user_events
    WHERE event_type = 'deposit'
      AND converted_amount > 0
      AND external_user_id IS NOT NULL
      AND event_date <= CURRENT_DATE - INTERVAL '1 month'  -- Фильтр сразу по дате
    GROUP BY external_user_id
    HAVING MIN(event_date) <= CURRENT_DATE - INTERVAL '1 month'  -- Дополнительная проверка
),

-- 2. Получаем только депозиты за первую неделю для подходящих пользователей
-- Фильтруем по дате сразу, чтобы не сканировать всю таблицу
user_week1_deposits AS (
    SELECT 
        eu.external_user_id,
        eu.ftd_date,
        eu.ftd_week_start,
        ue.event_date,
        ue.converted_amount
    FROM eligible_users eu
    INNER JOIN public.user_events ue 
        ON ue.external_user_id = eu.external_user_id
        AND ue.event_type = 'deposit'
        AND ue.converted_amount > 0
        AND ue.event_date >= eu.ftd_date  -- Только депозиты от FTD
        AND ue.event_date < eu.ftd_date + INTERVAL '7 days'  -- Только первая неделя
),

-- 3. Агрегируем по пользователям
user_week1_stats AS (
    SELECT 
        external_user_id,
        ftd_week_start,
        COUNT(*) as total_deposits_week1,
        SUM(converted_amount) as total_revenue_week1
    FROM user_week1_deposits
    GROUP BY external_user_id, ftd_week_start
)

-- 4. Финальная агрегация по неделям FTD
SELECT 
    ftd_week_start,
    COUNT(DISTINCT external_user_id) as users_count,
    SUM(total_deposits_week1) as total_deposits_week1,
    SUM(total_revenue_week1) as total_revenue_week1,
    -- ARPPU за первую неделю
    CASE 
        WHEN COUNT(DISTINCT external_user_id) > 0 
        THEN SUM(total_revenue_week1)::NUMERIC / COUNT(DISTINCT external_user_id)
        ELSE 0
    END as arppu_week1,
    -- Среднее количество депозитов за первую неделю
    CASE 
        WHEN COUNT(DISTINCT external_user_id) > 0 
        THEN SUM(total_deposits_week1)::NUMERIC / COUNT(DISTINCT external_user_id)
        ELSE 0
    END as avg_deposits_week1
FROM user_week1_stats
WHERE ftd_week_start != '2025-03-31'::date  -- Исключаем проблемную неделю
GROUP BY ftd_week_start
ORDER BY ftd_week_start;

