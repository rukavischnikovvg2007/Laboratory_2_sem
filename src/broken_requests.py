import requests
from requests.exceptions import Timeout, HTTPError, RequestException

# === НАСТРОЙКИ ===
TIMEOUT = 5  # секунд

# URL для разных тестов (можно менять)
# TEST_URL = "https://httpbin.org/delay/10"          # медленный ответ
# TEST_URL = "https://httpbin.org/status/404"        # ошибка 404
# TEST_URL = "https://httpbin.org/html"              # ответ не JSON
TEST_URL = "https://api.worldbank.org/v2/country/DEU/indicator/NY.GDP.PCAP.CD?format=json"  # рабочий

print(f"[INFO] Запрашиваю URL: {TEST_URL}")
print(f"[INFO] Таймаут: {TIMEOUT} сек")

try:
    # 1. Запрос с таймаутом
    response = requests.get(TEST_URL, timeout=TIMEOUT)

    # 2. Проверка HTTP-статуса
    response.raise_for_status()

    # 3. Пробуем распарсить JSON
    try:
        data = response.json()
        print("[OK] Ответ получен и распарсен как JSON")

        # 4. Небольшой анализ (если это API World Bank)
        if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
            records = data[1]
            years = [item['date'] for item in records if item.get('value') is not None]
            print(f"[INFO] Записей с данными: {len(years)}")
            if years:
                print(f"[INFO] Период: {min(years)} - {max(years)}")
        else:
            print("[INFO] Структура ответа:", type(data))

    except ValueError:
        print("[ERROR] Ответ не является валидным JSON")
        print("Первые 200 символов ответа:", response.text[:200])

except Timeout:
    print(f"[ERROR] Таймаут: сервер не ответил за {TIMEOUT} секунд")
except HTTPError as e:
    print(f"[ERROR] HTTP ошибка: {e}")
except RequestException as e:
    print(f"[ERROR] Ошибка сети/запроса: {e}")
except Exception as e:
    print(f"[ERROR] Непредвиденная ошибка: {e}")
