"""
ETL: Transform stage
Преобразование raw JSON → normalized → mart
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
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

def transform(config_path):
    """Преобразует raw данные в normalized и mart"""
    
    print("="*60)
    print("СТАДИЯ 2: TRANSFORM (преобразование данных)")
    print("="*60)
    
    # 1. Загружаем конфиг
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 2. Извлекаем variant_id (поддерживаем разные форматы)
    variant_id = get_nested_value(config, ['variant', 'id'])
    if not variant_id:
        variant_num = get_nested_value(config, ['variant_id'], '10')
        variant_id = f"variant_{variant_num}"
    
    print(f"📁 Вариант: {variant_id}")
    
    # 3. Находим самый свежий raw JSON
    raw_dir = Path(f"data/raw/{variant_id}")
    json_files = list(raw_dir.glob("*.json"))
    
    if not json_files:
        print(f"❌ Нет raw JSON файлов в {raw_dir}")
        return False
    
    latest_raw = max(json_files, key=lambda p: p.stat().st_mtime)
    print(f"📁 Использую raw файл: {latest_raw.name}")
    
    # 4. Читаем JSON
    with open(latest_raw, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 5. Извлекаем записи (World Bank API формат)
    if isinstance(data, list) and len(data) > 1:
        records = data[1]
    else:
        records = data
    
    print(f"📊 Найдено записей: {len(records)}")
    
    # 6. Создаем normalized DataFrame
    normalized_records = []
    for item in records:
        try:
            record = {
                'year': int(item['date']) if item.get('date') else None,
                'value': item.get('value'),
                'country_iso3': item.get('country', {}).get('id'),
                'country_name': item.get('country', {}).get('value'),
                'indicator_code': item.get('indicator', {}).get('id'),
                'indicator_name': item.get('indicator', {}).get('value')
            }
            normalized_records.append(record)
        except:
            continue
    
    df_norm = pd.DataFrame(normalized_records)
    print(f"✅ Normalized DataFrame: {df_norm.shape[0]} строк, {df_norm.shape[1]} колонок")
    
    # 7. Очистка normalized
    df_norm['year'] = pd.to_numeric(df_norm['year'], errors='coerce')
    df_norm['value'] = pd.to_numeric(df_norm['value'], errors='coerce')
    df_norm = df_norm.dropna(subset=['year'])
    df_norm = df_norm.drop_duplicates(subset=['year', 'country_iso3', 'indicator_code'])
    df_norm = df_norm.sort_values('year').reset_index(drop=True)
    
    # 8. Сохраняем normalized CSV
    norm_dir = Path(f"data/normalized/{variant_id}")
    norm_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    norm_path = norm_dir / f"{timestamp}.csv"
    df_norm.to_csv(norm_path, index=False, encoding='utf-8')
    print(f"✅ Normalized сохранен: {norm_path}")
    
    # 9. Загружаем справочник стран
    ref_path = Path("reference/countries.csv")
    if ref_path.exists():
        df_ref = pd.read_csv(ref_path)
        print(f"📚 Загружен справочник: {ref_path}")
    else:
        # Создаем справочник, если нет
        df_ref = pd.DataFrame({
            "country_iso3": ["DE"],
            "country_name_full": ["Germany"],
            "region": ["Western Europe"],
            "income_group": ["High income"],
            "currency": ["Euro"],
            "capital": ["Berlin"]
        })
        df_ref.to_csv(ref_path, index=False)
        print("📝 Создан новый справочник стран")
    
    print(f"   Справочник: {df_ref.shape[0]} строк")
    
    # 10. Join со справочником
    df_mart = df_norm.merge(df_ref, on="country_iso3", how="left")
    
    # 11. Добавляем временные признаки
    df_mart['date'] = pd.to_datetime(df_mart['year'], format='%Y')
    df_mart['decade'] = (df_mart['year'] // 10) * 10
    
    print(f"✅ Mart DataFrame: {df_mart.shape[0]} строк, {df_mart.shape[1]} колонок")
    
    # 12. Сохраняем mart CSV
    mart_dir = Path(f"data/mart/{variant_id}")
    mart_dir.mkdir(parents=True, exist_ok=True)
    
    mart_path = mart_dir / f"mart_yearly_{timestamp}.csv"
    df_mart.to_csv(mart_path, index=False, encoding='utf-8')
    print(f"✅ Mart сохранен: {mart_path}")
    
    # 13. Показываем статистику
    print(f"\n📊 Статистика:")
    print(f"   Диапазон лет: {int(df_mart['year'].min())} - {int(df_mart['year'].max())}")
    print(f"   Количество строк: {len(df_mart)}")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python transform.py <config_path>")
        sys.exit(1)
    
    transform(sys.argv[1])