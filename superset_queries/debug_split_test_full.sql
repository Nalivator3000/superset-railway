-- Полная диагностика распределения сплит-теста
-- Показывает распределение по последним символам и группам

-- 1. Распределение по последним символам
SELECT 
    'Распределение по символам' as analysis_type,
    LOWER(RIGHT(external_user_id, 1)) as last_char,
    COUNT(DISTINCT external_user_id) as unique_users,
    COUNT(*) as total_deposits,
    ROUND(COUNT(DISTINCT external_user_id)::NUMERIC / SUM(COUNT(DISTINCT external_user_id)) OVER () * 100, 2) as user_percentage
FROM public.user_events
WHERE event_type = 'deposit'
  AND converted_amount > 0
  AND external_user_id IS NOT NULL
  AND LENGTH(external_user_id) >= 1
  AND event_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY LOWER(RIGHT(external_user_id, 1))
ORDER BY last_char;

