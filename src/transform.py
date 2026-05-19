"""
ETL: Transform stage
Преобразование raw JSON → normalized → mart
"""

import os
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import sys
import yaml
import argparse

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

def transform(config_path, run_date=None, start_date=None, end_date=None):
    print("="*60)
    print("СТАДИЯ 2: TRANSFORM (преобразование данных)")
    print("="*60)
    
    if run_date:
        print(f"📅 Run date: {run_date}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    variant_id = get_nested_value(config, ['variant', 'id'])
    if not variant_id:
        variant_num = get_nested_value(config, ['variant_id'], '10')
        variant_id = f"variant_{variant_num}"
    
    print(f"📁 Вариант: {variant_id}")
    
    raw_dir = Path(f"data/raw/{variant_id}")
    
    if run_date:
        raw_file = raw_dir / f"raw_{run_date}.json"
        if not raw_file.exists():
            print(f"⚠️ Файл {raw_file} не найден, ищу самый свежий...")
            json_files = list(raw_dir.glob("*.json"))
            if not json_files:
                print(f"❌ Нет raw JSON файлов в {raw_dir}")
                return False
            latest_raw = max(json_files, key=lambda p: p.stat().st_mtime)
        else:
            latest_raw = raw_file
    else:
        json_files = list(raw_dir.glob("*.json"))
        if not json_files:
            print(f"❌ Нет raw JSON файлов в {raw_dir}")
            return False
        latest_raw = max(json_files, key=lambda p: p.stat().st_mtime)
    
    print(f"📁 Использую raw файл: {latest_raw.name}")
    
    with open(latest_raw, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list) and len(data) > 1:
        records = data[1]
    else:
        records = data
    
    print(f"📊 Найдено записей: {len(records)}")
    
    # Если нет данных — создаём пустые файлы и выходим с успехом
    if len(records) == 0:
        print("⚠️ Нет данных для обработки, создаю пустые файлы...")
        
        # Создаём пустой normalized
        norm_dir = Path(f"data/normalized/{variant_id}")
        norm_dir.mkdir(parents=True, exist_ok=True)
        empty_df = pd.DataFrame(columns=['year', 'value', 'country_iso3', 'country_name', 
                                          'indicator_code', 'indicator_name'])
        if run_date:
            norm_path = norm_dir / f"normalized_{run_date}.csv"
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            norm_path = norm_dir / f"{timestamp}.csv"
        empty_df.to_csv(norm_path, index=False, encoding='utf-8')
        print(f"✅ Пустой Normalized сохранен: {norm_path}")
        
        # Создаём пустой mart
        mart_dir = Path(f"data/mart/{variant_id}")
        mart_dir.mkdir(parents=True, exist_ok=True)
        empty_mart = pd.DataFrame(columns=['year', 'value', 'country_iso3', 'country_name',
                                            'indicator_code', 'indicator_name', 'country_name_full',
                                            'region', 'income_group', 'currency', 'capital', 'date', 'decade'])
        if run_date:
            mart_path = mart_dir / f"mart_{run_date}.csv"
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            mart_path = mart_dir / f"mart_yearly_{timestamp}.csv"
        empty_mart.to_csv(mart_path, index=False, encoding='utf-8')
        print(f"✅ Пустой Mart сохранен: {mart_path}")
        
        print("✅ Transform завершён (нет данных)")
        return True
    
    # Создаем normalized DataFrame
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
    
    df_norm['year'] = pd.to_numeric(df_norm['year'], errors='coerce')
    df_norm['value'] = pd.to_numeric(df_norm['value'], errors='coerce')
    df_norm = df_norm.dropna(subset=['year'])
    df_norm = df_norm.drop_duplicates(subset=['year', 'country_iso3', 'indicator_code'])
    df_norm = df_norm.sort_values('year').reset_index(drop=True)
    
    norm_dir = Path(f"data/normalized/{variant_id}")
    norm_dir.mkdir(parents=True, exist_ok=True)
    
    if run_date:
        norm_path = norm_dir / f"normalized_{run_date}.csv"
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        norm_path = norm_dir / f"{timestamp}.csv"
    
    df_norm.to_csv(norm_path, index=False, encoding='utf-8')
    print(f"✅ Normalized сохранен: {norm_path}")
    
    ref_path = Path("reference/countries.csv")
    if ref_path.exists():
        df_ref = pd.read_csv(ref_path)
        print(f"📚 Загружен справочник: {ref_path}")
    else:
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
    
    df_mart = df_norm.merge(df_ref, on="country_iso3", how="left")
    df_mart['date'] = pd.to_datetime(df_mart['year'], format='%Y')
    df_mart['decade'] = (df_mart['year'] // 10) * 10
    
    print(f"✅ Mart DataFrame: {df_mart.shape[0]} строк, {df_mart.shape[1]} колонок")
    
    mart_dir = Path(f"data/mart/{variant_id}")
    mart_dir.mkdir(parents=True, exist_ok=True)
    
    if run_date:
        mart_path = mart_dir / f"mart_{run_date}.csv"
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        mart_path = mart_dir / f"mart_yearly_{timestamp}.csv"
    
    df_mart.to_csv(mart_path, index=False, encoding='utf-8')
    print(f"✅ Mart сохранен: {mart_path}")
    
    if len(df_mart) > 0:
        print(f"\n📊 Статистика:")
        print(f"   Диапазон лет: {int(df_mart['year'].min())} - {int(df_mart['year'].max())}")
        print(f"   Количество строк: {len(df_mart)}")
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--run_date")
    parser.add_argument("--start")
    parser.add_argument("--end")
    args = parser.parse_args()
    
    success = transform(args.config, args.run_date, args.start, args.end)
    sys.exit(0 if success else 1)
