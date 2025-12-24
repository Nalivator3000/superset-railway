-- Упрощенный отчет: ARPPU по бренду 4rabet с группировкой по дате
-- Оптимизированная версия для быстрого выполнения на больших объемах данных
-- БЕЗ параметров - используйте фильтры Dashboard для выбора периода
-- 
-- Для использования:
-- 1. Создайте Chart на основе этого запроса
-- 2. Добавьте фильтры на Dashboard:
--    - Time Range фильтр для event_date (дата депозита)
-- 3. Примените фильтры к Chart через Scoping
-- 4. В Chart Builder:
--    - Dimensions: event_date (группировка по дате)
--    - Metrics: arppu_usd (AVG)
--    - Визуализация: Line Chart

-- Оптимизированный запрос: один проход по данным, минимум агрегаций
SELECT 
    DATE(ue.event_date) as event_date,
    CASE 
        WHEN COUNT(DISTINCT ue.external_user_id) > 0 
        THEN ROUND(SUM(ue.converted_amount)::NUMERIC / COUNT(DISTINCT ue.external_user_id), 2)
        ELSE 0
    END as arppu_usd
FROM public.user_events ue
WHERE ue.event_type = 'deposit'
  AND ue.converted_amount > 0
  AND ue.external_user_id IS NOT NULL
  AND ue.advertiser = '4rabet'
GROUP BY DATE(ue.event_date)
ORDER BY event_date;

