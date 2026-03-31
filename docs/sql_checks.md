# SQL-проверки качества данных

## Неделя 5: Загрузка витрины в SQLite

### Параметры
- **Таблица:** mart_world_bank
- **База данных:** data/mart.db
- **Количество строк:** 66
- **Диапазон лет:** 1960-2025

---

## Проверка 1: Таблица не пустая

**SQL-запрос:**
```sql
SELECT COUNT(*) FROM mart_world_bank;

## Проверка 2: Диапазон лет
SQL-запрос:

SELECT MIN(year), MAX(year) FROM mart_world_bank;

## Проверка 3: NULL в колонке value
SQL-запрос:

SELECT COUNT(*) FROM mart_world_bank WHERE value IS NULL;


## Проверка 4: Дубликаты по году
SQL-запрос:

SELECT year, COUNT(*) 
FROM mart_world_bank 
GROUP BY year 
HAVING COUNT(*) > 1;

## Проверка 5: Статистика по ВВП
SQL-запрос:

SELECT 
    ROUND(AVG(value), 2) as avg_gdp,
    MIN(value) as min_gdp,
    MAX(value) as max_gdp
FROM mart_world_bank 
WHERE value IS NOT NULL;
