-- Упрощенный отчет: Анализ рекламных кампаний из Google Sheets
-- БЕЗ параметров - используйте фильтры Dashboard для выбора периода
-- 
-- Для использования:
-- 1. Создайте Chart на основе этого запроса
-- 2. Добавьте фильтры на Dashboard:
--    - Time Range фильтр для event_date
--    - Select фильтр для attribution_type (1_hour / 24_hours)
--    - Select фильтр для format (banner, push, native, teaser)
--    - Select фильтр для campaign_name
-- 3. В Chart Builder:
--    - Dimensions: campaign_name, format, event_date (выберите нужную группировку)
--    - Metrics: total_spend, total_clicks, total_views, ctr, cpc
--    - Визуализация: Table, Bar Chart, Line Chart

SELECT 
    DATE(event_date) as event_date,
    attribution_type,
    format,
    campaign_name,
    campaignid,
    event_type,
    
    COUNT(*) as records_count,
    SUM(COALESCE(views, 0)) as total_views,
    SUM(COALESCE(clicks, 0)) as total_clicks,
    
    -- Очищаем и суммируем spend (запятые заменяем на точки)
    SUM(
        CASE 
            WHEN spend IS NULL OR spend = '' OR spend = ' ' THEN 0
            ELSE CAST(REPLACE(REPLACE(TRIM(spend), ',', '.'), ' ', '') AS NUMERIC)
        END
    ) as total_spend,
    
    SUM(COALESCE(postview, 0)) as total_postview,
    SUM(COALESCE(postclick, 0)) as total_postclick,
    
    -- Рассчитанные метрики
    CASE 
        WHEN SUM(COALESCE(clicks, 0)) > 0 
        THEN ROUND(
            SUM(CASE 
                WHEN spend IS NULL OR spend = '' OR spend = ' ' THEN 0
                ELSE CAST(REPLACE(REPLACE(TRIM(spend), ',', '.'), ' ', '') AS NUMERIC)
            END)::NUMERIC / NULLIF(SUM(COALESCE(clicks, 0)), 0), 2
        )
        ELSE NULL
    END as cpc,
    
    CASE 
        WHEN SUM(COALESCE(views, 0)) > 0 
        THEN ROUND(
            SUM(CASE 
                WHEN spend IS NULL OR spend = '' OR spend = ' ' THEN 0
                ELSE CAST(REPLACE(REPLACE(TRIM(spend), ',', '.'), ' ', '') AS NUMERIC)
            END)::NUMERIC / NULLIF(SUM(COALESCE(views, 0)), 0) * 1000, 2
        )
        ELSE NULL
    END as cpm,
    
    CASE 
        WHEN SUM(COALESCE(clicks, 0)) > 0 
        THEN ROUND(SUM(COALESCE(views, 0))::NUMERIC / NULLIF(SUM(COALESCE(clicks, 0)), 0), 2)
        ELSE NULL
    END as ctr,
    
    CASE 
        WHEN SUM(COALESCE(postview, 0)) > 0 
        THEN ROUND(
            SUM(CASE 
                WHEN spend IS NULL OR spend = '' OR spend = ' ' THEN 0
                ELSE CAST(REPLACE(REPLACE(TRIM(spend), ',', '.'), ' ', '') AS NUMERIC)
            END)::NUMERIC / NULLIF(SUM(COALESCE(postview, 0)), 0), 2
        )
        ELSE NULL
    END as cpa_pv

FROM google_sheets_campaigns
WHERE event_date IS NOT NULL
  AND campaign_name IS NOT NULL
GROUP BY 
    DATE(event_date),
    attribution_type,
    format,
    campaign_name,
    campaignid,
    event_type
ORDER BY 
    event_date DESC,
    total_spend DESC NULLS LAST;

