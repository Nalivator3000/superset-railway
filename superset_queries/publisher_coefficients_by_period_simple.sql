-- Упрощенный отчет: Коэффициенты паблишеров с выбором периода
-- БЕЗ параметров - используйте фильтры Dashboard для выбора периода
-- 
-- Для использования:
-- 1. Создайте Chart на основе этого запроса
-- 2. Добавьте фильтры на Dashboard:
--    - Select/Dropdown фильтр для month (выбор месяца)
--    - Select/Dropdown фильтр для brand (4rabet / Crorebet / All)
--    - Numeric фильтр для spend (минимальный spend)
--    - Numeric фильтр для current_cpa (максимальный CPA)
-- 3. Примените фильтры к Chart через Scoping
--
-- Разделение по брендам:
-- - Определяется по advertiser из user_events (связь по publisher_id и месяцу)
-- - До 2 декабря 2025: все записи относятся к 4rabet
-- - С 2 декабря 2025: разделение на 4rabet и Crorebet

WITH 
-- 1. Определяем advertiser для каждого паблишера по месяцу (из user_events)
publisher_advertiser AS (
    SELECT 
        publisher_id,
        month,
        advertiser
    FROM (
        SELECT 
            ps.publisher_id,
            ps.month,
            ue.advertiser,
            COUNT(*) as cnt,
            ROW_NUMBER() OVER (PARTITION BY ps.publisher_id, ps.month ORDER BY COUNT(*) DESC) as rn
        FROM publisher_spend ps
        INNER JOIN public.user_events ue 
            ON ue.publisher_id = ps.publisher_id
            AND DATE_TRUNC('month', ue.event_date) = TO_DATE(ps.month || '-01', 'YYYY-MM-DD')
        WHERE ps.publisher_id != 0
          AND ue.advertiser IS NOT NULL
        GROUP BY ps.publisher_id, ps.month, ue.advertiser
    ) ranked
    WHERE rn = 1  -- Берем самый частый advertiser
),

-- 2. Получаем данные о расходах с advertiser (фильтры применяются на уровне Dashboard)
period_spend AS (
    SELECT 
        ps.publisher_id,
        ps.publisher_name,
        ps.format,
        ps.month,
        ps.deposits_reported,
        ps.spend,
        ps.current_cpa,
        -- Определяем бренд по advertiser (если нет в publisher_advertiser, используем fallback)
        COALESCE(
            pa.advertiser,
            CASE 
                WHEN ps.month < '2025-12' THEN '4rabet'  -- До декабря все 4rabet
                ELSE 'Unknown'
            END
        ) as brand
    FROM publisher_spend ps
    LEFT JOIN publisher_advertiser pa
        ON ps.publisher_id = pa.publisher_id
        AND ps.month = pa.month
    WHERE ps.publisher_id != 0  -- Исключаем органику
),

-- 3. Находим PLR/NOR кампании за период (с учетом бренда)
plr_nor AS (
    SELECT 
        format,
        brand,
        SUM(spend) as total_spend,
        SUM(deposits_reported) as total_deposits,
        CASE 
            WHEN SUM(deposits_reported) > 0 
            THEN SUM(spend) / SUM(deposits_reported) 
            ELSE 0 
        END as avg_cpa
    FROM period_spend
    WHERE UPPER(publisher_name) LIKE '%PLR%' 
       OR UPPER(publisher_name) LIKE '%NOR%'
    GROUP BY format, brand
),

-- 4. Рассчитываем целевые CPA по форматам и брендам (-30% от PLR/NOR)
target_cpa_by_format AS (
    -- Сначала берем из PLR/NOR
    SELECT 
        format,
        brand,
        CASE 
            WHEN avg_cpa > 0 THEN avg_cpa * 0.7
            ELSE NULL
        END as target_cpa
    FROM plr_nor
    WHERE avg_cpa > 0
    
    UNION
    
    -- Если нет PLR/NOR для формата+бренда, используем среднее по всем кампаниям формата+бренда
    SELECT 
        ps.format,
        ps.brand,
        CASE 
            WHEN SUM(ps.deposits_reported) > 0 
            THEN (SUM(ps.spend) / SUM(ps.deposits_reported)) * 0.7
            ELSE NULL
        END as target_cpa
    FROM period_spend ps
    WHERE (ps.format, ps.brand) NOT IN (
        SELECT format, brand FROM plr_nor WHERE avg_cpa > 0
    )
    GROUP BY ps.format, ps.brand
)

-- 5. Рассчитываем коэффициенты для каждого паблишера
SELECT 
    ps.publisher_id,
    ps.publisher_name,
    ps.format,
    ps.month,
    ps.brand,
    COALESCE(tc.target_cpa, 0) as target_cpa_format,
    ps.current_cpa,
    ps.spend,
    ps.deposits_reported,
    -- Коэффициент = Target CPA / Current CPA
    CASE 
        WHEN ps.current_cpa > 0 AND COALESCE(tc.target_cpa, 0) > 0 
        THEN LEAST(GREATEST(COALESCE(tc.target_cpa, 0) / ps.current_cpa, 0.1), 3.0)
        ELSE 1.0
    END as coefficient,
    -- Процент изменения
    CASE 
        WHEN ps.current_cpa > 0 AND COALESCE(tc.target_cpa, 0) > 0 
        THEN ((LEAST(GREATEST(COALESCE(tc.target_cpa, 0) / ps.current_cpa, 0.1), 3.0) - 1) * 100)
        ELSE 0
    END as change_pct,
    -- Рекомендация
    CASE 
        WHEN ps.current_cpa > 0 AND COALESCE(tc.target_cpa, 0) > 0 THEN
            CASE 
                WHEN LEAST(GREATEST(COALESCE(tc.target_cpa, 0) / ps.current_cpa, 0.1), 3.0) >= 1.3 THEN 'УВЕЛИЧИТЬ ставку'
                WHEN LEAST(GREATEST(COALESCE(tc.target_cpa, 0) / ps.current_cpa, 0.1), 3.0) >= 1.1 THEN 'Увеличить немного'
                WHEN LEAST(GREATEST(COALESCE(tc.target_cpa, 0) / ps.current_cpa, 0.1), 3.0) >= 0.9 THEN 'Оставить'
                WHEN LEAST(GREATEST(COALESCE(tc.target_cpa, 0) / ps.current_cpa, 0.1), 3.0) >= 0.7 THEN 'Снизить немного'
                WHEN LEAST(GREATEST(COALESCE(tc.target_cpa, 0) / ps.current_cpa, 0.1), 3.0) >= 0.4 THEN 'СНИЗИТЬ ставку'
                ELSE 'отключить паблишера'
            END
        ELSE 'Нет данных'
    END as recommendation
FROM period_spend ps
LEFT JOIN target_cpa_by_format tc
    ON ps.format = tc.format
    AND ps.brand = tc.brand
ORDER BY ps.brand, ps.format, ps.month, coefficient DESC;

