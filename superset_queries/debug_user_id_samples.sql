-- Примеры user_id для проверки формата
-- Показывает 100 случайных user_id с их последними символами

SELECT 
    external_user_id,
    LENGTH(external_user_id) as id_length,
    LOWER(RIGHT(external_user_id, 1)) as last_char,
    LOWER(RIGHT(external_user_id, 2)) as last_2_chars,
    LOWER(RIGHT(external_user_id, 3)) as last_3_chars,
    -- Проверка группы
    CASE 
        WHEN LOWER(RIGHT(external_user_id, 1)) IN ('0', '1', '2', '3', '4', '5', '6', '7') 
        THEN 'Control'
        WHEN LOWER(RIGHT(external_user_id, 1)) IN ('8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z') 
        THEN 'Test'
        ELSE 'Unknown'
    END as test_group
FROM (
    SELECT DISTINCT external_user_id
    FROM public.user_events
    WHERE event_type = 'deposit'
      AND converted_amount > 0
      AND external_user_id IS NOT NULL
      AND LENGTH(external_user_id) >= 1
      AND event_date >= CURRENT_DATE - INTERVAL '30 days'
    LIMIT 1000
) sample
ORDER BY RANDOM()
LIMIT 100;

