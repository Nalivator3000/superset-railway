-- Запрос для атрибуции 1 HOUR
-- Только данные с attribution_type = '1_hour'
-- 
-- Для использования:
-- 1. Создайте Dataset на основе этого запроса
-- 2. Создайте метрики в Superset (см. GOOGLE_SHEETS_METRICS_SETUP.md)
-- 3. Используйте в Chart для анализа данных с атрибуцией 1 час

SELECT 
    DATE(event_date) as event_date,
    format,
    campaign_name,
    campaignid,
    event_type,
    source_sheet_id,
    
    -- Базовые метрики
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
    
    -- Очищаем CPA поля
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
    ) as avg_cpa_pc

FROM google_sheets_campaigns
WHERE event_date IS NOT NULL
  AND campaign_name IS NOT NULL
  AND attribution_type = '1_hour'  -- ТОЛЬКО 1 HOUR
GROUP BY 
    DATE(event_date),
    format,
    campaign_name,
    campaignid,
    event_type,
    source_sheet_id
ORDER BY 
    event_date DESC,
    total_spend DESC NULLS LAST;

