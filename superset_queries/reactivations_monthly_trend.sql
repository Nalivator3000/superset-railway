-- Отчет: Тренд реактиваций по месяцам с группировкой по периодам неактивности
-- Использует материализованное представление для быстрой работы
-- БЕЗ параметров - используйте фильтры Dashboard для выбора периода
-- 
-- ВАЖНО: Перед использованием создайте материализованное представление:
--   python 07_scripts/create_reactivations_materialized_view.py
-- 
-- Для использования:
-- 1. Создайте Chart на основе этого запроса
-- 2. Добавьте фильтры на Dashboard:
--    - Time Range фильтр для month_start (начало месяца)
-- 3. Примените фильтры к Chart через Scoping
-- 4. В Chart Builder:
--    - Dimensions: month_start (группировка по месяцу) и inactivity_period (для разных линий)
--    - Metrics: reactivations_count (SUM)
--    - Визуализация: Line Chart (для тренда по месяцам)
--
-- Визуализация:
-- - Line Chart: несколько линий (по одной для каждого периода неактивности)
-- - X-axis: month_start (начало месяца)
-- - Y-axis: reactivations_count (количество реактиваций)
-- - Series: inactivity_period (7-14 days, 14-30 days, 30-90 days, 90+ days)

-- Используем материализованное представление для быстрого доступа ко всем реактивациям
-- Группируем по месяцу и периоду неактивности для построения тренда
SELECT
    DATE_TRUNC('month', first_deposit)::date as month_start,  -- Начало месяца (для оси X)
    inactivity_period,  -- Категория периода неактивности (для разных линий на графике)
    COUNT(*) as reactivations_count  -- Количество реактиваций за месяц
FROM reactivations_materialized
GROUP BY 
    DATE_TRUNC('month', first_deposit),
    inactivity_period
ORDER BY 
    month_start,
    inactivity_period;

