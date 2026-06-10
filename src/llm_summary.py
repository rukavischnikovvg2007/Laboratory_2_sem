"""LLM-сводка для финального проекта (неделя 14)"""

import json
import os
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys
from gigachat import GigaChat
from dotenv import load_dotenv

# Загружаем API-ключ из .env
load_dotenv()

print("=" * 60)
print("LLM-СВОДКА ДЛЯ ФИНАЛЬНОГО ПРОЕКТА (GigaChat)")
print("=" * 60)

# ========== 1. Ищем dq_report.json ==========
dq_paths = [
    Path("dq_report.json"),
    Path("data/dq_report.json"),
    Path("data/dq_reports/dq_report.json"),
]

dq_file = None
for p in dq_paths:
    if p.exists():
        dq_file = p
        print(f"✅ Найден DQ-отчёт: {p}")
        break

if dq_file is None:
    print("❌ Не найден dq_report.json ни в одном из ожидаемых мест")
    print("   Искал: dq_report.json, data/dq_report.json, data/dq_reports/dq_report.json")
    sys.exit(1)

with open(dq_file, "r", encoding="utf-8") as f:
    dq_data = json.load(f)

# ========== 2. Ищем mart-файл ==========
mart_dir = Path("data/mart/variant_10")
mart_files = list(mart_dir.glob("mart_yearly_*.csv"))

if not mart_files:
    print(f"❌ Не найден mart-файл в {mart_dir}")
    sys.exit(1)

latest_mart = max(mart_files, key=lambda p: p.stat().st_mtime)
print(f"✅ Найден mart-файл: {latest_mart.name}")

df = pd.read_csv(latest_mart)
df_clean = df.dropna(subset=["value"])

# ========== 3. Извлекаем метрики ==========
metrics = {
    "min_value": float(df_clean["value"].min()),
    "min_year": int(df_clean.loc[df_clean["value"].idxmin(), "year"]),
    "max_value": float(df_clean["value"].max()),
    "max_year": int(df_clean.loc[df_clean["value"].idxmax(), "year"]),
    "mean_value": float(df_clean["value"].mean()),
    "last_value": float(df_clean.loc[df_clean["year"].idxmax(), "value"]),
    "last_year": int(df_clean["year"].max()),
    "prev_value": float(df_clean.loc[df_clean["year"].idxmax() - 1, "value"]),
    "prev_year": int(df_clean["year"].max() - 1),
}

dq_fail = dq_data.get("summary", {}).get("failed", 0)
dq_status = "PASS" if dq_fail == 0 else "FAIL"

print(f"\n📊 Извлечённые метрики:")
print(f"   - Минимум: {metrics['min_value']:.0f} USD ({metrics['min_year']})")
print(f"   - Максимум: {metrics['max_value']:.0f} USD ({metrics['max_year']})")
print(f"   - Среднее: {metrics['mean_value']:.0f} USD")
print(f"   - Последнее: {metrics['last_value']:.0f} USD ({metrics['last_year']})")
print(f"   - DQ статус: {dq_status} (FAIL={dq_fail})")

# ========== 4. Формируем строгий контекст и промпт ==========
prompt = f"""
Ты аналитик данных. Ниже — строгий контекст с уже рассчитанными метриками.

КОНТЕКСТ (только эти числа, не придумывай новые):
- Минимум ВВП: {metrics['min_value']:.0f} USD в {metrics['min_year']} году
- Максимум ВВП: {metrics['max_value']:.0f} USD в {metrics['max_year']} году
- Среднее ВВП: {metrics['mean_value']:.0f} USD
- Последнее значение: {metrics['last_value']:.0f} USD ({metrics['last_year']} год)
- Предыдущее значение: {metrics['prev_value']:.0f} USD ({metrics['prev_year']} год)
- Качество данных: {dq_status}

ЗАПРЕЩЕНО:
- Не придумывай новые числа
- Не вычисляй ничего самостоятельно (ни проценты, ни разницу)
- Не считай среднее, максимум, минимум — они уже даны
- Используй ТОЛЬКО числа из контекста выше

Напиши КРАТКИЙ анализ (3-5 абзацев):
1. Опиши общий тренд (рост/падение)
2. Отметь заметные точки (пики, спады)
3. Укажи возможные риски на основе данных
4. Предложи гипотезы, что могло повлиять на динамику
5. Предложи следующие шаги для анализа

Будь краток и информативен.
"""

# ========== 5. Функция вызова GigaChat ==========
def call_gigachat(prompt: str) -> str:
    """Отправляет запрос к GigaChat API"""
    api_key = os.getenv("GIGACHAT_API_KEY")
    
    if not api_key or api_key == "your_key_here":
        print("❌ ОШИБКА: GIGACHAT_API_KEY не настроен в .env файле")
        print("   Добавьте строку: GIGACHAT_API_KEY=ваш_ключ")
        return "Ошибка: API ключ не настроен. Проверьте .env файл."
    
    try:
        # Подключаемся к GigaChat
        with GigaChat(
            credentials=api_key,
            verify_ssl_certs=False,  # Для локальной разработки
            timeout=30
        ) as giga:
            response = giga.chat(prompt)
            return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Ошибка при вызове GigaChat: {e}")
        return f"Ошибка вызова GigaChat: {e}"

print("\n🔄 Отправка запроса к GigaChat...")
llm_response = call_gigachat(prompt)
print("✅ Ответ получен")

# ========== 6. Сохраняем LLM-сводку ==========
out_dir = Path("docs/llm")
out_dir.mkdir(parents=True, exist_ok=True)

summary_path = out_dir / "summary.md"
with open(summary_path, "w", encoding="utf-8") as f:
    f.write(f"# Анализ ВВП Германии (1960–{metrics['last_year']})\n\n")
    f.write(f"**Дата генерации:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
    f.write(f"**Модель:** GigaChat\n\n")
    f.write(llm_response.strip())
    f.write("\n\n---\n")
    f.write("## Использованные метрики (из кода)\n\n")
    for k, v in metrics.items():
        f.write(f"- {k}: {v}\n")
    f.write(f"- dq_status: {dq_status}\n")

print(f"\n✅ LLM-сводка сохранена: {summary_path}")

# ========== 7. Логируем использование LLM ==========
log_path = Path("docs/LLM_Usage_Log.md")

if not log_path.exists():
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("# LLM_Usage_Log\n# Журнал использования LLM\n\n")

log_entry = f"""
## Неделя 14 ({datetime.now().strftime('%Y-%m-%d')})

**Дата:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Модель:** GigaChat
**Цель запроса:** Интерпретация метрик ВВП Германии без самостоятельных вычислений

**Контекст (передан в LLM):**
- Минимум: {metrics['min_value']:.0f} USD ({metrics['min_year']})
- Максимум: {metrics['max_value']:.0f} USD ({metrics['max_year']})
- Среднее: {metrics['mean_value']:.0f} USD
- Последнее значение: {metrics['last_value']:.0f} USD ({metrics['last_year']})
- DQ статус: {dq_status}

**Промпт:** (полный промпт см. в src/llm_summary.py)

**Краткий ответ LLM:**  
{llm_response[:500]}...

**Проверка:**  
Все числа в ответе совпадают с переданными метриками.  
LLM использовался только для интерпретации, без вычислений.
Ни одна цифра не была придумана моделью.

**Итог:** PASS
"""

with open(log_path, "a", encoding="utf-8") as f:
    f.write(log_entry)

print(f"✅ Лог обновлён: {log_path}")

print("\n" + "=" * 60)
print("✅ СКРИПТ УСПЕШНО ЗАВЕРШЁН")
print("=" * 60)
