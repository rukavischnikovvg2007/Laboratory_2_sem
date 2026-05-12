"""
ETL: Load stage
Загрузка mart в базу данных SQLite (поддержка full и incremental режимов)
"""

import pandas as pd
import sqlite3
from pathlib import Path
import sys
import yaml

def get_nested_value(config, keys, default=None):
    """Безопасно получает значение из вложенного словаря"""
    for key in keys:
        if isinstance(config, dict):
            config = config.get(key)
        else:
            return default
        if config is None:
            return default
    return config

def load(config_path, mode="full"):
    """Загружает mart в базу данных"""
    
    print("="*60)
    print("СТАДИЯ 3: LOAD (загрузка в базу данных)")
    print("="*60)
    print(f"Режим: {mode}")
    
    # 1. Загружаем конфиг
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 2. Извлекаем variant_id
    variant_id = get_nested_value(config, ['variant', 'id'])
    if not variant_id:
        variant_num = get_nested_value(config, ['variant_id'], '10')
        variant_id = f"variant_{variant_num}"
    
    # 3. Находим самый свежий mart-файл
    mart_dir = Path(f"data/mart/{variant_id}")
    mart_files = list(mart_dir.glob("mart_yearly_*.csv"))
    
    if not mart_files:
        print(f"❌ Ошибка: нет mart-файла в {mart_dir}!")
        print("   Сначала выполните стадию TRANSFORM")
        return False
    
    latest = max(mart_files, key=lambda p: p.stat().st_mtime)
    print(f"📁 Файл: {latest.name}")
    
    # 4. Загружаем данные
    df = pd.read_csv(latest)
    print(f"📊 Строк в файле: {len(df)}")
    print(f"   Колонок: {len(df.columns)}")
    
    # 5. Подключаемся к базе данных
    db_path = Path("data/mart.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    
    TABLE_NAME = "mart_world_bank"
    
    # 6. Загружаем в зависимости от режима
    if mode == "full":
        # ПОЛНАЯ ЗАГРУЗКА: удаляем старую таблицу и создаем заново
        conn.execute(f"DROP TABLE IF EXISTS {TABLE_NAME};")
        print("   🗑️ Старая таблица удалена")
        
        df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
        conn.commit()
        print(f"   ✅ Данные загружены (full mode)")
        
    elif mode == "incremental":
        # ИНКРЕМЕНТАЛЬНАЯ ЗАГРУЗКА: добавляем только новые годы
        
        # Проверяем, существует ли таблица
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (TABLE_NAME,))
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            # Получаем максимальный год в базе
            cursor = conn.execute(f"SELECT MAX(year) FROM {TABLE_NAME};")
            max_year_in_db = cursor.fetchone()[0]
            print(f"   📅 Максимальный год в базе: {max_year_in_db}")
            
            # Берем только новые годы (больше watermark)
            df_new = df[df['year'] > max_year_in_db]
            print(f"   📊 Новых строк для добавления: {len(df_new)}")
            
            if len(df_new) > 0:
                df_new.to_sql(TABLE_NAME, conn, if_exists="append", index=False)
                conn.commit()
                print(f"   ✅ Добавлено {len(df_new)} новых строк")
                
                # Показываем диапазон добавленных годов
                min_new_year = df_new['year'].min()
                max_new_year = df_new['year'].max()
                print(f"   📅 Добавлены годы: {int(min_new_year)} - {int(max_new_year)}")
            else:
                print("   ✅ Новых данных нет")
        else:
            # Таблицы нет — создаем (первый запуск)
            df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
            conn.commit()
            print(f"   ✅ Таблица создана, загружено {len(df)} строк")
    
    # 7. Проверяем результат
    cursor = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME};")
    count = cursor.fetchone()[0]
    print(f"\n📊 Итоговое количество строк в таблице: {count}")
    
    # Показываем диапазон лет в базе
    cursor = conn.execute(f"SELECT MIN(year), MAX(year) FROM {TABLE_NAME};")
    min_year, max_year = cursor.fetchone()
    if min_year and max_year:
        print(f"📅 Диапазон лет в базе: {int(min_year)} - {int(max_year)}")
    
    conn.close()
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python load.py <config_path> [--mode full|incremental]")
        print("Пример: python load.py configs/variant_10.yml --mode full")
        sys.exit(1)
    
    # Проверяем режим
    mode = "full"
    if len(sys.argv) > 2 and sys.argv[2] == "--mode":
        mode = sys.argv[3] if len(sys.argv) > 3 else "full"
    
    load(sys.argv[1], mode)
