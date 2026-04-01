"""
НЕДЕЛЯ 5: SQL-проверки качества данных
"""

import sqlite3
from pathlib import Path

print("="*60)
print("SQL-ПРОВЕРКИ КАЧЕСТВА ДАННЫХ")
print("="*60)

# Подключаемся к базе
db_path = Path("data/mart.db")

if not db_path.exists():
    print(f"❌ Ошибка: файл {db_path} не найден!")
    print("   Сначала запустите load_to_sqlite.py")
    exit()

conn = sqlite3.connect(db_path)
TABLE = "mart_world_bank"

print(f"\nТаблица: {TABLE}")
print(f"База: {db_path.absolute()}")
print()

# ------------------------------------------------------------
# ПРОВЕРКА 1: Количество строк
# ------------------------------------------------------------
print("1. ПРОВЕРКА: Таблица не пустая")
print("-" * 40)

cursor = conn.execute(f"SELECT COUNT(*) FROM {TABLE};")
count = cursor.fetchone()[0]
print(f"   Количество строк: {count}")

if count > 0:
    print("   ✅ ПРОВЕРКА ПРОЙДЕНА")
else:
    print("   ❌ ОШИБКА")

# ------------------------------------------------------------
# ПРОВЕРКА 2: Диапазон лет
# ------------------------------------------------------------
print("\n2. ПРОВЕРКА: Диапазон лет")
print("-" * 40)

cursor = conn.execute(f"SELECT MIN(year), MAX(year) FROM {TABLE};")
min_year, max_year = cursor.fetchone()
print(f"   Годы: {min_year} - {max_year}")

if min_year == 1960 and max_year == 2025:
    print("   ✅ ПРОВЕРКА ПРОЙДЕНА")
else:
    print("   ❌ ОШИБКА")

# ------------------------------------------------------------
# ПРОВЕРКА 3: NULL в value
# ------------------------------------------------------------
print("\n3. ПРОВЕРКА: NULL в колонке value")
print("-" * 40)

cursor = conn.execute(f"SELECT COUNT(*) FROM {TABLE} WHERE value IS NULL;")
null_count = cursor.fetchone()[0]
print(f"   NULL в value: {null_count}")

if null_count == 1:
    print("   ✅ ПРОВЕРКА ПРОЙДЕНА (только 2025 год)")
else:
    print("   ❌ ОШИБКА")

# ------------------------------------------------------------
# ПРОВЕРКА 4: Дубликаты
# ------------------------------------------------------------
print("\n4. ПРОВЕРКА: Дубликаты по году")
print("-" * 40)

cursor = conn.execute(f"""
    SELECT year, COUNT(*) 
    FROM {TABLE} 
    GROUP BY year 
    HAVING COUNT(*) > 1;
""")
duplicates = cursor.fetchall()
print(f"   Дубликатов: {len(duplicates)}")

if len(duplicates) == 0:
    print("   ✅ ПРОВЕРКА ПРОЙДЕНА")
else:
    print(f"   ❌ ОШИБКА: {duplicates}")

# ------------------------------------------------------------
# ПРОВЕРКА 5: Статистика по ВВП
# ------------------------------------------------------------
print("\n5. ПРОВЕРКА: Статистика по ВВП")
print("-" * 40)

cursor = conn.execute(f"""
    SELECT 
        ROUND(AVG(value), 2) as avg_gdp,
        MIN(value) as min_gdp,
        MAX(value) as max_gdp
    FROM {TABLE} 
    WHERE value IS NOT NULL;
""")
avg_gdp, min_gdp, max_gdp = cursor.fetchone()
print(f"   Средний ВВП: ${avg_gdp:,.2f}")
print(f"   Минимальный ВВП: ${min_gdp:,.2f}")
print(f"   Максимальный ВВП: ${max_gdp:,.2f}")

# ------------------------------------------------------------
# ИТОГ
# ------------------------------------------------------------
print("\n" + "="*60)
print("ИТОГИ ПРОВЕРОК:")
print("="*60)

all_passed = (
    count == 66 and
    min_year == 1960 and max_year == 2025 and
    null_count == 1 and
    len(duplicates) == 0
)

if all_passed:
    print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
    print("   Данные загружены корректно")
else:
    print("⚠️ НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ")
    print("   Проверьте данные и повторите загрузку")

conn.close()
print("="*60)