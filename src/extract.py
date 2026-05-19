"""
ETL: Extract stage
Загрузка данных из World Bank API
"""

import os
import requests
import yaml
import json
from datetime import datetime
from pathlib import Path
import sys
import argparse

# Устанавливаем рабочую директорию
if os.path.exists("/opt/airflow"):
    os.chdir("/opt/airflow")
    print("📁 Working directory:", os.getcwd())

def extract(config_path, run_date=None, start_date=None, end_date=None):
    print("="*60)
    print("СТАДИЯ 1: EXTRACT (загрузка из API)")
    print("="*60)
    
    if run_date:
        print(f"📅 Run date: {run_date}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    if 'variant' in config:
        variant_id = config['variant']['id']
        indicator = config['api']['indicator']
        country = config['api']['country']
    else:
        variant_id = f"variant_{config.get('variant_id', '10')}"
        indicator = config.get('indicator', 'NY.GDP.PCAP.CD')
        country = config.get('country', 'DE')
        if 'api' in config:
            indicator = config['api'].get('indicator', indicator)
            country = config['api'].get('country', country)
    
    print(f"📁 Вариант: {variant_id}")
    print(f"📊 Индикатор: {indicator}")
    print(f"🌍 Страна: {country}")
    
    url = f"http://api.worldbank.org/v2/country/{country}/indicator/{indicator}?format=json"
    print(f"🔗 URL: {url}")
    
    print("\n⏳ Загрузка данных...")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        print("✅ Данные успешно загружены")
    except requests.exceptions.Timeout:
        print("[ERROR] Таймаут: сервер не ответил за 30 секунд")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP ошибка: {e}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Ошибка сети/запроса: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Непредвиденная ошибка: {e}")
        return False
    
    # Берём записи из ответа API
    if isinstance(data, list) and len(data) > 1:
        records = data[1]
    else:
        records = data
    
    print(f"📊 Загружено записей: {len(records)}")
    
    # Сохраняем в raw (с привязкой к run_date)
    raw_dir = Path(f"data/raw/{variant_id}")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    if run_date:
        filename = f"raw_{run_date}.json"
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{timestamp}.json"
    
    raw_path = raw_dir / filename
    
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Сохранено: {raw_path}")
    print(f"📦 Размер: {raw_path.stat().st_size} байт")
    
    # Отчёт по годам
    if len(records) > 0:
        years = [item.get('date') for item in records if item.get('value') is not None]
        print(f"📊 С данными: {len(years)} лет")
        if years:
            print(f"📅 Период: с {min(years)} по {max(years)}")
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--run_date")
    parser.add_argument("--start")
    parser.add_argument("--end")
    args = parser.parse_args()
    
    success = extract(args.config, args.run_date, args.start, args.end)
    sys.exit(0 if success else 1)
