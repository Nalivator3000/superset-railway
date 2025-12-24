-- Проверка распределения последних символов в user_id
-- Этот запрос покажет, какие символы реально используются и их распределение

SELECT 
    LOWER(RIGHT(external_user_id, 1)) as last_char,
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
GROUP BY LOWER(RIGHT(external_user_id, 1))
ORDER BY last_char;

