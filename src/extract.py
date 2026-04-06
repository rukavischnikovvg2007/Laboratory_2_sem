"""
ETL: Extract stage
Загрузка данных из World Bank API
"""

import requests
import yaml
import json
from datetime import datetime
from pathlib import Path
import sys

def extract(config_path):
    """Загружает данные из API и сохраняет в raw"""
    
    print("="*60)
    print("СТАДИЯ 1: EXTRACT (загрузка из API)")
    print("="*60)
    
    # 1. Загружаем конфиг
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Чтение конфига в зависимости от структуры
    # Если есть ключ 'variant' - используем его
    if 'variant' in config:
        variant_id = config['variant']['id']
        indicator = config['api']['indicator']
        country = config['api']['country']
    else:
        # Если конфиг старого формата (без variant)
        variant_id = f"variant_{config.get('variant_id', '10')}"
        indicator = config.get('indicator', 'NY.GDP.PCAP.CD')
        country = config.get('country', 'DE')
        
        # Если есть api вложенный
        if 'api' in config:
            indicator = config['api'].get('indicator', indicator)
            country = config['api'].get('country', country)
    
    print(f"📁 Вариант: {variant_id}")
    print(f"📊 Индикатор: {indicator}")
    print(f"🌍 Страна: {country}")
    
    # 2. Формируем URL
    url = f"http://api.worldbank.org/v2/country/{country}/indicator/{indicator}?format=json"
    print(f"🔗 URL: {url}")
    
    # 3. Делаем запрос
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
    
    # 4. Сохраняем в raw
    raw_dir = Path(f"data/raw/{variant_id}")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    raw_path = raw_dir / f"{timestamp}.json"
    
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Сохранено: {raw_path}")
    print(f"📦 Размер: {raw_path.stat().st_size} байт")
    
    # 5. Маленький отчёт
    if len(data) > 1 and len(data[1]) > 0:
        records = data[1]
        years = [item['date'] for item in records if item['value'] is not None]
        print(f"📊 Загружено {len(records)} записей, из них с данными: {len(years)} лет")
        if years:
            print(f"📅 Период: с {min(years)} по {max(years)}")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python extract.py <config_path>")
        print("Пример: python extract.py configs/variant_10.yml")
        sys.exit(1)
    
    extract(sys.argv[1])