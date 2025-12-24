# Идеи для дополнительных инсайтов из данных БД

## 📊 Уже реализованные отчеты:
- ✅ Реактивации по периодам неактивности (daily/weekly/monthly)
- ✅ ARPPU по различным атрибутам (publisher, format, campaign, site, region)
- ✅ Коэффициенты паблишеров (bid coefficients)
- ✅ Сравнение кампаний Google Sheets (1h vs 24h атрибуция)

---

## 🎯 Рекомендуемые дополнительные инсайты:

### 1. **Анализ Retention (Удержание пользователей)**

**Что показывает:**
- Процент пользователей, которые делают повторные депозиты
- Retention по периодам (Day 1, Day 7, Day 30)
- Сравнение retention по паблишерам/форматам/кампаниям

**SQL структура:**
```sql
-- Retention по дням (сколько пользователей вернулись через N дней)
WITH first_deposit AS (
    SELECT 
        external_user_id,
        MIN(event_date) as first_deposit_date
    FROM user_events
    WHERE event_type = 'deposit'
    GROUP BY external_user_id
),
user_deposits AS (
    SELECT 
        ue.external_user_id,
        ue.event_date,
        fd.first_deposit_date,
        DATE_PART('day', ue.event_date - fd.first_deposit_date) as days_since_first
    FROM user_events ue
    JOIN first_deposit fd ON ue.external_user_id = fd.external_user_id
    WHERE ue.event_type = 'deposit'
)
SELECT 
    days_since_first,
    COUNT(DISTINCT external_user_id) as returning_users
FROM user_deposits
WHERE days_since_first > 0
GROUP BY days_since_first
ORDER BY days_since_first;
```

**Применение:**
- Понимание, какие источники трафика приносят более "лояльных" пользователей
- Оптимизация маркетинговых кампаний для улучшения retention

---

### 2. **Анализ LTV (Lifetime Value) по источникам**

**Что показывает:**
- Средний LTV пользователей по паблишерам/форматам/кампаниям
- Сравнение LTV разных источников трафика
- Прогнозирование долгосрочной ценности пользователя

**SQL структура:**
```sql
-- LTV по паблишерам
WITH user_lifetime AS (
    SELECT 
        ue.external_user_id,
        ue.publisher_id,
        MIN(ue.event_date) as first_deposit_date,
        MAX(ue.event_date) as last_deposit_date,
        COUNT(*) as total_deposits,
        SUM(ue.converted_amount) as total_revenue
    FROM user_events ue
    WHERE ue.event_type = 'deposit'
      AND ue.publisher_id IS NOT NULL
      AND ue.publisher_id != 0
    GROUP BY ue.external_user_id, ue.publisher_id
)
SELECT 
    publisher_id,
    COUNT(DISTINCT external_user_id) as users,
    AVG(total_revenue) as avg_ltv,
    AVG(total_deposits) as avg_deposits_per_user,
    AVG(EXTRACT(EPOCH FROM (last_deposit_date - first_deposit_date)) / 86400) as avg_lifetime_days
FROM user_lifetime
GROUP BY publisher_id
ORDER BY avg_ltv DESC;
```

**Применение:**
- Определение наиболее ценных источников трафика
- Оптимизация бюджета на основе LTV, а не только CPA

---

### 3. **Анализ времени до первого депозита (Time to First Deposit)**

**Что показывает:**
- Сколько времени проходит от регистрации до первого депозита
- Сравнение по источникам трафика
- Оптимизация воронки конверсии

**SQL структура:**
```sql
-- Время до первого депозита
WITH first_events AS (
    SELECT 
        external_user_id,
        MIN(event_date) as first_event_date
    FROM user_events
    WHERE external_user_id IS NOT NULL
    GROUP BY external_user_id
),
first_deposits AS (
    SELECT 
        ue.external_user_id,
        ue.publisher_id,
        ue.event_date as first_deposit_date,
        fe.first_event_date
    FROM user_events ue
    JOIN first_events fe ON ue.external_user_id = fe.external_user_id
    WHERE ue.event_type = 'deposit'
      AND ue.event_date = (
          SELECT MIN(event_date) 
          FROM user_events 
          WHERE external_user_id = ue.external_user_id 
            AND event_type = 'deposit'
      )
)
SELECT 
    publisher_id,
    COUNT(*) as users,
    AVG(EXTRACT(EPOCH FROM (first_deposit_date - first_event_date)) / 3600) as avg_hours_to_deposit,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (first_deposit_date - first_event_date)) / 3600) as median_hours_to_deposit
FROM first_deposits
WHERE publisher_id IS NOT NULL AND publisher_id != 0
GROUP BY publisher_id
ORDER BY avg_hours_to_deposit;
```

**Применение:**
- Понимание качества трафика (быстрее депозит = лучше качество)
- Оптимизация воронки для ускорения конверсии

---

### 4. **Анализ среднего чека (Average Deposit Amount)**

**Что показывает:**
- Средний размер депозита по паблишерам/форматам/кампаниям
- Тренд изменения среднего чека во времени
- Сравнение между брендами (4rabet vs Crorebet)

**SQL структура:**
```sql
-- Средний чек по паблишерам и форматам
SELECT 
    ue.publisher_id,
    ps.format,
    ue.advertiser as brand,
    COUNT(*) as deposits_count,
    AVG(ue.converted_amount) as avg_deposit_amount,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ue.converted_amount) as median_deposit_amount,
    MIN(ue.converted_amount) as min_deposit,
    MAX(ue.converted_amount) as max_deposit
FROM user_events ue
LEFT JOIN publisher_spend ps ON ue.publisher_id = ps.publisher_id
WHERE ue.event_type = 'deposit'
  AND ue.converted_amount > 0
  AND ue.publisher_id IS NOT NULL
  AND ue.publisher_id != 0
GROUP BY ue.publisher_id, ps.format, ue.advertiser
ORDER BY avg_deposit_amount DESC;
```

**Применение:**
- Понимание, какие источники приносят пользователей с большими депозитами
- Оптимизация таргетинга для привлечения "дорогих" пользователей

---

### 5. **Cohort Analysis (Когортный анализ)**

**Что показывает:**
- Поведение пользователей, привлеченных в разные периоды
- Retention по когортам
- LTV по когортам

**SQL структура:**
```sql
-- Cohort analysis: Retention по месяцам привлечения
WITH user_cohorts AS (
    SELECT 
        external_user_id,
        DATE_TRUNC('month', MIN(event_date)) as cohort_month
    FROM user_events
    WHERE event_type = 'deposit'
    GROUP BY external_user_id
),
monthly_activity AS (
    SELECT 
        ue.external_user_id,
        uc.cohort_month,
        DATE_TRUNC('month', ue.event_date) as activity_month,
        COUNT(*) as deposits,
        SUM(ue.converted_amount) as revenue
    FROM user_events ue
    JOIN user_cohorts uc ON ue.external_user_id = uc.external_user_id
    WHERE ue.event_type = 'deposit'
    GROUP BY ue.external_user_id, uc.cohort_month, DATE_TRUNC('month', ue.event_date)
)
SELECT 
    cohort_month,
    activity_month,
    EXTRACT(MONTH FROM AGE(activity_month, cohort_month)) as period_number,
    COUNT(DISTINCT external_user_id) as active_users,
    SUM(deposits) as total_deposits,
    SUM(revenue) as total_revenue
FROM monthly_activity
GROUP BY cohort_month, activity_month
ORDER BY cohort_month, activity_month;
```

**Применение:**
- Понимание долгосрочных трендов
- Сравнение эффективности маркетинга в разные периоды

---

### 6. **Анализ географических паттернов**

**Что показывает:**
- Эффективность по странам/регионам
- ARPPU по странам
- Retention по странам
- Сравнение брендов по странам

**SQL структура:**
```sql
-- Географический анализ
SELECT 
    ue.country,
    ue.advertiser as brand,
    COUNT(DISTINCT ue.external_user_id) as paying_users,
    COUNT(*) as total_deposits,
    SUM(ue.converted_amount) as total_revenue,
    AVG(ue.converted_amount) as avg_deposit,
    CASE 
        WHEN COUNT(DISTINCT ue.external_user_id) > 0 
        THEN SUM(ue.converted_amount) / COUNT(DISTINCT ue.external_user_id)
        ELSE 0
    END as arppu
FROM user_events ue
WHERE ue.event_type = 'deposit'
  AND ue.converted_amount > 0
  AND ue.country IS NOT NULL
GROUP BY ue.country, ue.advertiser
ORDER BY total_revenue DESC;
```

**Применение:**
- Оптимизация геотаргетинга
- Понимание, какие страны наиболее прибыльны

---

### 7. **Анализ повторных депозитов (Repeat Deposit Rate)**

**Что показывает:**
- Процент пользователей, которые делают повторные депозиты
- Среднее количество депозитов на пользователя
- Сравнение по источникам трафика

**SQL структура:**
```sql
-- Repeat Deposit Rate
WITH user_stats AS (
    SELECT 
        ue.external_user_id,
        ue.publisher_id,
        COUNT(*) as deposit_count,
        CASE WHEN COUNT(*) > 1 THEN 1 ELSE 0 END as is_repeat_user
    FROM user_events ue
    WHERE ue.event_type = 'deposit'
      AND ue.publisher_id IS NOT NULL
      AND ue.publisher_id != 0
    GROUP BY ue.external_user_id, ue.publisher_id
)
SELECT 
    publisher_id,
    COUNT(*) as total_users,
    SUM(is_repeat_user) as repeat_users,
    ROUND(100.0 * SUM(is_repeat_user) / COUNT(*), 2) as repeat_rate_pct,
    AVG(deposit_count) as avg_deposits_per_user
FROM user_stats
GROUP BY publisher_id
ORDER BY repeat_rate_pct DESC;
```

**Применение:**
- Понимание лояльности пользователей по источникам
- Оптимизация для привлечения "повторных" пользователей

---

### 8. **Анализ сезонности и временных паттернов**

**Что показывает:**
- Активность по дням недели
- Активность по часам суток (если есть данные)
- Сезонные тренды

**SQL структура:**
```sql
-- Активность по дням недели
SELECT 
    EXTRACT(DOW FROM event_date) as day_of_week,
    CASE EXTRACT(DOW FROM event_date)
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END as day_name,
    COUNT(*) as deposits,
    COUNT(DISTINCT external_user_id) as users,
    SUM(converted_amount) as revenue
FROM user_events
WHERE event_type = 'deposit'
GROUP BY EXTRACT(DOW FROM event_date)
ORDER BY day_of_week;
```

**Применение:**
- Оптимизация времени запуска кампаний
- Понимание пиков активности

---

### 9. **Анализ эффективности форматов рекламы (детальный)**

**Что показывает:**
- Сравнение форматов по всем метрикам (ARPPU, Retention, LTV, Repeat Rate)
- Тренды по форматам во времени
- Оптимальные форматы для разных брендов

**SQL структура:**
```sql
-- Детальный анализ форматов
SELECT 
    ps.format,
    ue.advertiser as brand,
    COUNT(DISTINCT ue.external_user_id) as users,
    COUNT(*) as deposits,
    SUM(ue.converted_amount) as revenue,
    AVG(ue.converted_amount) as avg_deposit,
    CASE 
        WHEN COUNT(DISTINCT ue.external_user_id) > 0 
        THEN SUM(ue.converted_amount) / COUNT(DISTINCT ue.external_user_id)
        ELSE 0
    END as arppu
FROM user_events ue
JOIN publisher_spend ps ON ue.publisher_id = ps.publisher_id
WHERE ue.event_type = 'deposit'
  AND ue.converted_amount > 0
  AND ps.format IS NOT NULL
GROUP BY ps.format, ue.advertiser
ORDER BY revenue DESC;
```

**Применение:**
- Оптимизация распределения бюджета между форматами
- Понимание, какие форматы работают лучше для разных брендов

---

### 10. **Анализ конверсионной воронки (если есть данные о views/clicks)**

**Что показывает:**
- Конверсия views → clicks → deposits
- Потери на каждом этапе воронки
- Сравнение воронок по источникам

**Применение:**
- Оптимизация воронки конверсии
- Понимание, где теряются пользователи

---

### 11. **Сравнение эффективности брендов (4rabet vs Crorebet)**

**Что показывает:**
- Сравнение всех метрик между брендами
- Различия в поведении пользователей
- Оптимизация для каждого бренда отдельно

**SQL структура:**
```sql
-- Сравнение брендов
SELECT 
    COALESCE(advertiser, 'Unknown') as brand,
    COUNT(DISTINCT external_user_id) as users,
    COUNT(*) as deposits,
    SUM(converted_amount) as revenue,
    AVG(converted_amount) as avg_deposit,
    CASE 
        WHEN COUNT(DISTINCT external_user_id) > 0 
        THEN SUM(converted_amount) / COUNT(DISTINCT external_user_id)
        ELSE 0
    END as arppu
FROM user_events
WHERE event_type = 'deposit'
  AND converted_amount > 0
GROUP BY COALESCE(advertiser, 'Unknown')
ORDER BY revenue DESC;
```

---

### 12. **Анализ эффективности кампаний (из Google Sheets + user_events)**

**Что показывает:**
- Сравнение данных из Google Sheets с реальными депозитами
- Валидация атрибуции
- Поиск расхождений

**Применение:**
- Проверка качества данных
- Оптимизация атрибуции

---

## 🎯 Приоритетные инсайты для реализации:

1. **Retention Analysis** - критически важно для понимания качества трафика
2. **LTV Analysis** - для оптимизации бюджета
3. **Repeat Deposit Rate** - для понимания лояльности
4. **Geographic Analysis** - для геотаргетинга
5. **Cohort Analysis** - для долгосрочных трендов

---

## 📝 Рекомендации по реализации:

1. Начните с **Retention** и **LTV** - это даст максимальную ценность
2. Создайте отдельные Dashboard для каждого типа анализа
3. Используйте фильтры для сравнения разных периодов/источников
4. Комбинируйте метрики для комплексного анализа

---

**Готов помочь реализовать любой из этих инсайтов!** 🚀

