-- Отчет: Анализ рекламных кампаний из Google Sheets
-- БЕЗ параметров - используйте фильтры Dashboard для выбора периода и других параметров
-- 
-- Для использования:
-- 1. Создайте Chart на основе этого запроса
-- 2. Добавьте фильтры на Dashboard:
--    - Time Range фильтр для event_date (дата события)
--    - Select фильтр для attribution_type (1_hour / 24_hours)
--    - Select фильтр для format (banner, push, native, teaser и т.д.)
--    - Select фильтр для campaign_name (выбор кампаний)
--    - Select фильтр для event_type (ftd, rd)
--    - Numeric фильтр для spend (минимальный spend)
-- 3. Примените фильтры к Chart через Scoping
-- 4. В Chart Builder:
--    - Dimensions: campaign_name, format, event_date, event_type (в зависимости от нужной группировки)
--    - Metrics: total_spend, total_clicks, total_views, avg_cpa_pv, avg_cpa_pc
--    - Визуализация: Table, Bar Chart, Line Chart (в зависимости от задачи)

WITH cleaned_data AS (
    SELECT 
        source_sheet_id,
        attribution_type,
        campaignid,
        event_date,
        campaign_name,
        event_type,
        format,
        views,
        clicks,
        -- Очищаем spend от запятых и конвертируем в NUMERIC
        CASE 
            WHEN spend IS NULL OR spend = '' OR TRIM(spend) = '' THEN 0
            ELSE CAST(REPLACE(REPLACE(TRIM(spend), ',', '.'), ' ', '') AS NUMERIC)
        END as spend,
        postview,
        postclick,
        -- Очищаем CPA_PV от запятых и конвертируем в NUMERIC
        CASE 
            WHEN cpa_pv IS NULL OR cpa_pv = '' OR TRIM(cpa_pv) = '' OR LOWER(TRIM(cpa_pv)) = 'inf' THEN NULL
            ELSE CAST(REPLACE(REPLACE(TRIM(cpa_pv), ',', '.'), ' ', '') AS NUMERIC)
        END as cpa_pv,
        -- Очищаем CPA_PC от запятых и конвертируем в NUMERIC
        CASE 
            WHEN cpa_pc IS NULL OR cpa_pc = '' OR TRIM(cpa_pc) = '' OR LOWER(TRIM(cpa_pc)) = 'inf' THEN NULL
            ELSE CAST(REPLACE(REPLACE(TRIM(cpa_pc), ',', '.'), ' ', '') AS NUMERIC)
        END as cpa_pc,
        -- Очищаем Total Spend
        CASE 
            WHEN total_spend IS NULL OR total_spend = '' OR TRIM(total_spend) = '' THEN NULL
            ELSE CAST(REPLACE(REPLACE(TRIM(total_spend), ',', '.'), ' ', '') AS NUMERIC)
        END as total_spend,
        -- Очищаем Total CPA
        CASE 
            WHEN total_cpa IS NULL OR total_cpa = '' OR TRIM(total_cpa) = '' THEN NULL
            ELSE CAST(REPLACE(REPLACE(TRIM(total_cpa), ',', '.'), ' ', '') AS NUMERIC)
        END as total_cpa
    FROM google_sheets_campaigns
    WHERE event_date IS NOT NULL
      AND campaign_name IS NOT NULL
)

SELECT 
    -- Измерения для группировки
    DATE(event_date) as event_date,
    attribution_type,
    format,
    campaign_name,
    campaignid,
    event_type,
    source_sheet_id,
    
    -- Метрики
    COUNT(*) as records_count,
    SUM(COALESCE(views, 0)) as total_views,
    SUM(COALESCE(clicks, 0)) as total_clicks,
    SUM(COALESCE(spend, 0)) as total_spend,
    SUM(COALESCE(postview, 0)) as total_postview,
    SUM(COALESCE(postclick, 0)) as total_postclick,
    
    -- Средние значения (используем NULLIF для безопасного деления)
    CASE 
        WHEN SUM(COALESCE(clicks, 0)) > 0 
        THEN ROUND(SUM(spend)::NUMERIC / NULLIF(SUM(COALESCE(clicks, 0)), 0), 2)
        ELSE NULL
    END as cpc,  -- Cost Per Click
    
    CASE 
        WHEN SUM(COALESCE(views, 0)) > 0 
        THEN ROUND(SUM(spend)::NUMERIC / NULLIF(SUM(COALESCE(views, 0)), 0) * 1000, 2)
        ELSE NULL
    END as cpm,  -- Cost Per Mille (на 1000 показов)
    
    CASE 
        WHEN SUM(COALESCE(clicks, 0)) > 0 
        THEN ROUND(SUM(COALESCE(views, 0))::NUMERIC / NULLIF(SUM(COALESCE(clicks, 0)), 0), 2)
        ELSE NULL
    END as ctr,  -- Click Through Rate (views/clicks)
    
    -- Средние CPA (только для не-NULL значений)
    ROUND(AVG(CASE WHEN cpa_pv IS NOT NULL THEN cpa_pv END), 2) as avg_cpa_pv,
    ROUND(AVG(CASE WHEN cpa_pc IS NOT NULL THEN cpa_pc END), 2) as avg_cpa_pc,
    
    -- Total Spend и Total CPA (если есть)
    SUM(COALESCE(total_spend, 0)) as total_spend_aggregated,
    ROUND(AVG(CASE WHEN total_cpa IS NOT NULL THEN total_cpa END), 2) as avg_total_cpa,
    
    -- Конверсии (рассчитанные CPA)
    CASE 
        WHEN SUM(COALESCE(postview, 0)) > 0 
        THEN ROUND(SUM(spend)::NUMERIC / NULLIF(SUM(COALESCE(postview, 0)), 0), 2)
        ELSE NULL
    END as calculated_cpa_pv,  -- Рассчитанный CPA PostView
    
    CASE 
        WHEN SUM(COALESCE(postclick, 0)) > 0 
        THEN ROUND(SUM(spend)::NUMERIC / NULLIF(SUM(COALESCE(postclick, 0)), 0), 2)
        ELSE NULL
    END as calculated_cpa_pc  -- Рассчитанный CPA PostClick

FROM cleaned_data
GROUP BY 
    DATE(event_date),
    attribution_type,
    format,
    campaign_name,
    campaignid,
    event_type,
    source_sheet_id
ORDER BY 
    event_date DESC,
    attribution_type,
    format,
    campaign_name;

