import requests
import yaml
import json
from datetime import datetime
from pathlib import Path

# Загружаем конфиг
config_path = Path("configs/variant_10.yml")
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# Извлекаем нужные поля
variant_id = config.get("variant_id", "unknown")
base_url = config['api']['base_url']
endpoint = config['api']['request_template']
params = config['api']['params']

# Полный URL
url = f"{base_url}{endpoint}"
print(f"[INFO] Вариант: {variant_id}")
print(f"[INFO] Запрашиваю URL: {url}")
print(f"[INFO] Параметры: {params}")

# Делаем запрос
try:
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    # Папка: data/raw/variant_10/
    raw_dir = Path("data/raw") / f"variant_{variant_id}"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Имя файла: YYYY-MM-DD_HH-MM-SS.json
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = raw_dir / f"{timestamp}.json"

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[OK] Данные сохранены в {filename}")

    # Маленький отчёт
    if len(data) > 1 and len(data[1]) > 0:
        records = data[1]
        years = [item['date'] for item in records if item['value'] is not None]
        print(f"[INFO] Загружено {len(records)} записей, из них с данными: {len(years)} лет")
        print(f"[INFO] Период: с {min(years)} по {max(years)}")
        print(f"[INFO] Размер файла: {filename.stat().st_size} байт")
    else:
        print("[WARNING] Структура ответа необычная, проверь файл вручную")

except requests.exceptions.Timeout:
    print("[ERROR] Таймаут: сервер не ответил за 30 секунд")
    exit(1)
except requests.exceptions.HTTPError as e:
    print(f"[ERROR] HTTP ошибка: {e}")
    exit(1)
except requests.exceptions.RequestException as e:
    print(f"[ERROR] Ошибка сети/запроса: {e}")
    exit(1)
except Exception as e:
    print(f"[ERROR] Непредвиденная ошибка: {e}")
    exit(1)
