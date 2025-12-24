-- Отчет: Средний ARPPU (Average Revenue Per Paying User) по атрибутам
-- С опциональными параметрами для фильтрации по дате (для ускорения запроса)
-- 
-- Параметры Superset (опционально, для ускорения):
--   - start_date: Дата начала периода (формат: 'YYYY-MM-DD', например: '2025-11-01')
--   - end_date: Дата окончания периода (формат: 'YYYY-MM-DD', например: '2025-12-18')
--   Если параметры не заданы, запрос обработает все данные (может быть медленным)
-- 
-- Для использования:
-- 1. Создайте Chart на основе этого запроса
-- 2. В Query Settings (опционально) задайте параметры start_date и end_date для ускорения
-- 3. Добавьте фильтры на Dashboard:
--    - Time Range фильтр для min_event_date или max_event_date (дата депозита)
--    - Select фильтр для brand (4rabet / Crorebet / All)
--    - Select фильтр для breakdown_type (Publisher / Format / Campaign / Site / Region / All users)
--    - Numeric фильтр для total_deposits (минимальное количество депозитов)
-- 4. Примените фильтры к Chart через Scoping
--
-- Разбивки:
-- - По паблишеру (publisher_id)
-- - По формату (format - извлекается из publisher_spend или sub_id)
-- - По рекламной кампании (campaign_id)
-- - По сайту (website)
-- - По региону (country)
-- - По бренду (4rabet / Crorebet - определяется по полю advertiser, с 2 декабря 2025)
-- - Все пользователи (без разбивки по атрибуции, включая неатрибутированных)
--
-- Примечание: Разбивки по OS и Browser пока не включены, так как эти поля отсутствуют
-- в таблице user_events. Если они появятся позже, можно будет добавить аналогичные CTE.

WITH 
-- 0. Предварительно определяем формат для каждого паблишера (оптимизация)
publisher_format AS (
    SELECT DISTINCT ON (publisher_id)
        publisher_id,
        format
    FROM publisher_spend
    WHERE publisher_id IS NOT NULL AND publisher_id != 0
    GROUP BY publisher_id, format
    ORDER BY publisher_id, COUNT(*) DESC
),

-- 1. Получаем все депозиты с атрибутами и форматом
deposits AS (
    SELECT 
        ue.external_user_id,
        ue.event_date,
        ue.publisher_id,
        ue.campaign_id,
        ue.website,
        ue.country,
        ue.converted_amount,  -- Сумма депозита в USD
        -- Определяем бренд по advertiser (если NULL, используем website как fallback)
        COALESCE(
            ue.advertiser,
            CASE 
                WHEN ue.website ILIKE '%crorebet%' OR ue.website ILIKE '%crore%' THEN 'Crorebet'
                WHEN ue.website ILIKE '%4rabet%' OR ue.website ILIKE '%4ra%' THEN '4rabet'
                ELSE 'Unknown'
            END
        ) as brand,
        -- Извлекаем формат из предварительно подготовленной таблицы или sub_id
        COALESCE(
            pf.format,
            CASE 
                WHEN ue.sub_id ILIKE '%POP%' OR ue.sub_id ILIKE '%-POP%' THEN 'POP'
                WHEN ue.sub_id ILIKE '%PUSH%' OR ue.sub_id ILIKE '%-PUSH%' THEN 'PUSH'
                WHEN ue.sub_id ILIKE '%VIDEO%' OR ue.sub_id ILIKE '%-VIDEO%' THEN 'VIDEO'
                WHEN ue.sub_id ILIKE '%BANNER%' OR ue.sub_id ILIKE '%-BANNER%' THEN 'BANNER'
                WHEN ue.sub_id ILIKE '%NATIVE%' OR ue.sub_id ILIKE '%-NATIVE%' THEN 'NATIVE'
                ELSE 'OTHER'
            END
        ) as format
    FROM public.user_events ue
    LEFT JOIN publisher_format pf ON ue.publisher_id = pf.publisher_id
    WHERE ue.event_type = 'deposit'
      AND ue.converted_amount > 0  -- Только реальные депозиты
      AND ue.external_user_id IS NOT NULL  -- Только пользователи с ID
      -- Фильтрация по дате (раскомментируй и установи даты для ускорения запроса)
      -- Рекомендуется ограничить период, например, последний месяц:
      -- AND ue.event_date >= '2025-11-01'::date
      -- AND ue.event_date <= '2025-12-18'::date
),

-- 2. Агрегируем по пользователям для расчета ARPPU (сохраняем даты для фильтрации)
user_totals AS (
    SELECT 
        external_user_id,
        brand,
        publisher_id,
        campaign_id,
        website,
        country,
        format,
        MIN(event_date) as min_event_date,
        MAX(event_date) as max_event_date,
        COUNT(*) as deposit_count,
        SUM(converted_amount) as total_deposits_usd
    FROM deposits
    GROUP BY 
        external_user_id,
        brand,
        publisher_id,
        campaign_id,
        website,
        country,
        format
),

-- 3. Рассчитываем ARPPU по разным разбивкам
arppu_by_publisher AS (
    SELECT 
        'Publisher' as breakdown_type,
        brand,
        publisher_id::TEXT as breakdown_value,
        NULL::TEXT as format,
        NULL::INTEGER as campaign_id,
        NULL::TEXT as website,
        NULL::TEXT as country,
        MIN(min_event_date) as min_event_date,
        MAX(max_event_date) as max_event_date,
        COUNT(DISTINCT external_user_id) as paying_users,
        SUM(deposit_count) as total_deposits,
        SUM(total_deposits_usd) as total_revenue_usd,
        CASE 
            WHEN COUNT(DISTINCT external_user_id) > 0 
            THEN SUM(total_deposits_usd) / COUNT(DISTINCT external_user_id)
            ELSE 0
        END as arppu_usd,
        CASE 
            WHEN COUNT(DISTINCT external_user_id) > 0 
            THEN SUM(deposit_count)::NUMERIC / COUNT(DISTINCT external_user_id)
            ELSE 0
        END as avg_deposits_per_user
    FROM user_totals
    WHERE publisher_id IS NOT NULL AND publisher_id != 0  -- Только атрибутированные
    GROUP BY brand, publisher_id
),

arppu_by_format AS (
    SELECT 
        'Format' as breakdown_type,
        brand,
        NULL::TEXT as breakdown_value,
        format,
        NULL::INTEGER as campaign_id,
        NULL::TEXT as website,
        NULL::TEXT as country,
        MIN(min_event_date) as min_event_date,
        MAX(max_event_date) as max_event_date,
        COUNT(DISTINCT external_user_id) as paying_users,
        SUM(deposit_count) as total_deposits,
        SUM(total_deposits_usd) as total_revenue_usd,
        CASE 
            WHEN COUNT(DISTINCT external_user_id) > 0 
            THEN SUM(total_deposits_usd) / COUNT(DISTINCT external_user_id)
            ELSE 0
        END as arppu_usd,
        CASE 
            WHEN COUNT(DISTINCT external_user_id) > 0 
            THEN SUM(deposit_count)::NUMERIC / COUNT(DISTINCT external_user_id)
            ELSE 0
        END as avg_deposits_per_user
    FROM user_totals
    WHERE format IS NOT NULL
    GROUP BY brand, format
),

arppu_by_campaign AS (
    SELECT 
        'Campaign' as breakdown_type,
        brand,
        campaign_id::TEXT as breakdown_value,
        NULL::TEXT as format,
        campaign_id,
        NULL::TEXT as website,
        NULL::TEXT as country,
        MIN(min_event_date) as min_event_date,
        MAX(max_event_date) as max_event_date,
        COUNT(DISTINCT external_user_id) as paying_users,
        SUM(deposit_count) as total_deposits,
        SUM(total_deposits_usd) as total_revenue_usd,
        CASE 
            WHEN COUNT(DISTINCT external_user_id) > 0 
            THEN SUM(total_deposits_usd) / COUNT(DISTINCT external_user_id)
            ELSE 0
        END as arppu_usd,
        CASE 
            WHEN COUNT(DISTINCT external_user_id) > 0 
            THEN SUM(deposit_count)::NUMERIC / COUNT(DISTINCT external_user_id)
            ELSE 0
        END as avg_deposits_per_user
    FROM user_totals
    WHERE campaign_id IS NOT NULL AND campaign_id != 0
    GROUP BY brand, campaign_id
),

arppu_by_site AS (
    SELECT 
        'Site' as breakdown_type,
        brand,
        website as breakdown_value,
        NULL::TEXT as format,
        NULL::INTEGER as campaign_id,
        website,
        NULL::TEXT as country,
        MIN(min_event_date) as min_event_date,
        MAX(max_event_date) as max_event_date,
        COUNT(DISTINCT external_user_id) as paying_users,
        SUM(deposit_count) as total_deposits,
        SUM(total_deposits_usd) as total_revenue_usd,
        CASE 
            WHEN COUNT(DISTINCT external_user_id) > 0 
            THEN SUM(total_deposits_usd) / COUNT(DISTINCT external_user_id)
            ELSE 0
        END as arppu_usd,
        CASE 
            WHEN COUNT(DISTINCT external_user_id) > 0 
            THEN SUM(deposit_count)::NUMERIC / COUNT(DISTINCT external_user_id)
            ELSE 0
        END as avg_deposits_per_user
    FROM user_totals
    WHERE website IS NOT NULL
    GROUP BY brand, website
),

arppu_by_region AS (
    SELECT 
        'Region' as breakdown_type,
        brand,
        country as breakdown_value,
        NULL::TEXT as format,
        NULL::INTEGER as campaign_id,
        NULL::TEXT as website,
        country,
        MIN(min_event_date) as min_event_date,
        MAX(max_event_date) as max_event_date,
        COUNT(DISTINCT external_user_id) as paying_users,
        SUM(deposit_count) as total_deposits,
        SUM(total_deposits_usd) as total_revenue_usd,
        CASE 
            WHEN COUNT(DISTINCT external_user_id) > 0 
            THEN SUM(total_deposits_usd) / COUNT(DISTINCT external_user_id)
            ELSE 0
        END as arppu_usd,
        CASE 
            WHEN COUNT(DISTINCT external_user_id) > 0 
            THEN SUM(deposit_count)::NUMERIC / COUNT(DISTINCT external_user_id)
            ELSE 0
        END as avg_deposits_per_user
    FROM user_totals
    WHERE country IS NOT NULL
    GROUP BY brand, country
),

-- Все пользователи (без разбивки по атрибуции, включая неатрибутированных)
all_deposits AS (
    SELECT 
        ue.external_user_id,
        ue.event_date,
        ue.website,
        ue.country,
        ue.converted_amount,
        -- Определяем бренд по advertiser (если NULL, используем website как fallback)
        COALESCE(
            ue.advertiser,
            CASE 
                WHEN ue.website ILIKE '%crorebet%' OR ue.website ILIKE '%crore%' THEN 'Crorebet'
                WHEN ue.website ILIKE '%4rabet%' OR ue.website ILIKE '%4ra%' THEN '4rabet'
                ELSE 'Unknown'
            END
        ) as brand
    FROM public.user_events ue
    WHERE ue.event_type = 'deposit'
      AND ue.converted_amount > 0
      AND ue.external_user_id IS NOT NULL
),

all_user_totals AS (
    SELECT 
        external_user_id,
        brand,
        MIN(event_date) as min_event_date,
        MAX(event_date) as max_event_date,
        COUNT(*) as deposit_count,
        SUM(converted_amount) as total_deposits_usd
    FROM all_deposits
    GROUP BY external_user_id, brand
),

arppu_all_users AS (
    SELECT 
        'All users' as breakdown_type,
        brand,
        'All' as breakdown_value,
        NULL::TEXT as format,
        NULL::INTEGER as campaign_id,
        NULL::TEXT as website,
        NULL::TEXT as country,
        MIN(min_event_date) as min_event_date,
        MAX(max_event_date) as max_event_date,
        COUNT(DISTINCT external_user_id) as paying_users,
        SUM(deposit_count) as total_deposits,
        SUM(total_deposits_usd) as total_revenue_usd,
        CASE 
            WHEN COUNT(DISTINCT external_user_id) > 0 
            THEN SUM(total_deposits_usd) / COUNT(DISTINCT external_user_id)
            ELSE 0
        END as arppu_usd,
        CASE 
            WHEN COUNT(DISTINCT external_user_id) > 0 
            THEN SUM(deposit_count)::NUMERIC / COUNT(DISTINCT external_user_id)
            ELSE 0
        END as avg_deposits_per_user
    FROM all_user_totals
    GROUP BY brand
)

-- Объединяем все разбивки
SELECT 
    breakdown_type,
    brand,
    breakdown_value,
    format,
    campaign_id,
    website,
    country,
    min_event_date,
    max_event_date,
    paying_users,
    total_deposits,
    ROUND(total_revenue_usd::NUMERIC, 2) as total_revenue_usd,
    ROUND(arppu_usd::NUMERIC, 2) as arppu_usd,
    ROUND(avg_deposits_per_user::NUMERIC, 2) as avg_deposits_per_user
FROM (
    SELECT * FROM arppu_by_publisher
    UNION ALL
    SELECT * FROM arppu_by_format
    UNION ALL
    SELECT * FROM arppu_by_campaign
    UNION ALL
    SELECT * FROM arppu_by_site
    UNION ALL
    SELECT * FROM arppu_by_region
    UNION ALL
    SELECT * FROM arppu_all_users
) combined
ORDER BY 
    brand,
    breakdown_type,
    arppu_usd DESC;

