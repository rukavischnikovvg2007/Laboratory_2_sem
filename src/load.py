"""
НЕДЕЛЯ 5: Загрузка витрины в SQLite
"""

import pandas as pd
import sqlite3
from pathlib import Path

print("="*60)
print("ЗАГРУЗКА ВИТРИНЫ В SQLITE")
print("="*60)

# 1. Находим mart-файл из 4 недели
mart_dir = Path("data/mart/variant_10")
mart_files = list(mart_dir.glob("mart_yearly_*.csv"))

if not mart_files:
    print("❌ Ошибка: нет mart-файла!")
    print("   Сначала выполните задание 4 недели")
    exit()

latest = max(mart_files, key=lambda p: p.stat().st_mtime)
print(f"Файл: {latest.name}")

# 2. Загружаем данные
df = pd.read_csv(latest)
print(f"Строк: {len(df)}")
print(f"Колонок: {len(df.columns)}")

# 3. Создаем базу данных SQLite
db_path = Path("data/mart.db")
db_path.parent.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(db_path)

# 4. Загружаем в таблицу
TABLE_NAME = "mart_world_bank"
df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
conn.commit()  # ВАЖНО! Сохраняем изменения

# 5. Проверяем
cursor = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME};")
count = cursor.fetchone()[0]
print(f"✅ Загружено {count} строк в таблицу '{TABLE_NAME}'")

conn.close()
print("="*60)
