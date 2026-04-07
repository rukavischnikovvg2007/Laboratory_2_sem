"""
ETL Pipeline: Единая команда для запуска всего пайплайна
python -m src.pipeline --config configs/variant_10.yml --mode full
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import yaml

# Импортируем наши стадии
from src.extract import extract
from src.transform import transform
from src.load import load

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

def load_state(state_path):
    """Загружает состояние пайплайна из JSON файла"""
    if state_path.exists():
        with open(state_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "variant_id": None,
        "source_type": "world_bank",
        "last_successful_run": None,
        "last_watermark": None,
        "mode": None
    }

def save_state(state_path, state):
    """Сохраняет состояние пайплайна в JSON файл"""
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def run_pipeline(config_path, mode="full"):
    """Запускает весь ETL пайплайн"""
    
    print("="*70)
    print("🚀 ЗАПУСК ETL ПАЙПЛАЙНА")
    print("="*70)
    print(f"Конфиг: {config_path}")
    print(f"Режим: {mode}")
    print()
    
    # 1. Загружаем состояние
    state_path = Path("data/state/state.json")
    state = load_state(state_path)
    print(f"📁 Состояние загружено из {state_path}")
    print(f"   Последний успешный запуск: {state.get('last_successful_run', 'никогда')}")
    print(f"   Watermark: {state.get('last_watermark', 'нет')}")
    print()
    
    # 2. EXTRACT
    if not extract(config_path):
        print("❌ Пайплайн остановлен на стадии EXTRACT")
        return False
    
    # 3. TRANSFORM
    if not transform(config_path):
        print("❌ Пайплайн остановлен на стадии TRANSFORM")
        return False
    
    # 4. LOAD
    if not load(config_path, mode):
        print("❌ Пайплайн остановлен на стадии LOAD")
        return False
    
    # 5. Обновляем состояние
    state['last_successful_run'] = datetime.now().isoformat()
    state['mode'] = mode
    
    # Получаем variant_id из конфига (безопасно, поддерживая разные форматы)
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Пытаемся получить variant_id разными способами
    variant_id = get_nested_value(config, ['variant', 'id'])
    if not variant_id:
        variant_num = get_nested_value(config, ['variant_id'], '10')
        variant_id = f"variant_{variant_num}"
    
    state['variant_id'] = variant_id
    print(f"📌 variant_id: {variant_id}")
    
    # Обновляем watermark (максимальный год из mart)
    mart_dir = Path(f"data/mart/{variant_id}")
    mart_files = list(mart_dir.glob("mart_yearly_*.csv"))
    if mart_files:
        latest_mart = max(mart_files, key=lambda p: p.stat().st_mtime)
        df = pd.read_csv(latest_mart)
        state['last_watermark'] = int(df['year'].max())
        print(f"📌 Watermark обновлен: {state['last_watermark']}")
    
    save_state(state_path, state)
    print(f"\n💾 Состояние сохранено в {state_path}")
    
    print("\n" + "="*70)
    print("✅ ETL ПАЙПЛАЙН УСПЕШНО ЗАВЕРШЕН!")
    print("="*70)
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Запуск ETL пайплайна")
    parser.add_argument("--config", required=True, help="Путь к конфиг файлу")
    parser.add_argument("--mode", choices=["full", "incremental"], default="full", 
                        help="Режим запуска: full (полная перезагрузка) или incremental (только новые данные)")
    
    args = parser.parse_args()
    
    success = run_pipeline(args.config, args.mode)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
