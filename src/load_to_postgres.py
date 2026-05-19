"""
ETL: Load stage для PostgreSQL (Docker)
Загружает mart в PostgreSQL контейнер с защитой от дублей (DELETE + INSERT)
"""

import os
import pandas as pd
import psycopg2
from pathlib import Path
import sys
import yaml
import argparse
from sqlalchemy import create_engine

# Устанавливаем рабочую директорию
if os.path.exists("/opt/airflow"):
    os.chdir("/opt/airflow")
    print("📁 Working directory:", os.getcwd())

def get_nested_value(config, keys, default=None):
    for key in keys:
        if isinstance(config, dict):
            config = config.get(key)
        else:
            return default
        if config is None:
            return default
    return config

def load_to_postgres(config_path, run_date=None, start_date=None, end_date=None, mode="incremental"):
    print("="*60)
    print("СТАДИЯ 3: LOAD (загрузка в PostgreSQL Docker)")
    print("="*60)
    print(f"Режим: {mode}")
    
    if run_date:
        print(f"📅 Run date: {run_date}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    variant_id = get_nested_value(config, ['variant', 'id'])
    if not variant_id:
        variant_num = get_nested_value(config, ['variant_id'], '10')
        variant_id = f"variant_{variant_num}"
    
    mart_dir = Path(f"data/mart/{variant_id}")
    
    if run_date:
        mart_file = mart_dir / f"mart_{run_date}.csv"
        if not mart_file.exists():
            print(f"⚠️ Файл {mart_file} не найден, ищу самый свежий...")
            mart_files = list(mart_dir.glob("mart_*.csv"))
            if not mart_files:
                print(f"❌ Ошибка: нет mart-файла в {mart_dir}!")
                return False
            mart_file = max(mart_files, key=lambda p: p.stat().st_mtime)
    else:
        mart_files = list(mart_dir.glob("mart_*.csv"))
        if not mart_files:
            print(f"❌ Ошибка: нет mart-файла в {mart_dir}!")
            return False
        mart_file = max(mart_files, key=lambda p: p.stat().st_mtime)
    
    print(f"📁 Файл: {mart_file.name}")
    
    df = pd.read_csv(mart_file)
    print(f"📊 Строк в файле: {len(df)}")
    print(f"   Колонок: {len(df.columns)}")
    
    if run_date:
        period_year = int(run_date[:4])
    elif 'year' in df.columns:
        period_year = int(df['year'].iloc[0]) if len(df) > 0 else None
    else:
        period_year = None
    
    print(f"📅 Период для удаления: {period_year}")
    
    DB_CONFIG = {
        "host": "postgres",
        "port": 5432,
        "database": "analytics",
        "user": "airflow",
        "password": "airflow"
    }
    TABLE_NAME = "mart_world_bank"
    
    try:
        print(f"\n🔌 Подключение к PostgreSQL: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        
        engine = create_engine(
            f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
            f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )
        
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cur = conn.cursor()
        
        print("✅ Подключение к PostgreSQL успешно")
        
        if mode == "full":
            try:
                cur.execute(f"DROP TABLE IF EXISTS {TABLE_NAME};")
                print("   🗑️ Старая таблица удалена")
            except Exception as e:
                print(f"   ⚠️ Не удалось удалить таблицу: {e}")
            
            df.to_sql(TABLE_NAME, engine, if_exists="replace", index=False)
            print(f"   ✅ Данные загружены (full mode)")
            
        elif mode == "incremental":
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, (TABLE_NAME,))
            table_exists = cur.fetchone()[0]
            
            if not table_exists:
                df.head(0).to_sql(TABLE_NAME, engine, if_exists="replace", index=False)
                print("   📋 Таблица создана")
            
            if period_year:
                cur.execute(f"DELETE FROM {TABLE_NAME} WHERE year = %s;", (period_year,))
                deleted_count = cur.rowcount
                print(f"   🗑️ Удалено строк за {period_year}: {deleted_count}")
            else:
                print("   ⚠️ Не удалось определить период для удаления")
            
            df.to_sql(TABLE_NAME, engine, if_exists="append", index=False)
            print(f"   ✅ Добавлено {len(df)} строк")
        
        conn.commit()
        
        cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME};")
        count = cur.fetchone()[0]
        print(f"\n📊 Итоговое количество строк в таблице: {count}")
        
        cur.execute(f"SELECT MIN(year), MAX(year) FROM {TABLE_NAME};")
        result = cur.fetchone()
        if result and result[0] and result[1]:
            print(f"📅 Диапазон лет в базе: {int(result[0])} - {int(result[1])}")
        
        cur.execute("""
            SELECT year, COUNT(*) as cnt 
            FROM mart_world_bank 
            GROUP BY year 
            HAVING COUNT(*) > 1;
        """)
        duplicates = cur.fetchall()
        if duplicates:
            print(f"\n⚠️ ВНИМАНИЕ: Найдены дубликаты по годам:")
            for year, cnt in duplicates:
                print(f"   Год {year}: {cnt} строк (ожидается 1 группа)")
        else:
            print(f"\n✅ Проверка дублей: OK (нет дублей по годам)")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--run_date")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--mode", default="incremental", choices=["full", "incremental"])
    args = parser.parse_args()
    
    success = load_to_postgres(args.config, args.run_date, args.start, args.end, args.mode)
    sys.exit(0 if success else 1)
