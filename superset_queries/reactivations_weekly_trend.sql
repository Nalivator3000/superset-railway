-- Отчет: Тренд реактиваций по неделям с группировкой по периодам неактивности
-- Использует материализованное представление для быстрой работы
-- БЕЗ параметров - используйте фильтры Dashboard для выбора периода
-- 
-- ВАЖНО: Перед использованием создайте материализованное представление:
--   python 07_scripts/create_reactivations_materialized_view.py
-- 
-- Для использования:
-- 1. Создайте Chart на основе этого запроса
-- 2. Добавьте фильтры на Dashboard:
--    - Time Range фильтр для week_start (начало недели)
-- 3. Примените фильтры к Chart через Scoping
-- 4. В Chart Builder:
--    - Dimensions: week_start (группировка по неделе) и inactivity_period (для разных линий)
--    - Metrics: reactivations_count (SUM)
--    - Визуализация: Line Chart (для тренда по неделям)
--
-- Визуализация:
-- - Line Chart: несколько линий (по одной для каждого периода неактивности)
-- - X-axis: week_start (начало недели)
-- - Y-axis: reactivations_count (количество реактиваций)
-- - Series: inactivity_period (7-14 days, 14-30 days, 30-90 days, 90+ days)

-- Используем материализованное представление для быстрого доступа ко всем реактивациям
-- Группируем по неделе и периоду неактивности для построения тренда
SELECT
    DATE_TRUNC('week', first_deposit)::date as week_start,  -- Начало недели (для оси X)
    inactivity_period,  -- Категория периода неактивности (для разных линий на графике)
    COUNT(*) as reactivations_count  -- Количество реактиваций за неделю
FROM reactivations_materialized
GROUP BY 
    DATE_TRUNC('week', first_deposit),
    inactivity_period
ORDER BY 
    week_start,
    inactivity_period;

