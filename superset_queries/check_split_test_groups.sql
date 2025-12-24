-- Проверка распределения по группам сплит-теста
-- Показывает, сколько пользователей попадает в каждую группу

SELECT 
    CASE 
        WHEN LOWER(RIGHT(external_user_id, 1)) IN ('0', '1', '2', '3', '4', '5', '6', '7') 
        THEN 'Control'
        WHEN LOWER(RIGHT(external_user_id, 1)) IN ('8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z') 
        THEN 'Test'
        ELSE 'Unknown'
    END as test_group,
    COUNT(DISTINCT external_user_id) as unique_users,
    COUNT(*) as total_deposits,
    ROUND(COUNT(DISTINCT external_user_id)::NUMERIC / SUM(COUNT(DISTINCT external_user_id)) OVER () * 100, 2) as user_percentage
FROM public.user_events
WHERE event_type = 'deposit'
  AND converted_amount > 0
  AND external_user_id IS NOT NULL
  AND LENGTH(external_user_id) >= 1
  -- Добавьте фильтр по дате для ускорения
  AND event_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY 
    CASE 
        WHEN LOWER(RIGHT(external_user_id, 1)) IN ('0', '1', '2', '3', '4', '5', '6', '7') 
        THEN 'Control'
        WHEN LOWER(RIGHT(external_user_id, 1)) IN ('8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z') 
        THEN 'Test'
        ELSE 'Unknown'
    END
ORDER BY test_group;

