# Настройка чарта ARPPU для 4rabet

## Шаг 1: Создание Dataset

1. **Откройте Superset** → **SQL Lab**
2. **Скопируйте SQL-запрос** из файла `arppu_crorebet_trend_simple.sql`
3. **Вставьте запрос** в SQL Lab
4. **Выполните запрос** (Run) - проверьте, что данные возвращаются
5. **Сохраните как Dataset:**
   - Нажмите **"Save"** → **"Save dataset"**
   - **Table name**: `arppu_4rabet_trend`
   - **Schema**: `public` (или оставьте пустым)
   - Нажмите **"Save"**

## Шаг 2: Создание Chart

1. **После сохранения Dataset** нажмите **"Explore"** (или перейдите в **Charts** → **+ Chart**)
2. **Выберите Dataset**: `arppu_4rabet_trend`
3. **Выберите Chart Type**: **Line Chart** (для графика тренда)

### Настройка Query:

**Query Mode**: `Aggregate` (НЕ Raw records!)

**Dimensions (Group by)**:
- `event_date` - дата (для оси X графика)

**Metrics**:
- `arppu_usd` - средний ARPPU (основная метрика)
  - Тип: `AVG` или `SUM` (обычно `AVG` для среднего значения)
  
**Опциональные Metrics** (для дополнительной информации):
- `paying_users` - количество платящих пользователей (SUM)
- `total_deposits` - общее количество депозитов (SUM)
- `total_revenue_usd` - общая выручка (SUM)

### Настройка визуализации:

**Chart Type**: **Line Chart**

**Time Column**: `event_date`

**X Axis**: `event_date`

**Y Axis**: `arppu_usd`

**Опционально**:
- **Series**: можно добавить другие метрики для сравнения
- **Color Scheme**: выберите цветовую схему
- **Show Legend**: включите, если несколько серий

4. **Сохраните Chart:**
   - Нажмите **"Save"** → **"Save chart"**
   - **Chart name**: `ARPPU 4rabet - Trend`
   - **Description** (опционально): `График изменения ARPPU по бренду 4rabet по дням`
   - Нажмите **"Save"**

## Шаг 3: Создание Dashboard

### Вариант 1: Создать Dashboard при сохранении Chart (РЕКОМЕНДУЕТСЯ)

1. **При сохранении Chart** найдите поле **"Add to Dashboard"**
2. Выберите **"+ Add to new dashboard"**
3. **Dashboard name**: `ARPPU Analysis`
4. Нажмите **"Save"**
5. ✅ Dashboard создастся автоматически с вашим Chart!

### Вариант 2: Создать Dashboard отдельно

1. **Dashboards** → **"+ Dashboard"** (кнопка в правом верхнем углу)
2. **Dashboard name**: `ARPPU Analysis`
3. **Description** (опционально): `Анализ ARPPU по бренду 4rabet`
4. Нажмите **"Save"**

## Шаг 4: Добавление Chart на Dashboard

1. **Откройте созданный Dashboard**
2. Нажмите **"Edit Dashboard"** (кнопка в правом верхнем углу)
3. Нажмите **"+ Chart"** (кнопка в левом верхнем углу)
4. **Выберите Chart**: `ARPPU 4rabet - Trend`
5. **Chart появится на Dashboard** - перетащите его в нужное место
6. **Настройте размер**: потяните за углы чарта, чтобы изменить размер
7. Нажмите **"Save"** (кнопка в правом верхнем углу)

## Шаг 5: Добавление фильтра по дате

1. **На Dashboard** (в режиме редактирования) нажмите **"+ Filter"** (или **"Add Filter"**)
2. **Выберите тип фильтра**: **Time Range** или **Date Range**
3. **Выберите Dataset**: `arppu_4rabet_trend`
4. **Выберите Column**: `event_date`
5. **Filter name**: `Date Range`
6. **Настройте Scoping** (важно!):
   - Нажмите на фильтр → **"Scoping"**
   - Выберите **"Apply to specific charts"**
   - Отметьте чекбокс для вашего чарта `ARPPU 4rabet - Trend`
   - Нажмите **"Save"**
7. **Нажмите "Save"** на Dashboard

## Шаг 6: Настройка внешнего вида Dashboard

1. **В режиме редактирования Dashboard:**
   - **Перетащите чарт** в нужное место
   - **Измените размер** чарта (потяните за углы)
   - **Растяните чарт** на всю ширину, если нужно (но не на весь экран)

2. **Для растяжения без полноэкранного режима:**
   - Потяните правый край чарта вправо
   - Или установите ширину чарта на 24 колонки (максимум в сетке Superset)

3. **Сохраните Dashboard**

## Готово! ✅

Теперь у вас есть:
- ✅ Chart с графиком ARPPU по 4rabet
- ✅ Dashboard с фильтром по дате
- ✅ Возможность выбирать период прямо на Dashboard

## Дополнительные советы:

1. **Для ускорения запроса**: Раскомментируйте строки 30-31 в SQL и установите нужный период
2. **Для сравнения с Crorebet**: Создайте аналогичный чарт для Crorebet и добавьте на тот же Dashboard
3. **Для группировки по неделям/месяцам**: Измените `DATE(ue.event_date)` на `DATE_TRUNC('week', ue.event_date)` или `DATE_TRUNC('month', ue.event_date)` в SQL

