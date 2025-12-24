-- Сводная таблица: Сравнение атрибуций 1 HOUR и 24 HOURS
-- Показывает данные для обоих типов атрибуции в одной таблице для сравнения
-- Группирует по кампаниям: одна запись на кампанию с суммой всех показателей за период
-- 
-- Для использования:
-- 1. Создайте Dataset на основе этого запроса
-- 2. Создайте метрики в Superset (см. GOOGLE_SHEETS_METRICS_SETUP.md)
-- 3. Используйте в Chart для сравнения эффективности разных типов атрибуции
-- 4. Group by: campaign_name, attribution_type
-- 5. Используйте фильтр по дате на Dashboard для выбора периода

SELECT 
    attribution_type,  -- '1_hour' или '24_hours'
    campaign_name,
    campaignid,
    format,  -- Оставляем для возможной фильтрации, но не группируем по нему
    
    -- Базовые метрики (суммируем за весь период)
    COUNT(*) as records_count,
    SUM(COALESCE(views, 0)) as total_views,
    SUM(COALESCE(clicks, 0)) as total_clicks,
    
    -- Очищаем и суммируем spend
    SUM(
        CASE 
            WHEN spend IS NULL OR spend = '' OR TRIM(spend) = '' THEN 0
            ELSE CAST(REPLACE(REPLACE(TRIM(spend), ',', '.'), ' ', '') AS NUMERIC)
        END
    ) as total_spend,
    
    SUM(COALESCE(postview, 0)) as total_postview,
    SUM(COALESCE(postclick, 0)) as total_postclick,
    
    -- Очищаем CPA поля (средние значения)
    AVG(
        CASE 
            WHEN cpa_pv IS NULL OR cpa_pv = '' OR TRIM(cpa_pv) = '' OR LOWER(TRIM(cpa_pv)) = 'inf' THEN NULL
            ELSE CAST(REPLACE(REPLACE(TRIM(cpa_pv), ',', '.'), ' ', '') AS NUMERIC)
        END
    ) as avg_cpa_pv,
    
    AVG(
        CASE 
            WHEN cpa_pc IS NULL OR cpa_pc = '' OR TRIM(cpa_pc) = '' OR LOWER(TRIM(cpa_pc)) = 'inf' THEN NULL
            ELSE CAST(REPLACE(REPLACE(TRIM(cpa_pc), ',', '.'), ' ', '') AS NUMERIC)
        END
    ) as avg_cpa_pc,
    
    -- Диапазон дат для фильтрации на Dashboard
    MIN(DATE(event_date)) as min_date,
    MAX(DATE(event_date)) as max_date

FROM google_sheets_campaigns
WHERE event_date IS NOT NULL
  AND campaign_name IS NOT NULL
  AND attribution_type IN ('1_hour', '24_hours')  -- Оба типа атрибуции
GROUP BY 
    attribution_type,  -- Группируем по типу атрибуции (для сравнения 1h vs 24h)
    campaign_name,
    campaignid,
    format  -- Оставляем format для возможной фильтрации, но данные агрегируются по кампании
ORDER BY 
    attribution_type,
    total_spend DESC NULLS LAST;

