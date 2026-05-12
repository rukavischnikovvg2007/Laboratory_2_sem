"""
ETL: Load stage для PostgreSQL (Docker)
Загружает mart в PostgreSQL контейнер
"""

import pandas as pd
import psycopg2
from pathlib import Path
import sys
import yaml
from sqlalchemy import create_engine

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

def load_to_postgres(config_path, mode="full"):
    """Загружает mart в PostgreSQL (Docker контейнер)"""
    
    print("="*60)
    print("СТАДИЯ 3: LOAD (загрузка в PostgreSQL Docker)")
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
    print(f"   Колонки: {list(df.columns)}")
    
    # 5. ПАРАМЕТРЫ ПОДКЛЮЧЕНИЯ К POSTGRESQL (ИСПРАВЛЕНО!)
    # Используем имя сервиса из docker-compose.yml
    DB_CONFIG = {
        "host": "postgres",  # ← ИМЯ СЕРВИСА из docker-compose.yml
        "port": 5432,        # ← ВНУТРЕННИЙ порт контейнера
        "database": "analytics",
        "user": "student",
        "password": "student_pw"
    }
    
    TABLE_NAME = "mart_world_bank"
    
    try:
        print(f"\n🔌 Подключение к PostgreSQL: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
        
        # Создаем подключение через SQLAlchemy (для pandas)
        engine = create_engine(
            f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
            f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )
        
        # Также создаем сырое подключение для выполнения команд
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        
        print("✅ Подключение к PostgreSQL успешно")
        
        # 6. Загружаем в зависимости от режима
        if mode == "full":
            try:
                with conn.cursor() as cursor:
                    cursor.execute(f"DROP TABLE IF EXISTS {TABLE_NAME};")
                print("   🗑️ Старая таблица удалена")
            except Exception as e:
                print(f"   ⚠️ Не удалось удалить таблицу: {e}")
            
            df.to_sql(TABLE_NAME, engine, if_exists="replace", index=False)
            print(f"   ✅ Данные загружены (full mode)")
            
        elif mode == "incremental":
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, (TABLE_NAME,))
            table_exists = cursor.fetchone()[0]
            
            if table_exists:
                cursor.execute(f"SELECT MAX(year) FROM {TABLE_NAME};")
                max_year_in_db = cursor.fetchone()[0]
                print(f"   📅 Максимальный год в базе: {max_year_in_db}")
                
                df_new = df[df['year'] > max_year_in_db]
                print(f"   📊 Новых строк для добавления: {len(df_new)}")
                
                if len(df_new) > 0:
                    df_new.to_sql(TABLE_NAME, engine, if_exists="append", index=False)
                    print(f"   ✅ Добавлено {len(df_new)} новых строк")
                    
                    min_new_year = df_new['year'].min()
                    max_new_year = df_new['year'].max()
                    print(f"   📅 Добавлены годы: {int(min_new_year)} - {int(max_new_year)}")
                else:
                    print("   ✅ Новых данных нет")
            else:
                df.to_sql(TABLE_NAME, engine, if_exists="replace", index=False)
                print(f"   ✅ Таблица создана, загружено {len(df)} строк")
        
        # 7. Проверяем результат
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME};")
            count = cursor.fetchone()[0]
            print(f"\n📊 Итоговое количество строк в таблице: {count}")
            
            cursor.execute(f"SELECT MIN(year), MAX(year) FROM {TABLE_NAME};")
            result = cursor.fetchone()
            if result:
                min_year, max_year = result
                if min_year and max_year:
                    print(f"📅 Диапазон лет в базе: {int(min_year)} - {int(max_year)}")
        
        print("\n📋 Пример данных (первые 5 строк):")
        print(df.head().to_string())
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА подключения к PostgreSQL: {e}")
        print("\nПроверьте:")
        print("  1. Запущен ли Docker контейнер: docker ps")
        print("  2. Работает ли PostgreSQL: docker exec -it lab_postgres psql -U student -d analytics -c 'SELECT 1;'")
        print("  3. Правильные ли параметры подключения:")
        print(f"     host={DB_CONFIG['host']}, port={DB_CONFIG['port']}")
        print("  4. Существует ли база данных 'analytics'")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python load_to_postgres.py <config_path> [--mode full|incremental]")
        print("Пример: python load_to_postgres.py configs/variant_10.yml --mode full")
        print("\nПеред запуском убедитесь, что Docker контейнер запущен:")
        print("  docker compose up -d")
        sys.exit(1)
    
    mode = "full"
    if len(sys.argv) > 2 and sys.argv[2] == "--mode":
        mode = sys.argv[3] if len(sys.argv) > 3 else "full"
    
    success = load_to_postgres(sys.argv[1], mode)
    
    if success:
        print("\n✅ Готово! Данные загружены в PostgreSQL.")
        print("   Теперь можно подключать Metabase к базе данных 'analytics'")
    else:
        print("\n❌ Загрузка не удалась. Проверьте ошибки выше.")
        sys.exit(1)