-- Диагностика распределения сплит-теста
-- Показывает примеры user_id, последние символы и распределение по группам

-- 1. Примеры user_id с последним символом
WITH sample_users AS (
    SELECT DISTINCT
        external_user_id,
        LOWER(RIGHT(external_user_id, 1)) as last_char,
        LENGTH(external_user_id) as id_length,
        -- Определяем группу
        CASE 
            WHEN LOWER(RIGHT(external_user_id, 1)) IN ('0', '1', '2', '3', '4', '5', '6', '7') 
            THEN 'Control'
            WHEN LOWER(RIGHT(external_user_id, 1)) IN ('8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z') 
            THEN 'Test'
            ELSE 'Unknown'
        END as test_group
    FROM public.user_events
    WHERE event_type = 'deposit'
      AND converted_amount > 0
      AND external_user_id IS NOT NULL
      AND LENGTH(external_user_id) >= 1
      AND event_date >= CURRENT_DATE - INTERVAL '30 days'
    LIMIT 1000
)

-- Показываем примеры
SELECT 
    'Примеры user_id' as info_type,
    external_user_id,
    last_char,
    id_length,
    test_group
FROM sample_users
ORDER BY RANDOM()
LIMIT 20;

