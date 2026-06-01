# Laboratory_2_sem

Описание моего первого проекта по анализу данных.

# ETL проект: данные World Bank (вариант 10)

Проект по извлечению, трансформации и загрузке данных из World Bank API с последующим анализом, проверкой качества данных и визуализацией.

---

## Быстрый запуск
### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```
### 2. Запуск ETL пайплайна
```bash
python -m src.pipeline --config configs/variant_10.yml --mode full
```
### 3. Запуск проверок качества данных
```bash
python src/dq.py
```
### 4. Просмотр отчётов

| Артефакт | Путь |
|----------|------|
| DQ отчёт | data/dq_report.json |
| BI дашборд |	Скриншоты в docs/bi/ |
| Анализ аномалий	| notebooks/week13_ml.ipynb |
| LLM сводка |	docs/llm/summary.md |
| Правила LLM |	docs/llm_rules.md |
| Лог использования | LLM	docs/LLM_Usage_Log.md |

---

## Структура проекта
```text
Laboratory_2_sem-main/
├── src/                   # Исходный код
│   ├── diagnostic_append.py
│   ├── diagnostic_assert.py
│   ├── diagnostic_dates.py
│   ├── diagnostic_units.py
│   ├── load.py
│   ├── sql_checks.py
│   ├── transaction_demo.py
│   ├── extract.py          # Извлечение данных из API
│   ├── transform.py        # Трансформация в normalized и mart
│   ├── load_to_postgres.py # Загрузка в PostgreSQL
│   ├── dq.py               # Проверки качества данных
│   ├── pipeline.py         # ETL пайплайн
│   └── __init__.py
├── data/                   # Данные
│   ├── mart.db
│   ├── raw/                # Сырые данные из API
│   ├── normalized/         # Нормализованные данные
│   ├── mart/               # Витрина данных
│   └── state/             
|       └── state.json      # Отчёт о качестве данных
├── configs/                # Конфигурационные файлы
│   └── variant_10.yml
├── docs/                   # Документация и отчёты
│   ├── sql_checks.md
│   ├── Airflow/
│   ├── figures/
│   ├── ml/
│   ├── Data_Contract.md
│   ├── Implementation_Plan.md
│   ├── data_dictionary.md
│   ├── bi/                 # Скриншоты BI дашборда
|       ├── chart_ranking.png
|       ├── chart_timeseries.png
|       └── dashboard_overview.png
│   ├── llm/                # LLM сводка
|       └── summary.md
│   ├── llm_rules.md        # Правила использования LLM
│   └── LLM_Usage_Log.md    # Журнал работы с LLM
├── notebooks/              # Jupyter ноутбуки
│   ├── week3_eda.ipynb
│   ├── week4_mart.ipynb
│   ├── week7_viz.ipynb
│   ├── broken_week13_ml.ipynb
│   └── week13_ml.ipynb     # Анализ аномалий
├── reference/              # Справочные данные
│   └── countries.csv       # Справочник стран
├── tests/                  # Тесты
│   └── test_dq.py          # Тесты DQ модуля
├── .env
├── broken_env.py
├── broken_pandas_read.py
├── broken_requests.py
├── docker-compose.no-volume.yml
├── load_to_postgres.py
├── many_to_many_demo.py
├── dq_report.json
├── docker-compose.yaml     # Docker для Airflow
├── docker-compose-postgres.yml  # Docker для PostgreSQL и Metabase
├── requirements.txt        # Зависимости Python
└── README.md               # Этот файл
```
---

### Данные
- Источник: World Bank API
- Индикатор: GDP per capita (current US$) — NY.GDP.PCAP.CD
- Страна: Germany (DE)
- Период: 1960 — 2024

---

## Результаты анализа
### Основные метрики ВВП Германии
Метрика	Значение	Год
Минимум	1,162 USD	1960
Максимум	56,103 USD	2024
Среднее	~25,000 USD	1960-2024

### Ключевые выводы
- Рост с 1960 по 1990 год
- Резкий скачок в 1990 (объединение Германии)
- Падение в 2009 (мировой финансовый кризис)
- Падение в 2020 (пандемия COVID-19)
- Восстановление и рост после 2021 года

---

### Качество данных
- DQ проверки пройдены: 12 PASS, 0 FAIL, 1 WARNING
- WARNING: значение за 2025 год отсутствует (данные ещё не опубликованы)

---

### Использование LLM
- В проекте LLM используется только для интерпретации уже рассчитанных метрик, а не для вычислений. Правила описаны в docs/llm_rules.md.




