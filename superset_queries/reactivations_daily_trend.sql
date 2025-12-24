-- Отчет: Тренд реактиваций по дням с группировкой по периодам неактивности
-- Использует материализованное представление для быстрой работы
-- БЕЗ параметров - используйте фильтры Dashboard для выбора периода
-- 
-- ВАЖНО: Перед использованием создайте материализованное представление:
--   python 07_scripts/create_reactivations_materialized_view.py
-- 
-- Для использования:
-- 1. Создайте Chart на основе этого запроса
-- 2. Добавьте фильтры на Dashboard:
--    - Time Range фильтр для reactivation_date (дата реактивации)
-- 3. Примените фильтры к Chart через Scoping
-- 4. В Chart Builder:
--    - Dimensions: reactivation_date (группировка по дате) и inactivity_period (для разных линий)
--    - Metrics: reactivations_count (COUNT)
--    - Визуализация: Line Chart (для тренда по дням)
--
-- Визуализация:
-- - Line Chart: несколько линий (по одной для каждого периода неактивности)
-- - X-axis: reactivation_date (дата)
-- - Y-axis: reactivations_count (количество реактиваций)
-- - Series: inactivity_period (7-14 days, 14-30 days, 30-90 days, 90+ days)

-- Используем материализованное представление для быстрого доступа ко всем реактивациям
-- Группируем по дате и периоду неактивности для построения тренда
SELECT
    DATE(first_deposit) as reactivation_date,  -- Дата реактивации (для оси X)
    inactivity_period,  -- Категория периода неактивности (для разных линий на графике)
    COUNT(*) as reactivations_count  -- Количество реактиваций за день
FROM reactivations_materialized
GROUP BY 
    DATE(first_deposit),
    inactivity_period
ORDER BY 
    reactivation_date,
    inactivity_period;

