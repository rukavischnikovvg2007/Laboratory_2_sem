"""
Модуль проверки качества данных (Data Quality)
Содержит функции для проверки данных и генерации отчета
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class DataQualityChecker:
    """Класс для проверки качества данных"""
    
    def __init__(self, df: pd.DataFrame, source_name: str = "unknown"):
        """
        Инициализация проверки качества
        
        Args:
            df: DataFrame для проверки
            source_name: Название источника (normalized/mart)
        """
        self.df = df
        self.source_name = source_name
        self.results: List[Dict[str, Any]] = []
        
    def add_result(self, name: str, status: str, message: str, details: Any = None):
        """Добавляет результат проверки"""
        self.results.append({
            "check_name": name,
            "status": status,  # PASS, FAIL, WARNING
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    def check_not_empty(self) -> None:
        """Проверка 1: Таблица не пустая"""
        print("\n1. Проверка: таблица не пустая")
        
        if len(self.df) == 0:
            self.add_result(
                "Таблица не пустая",
                "FAIL",
                f"Таблица пустая! 0 строк"
            )
            print("   ❌ FAIL: таблица пустая")
        else:
            self.add_result(
                "Таблица не пустая",
                "PASS",
                f"Таблица содержит {len(self.df)} строк"
            )
            print(f"   ✅ PASS: {len(self.df)} строк")
    
    def check_no_null_in_columns(self, columns: List[str], critical: bool = True) -> None:
        """
        Проверка 2: Нет NULL в критических колонках
        
        Args:
            columns: список колонок для проверки
            critical: если True -> FAIL, если False -> WARNING
        """
        print(f"\n2. Проверка: нет NULL в колонках {columns}")
        
        for col in columns:
            if col not in self.df.columns:
                self.add_result(
                    f"NULL в колонке '{col}'",
                    "FAIL" if critical else "WARNING",
                    f"Колонка '{col}' не найдена в данных!"
                )
                print(f"   ❌ FAIL: колонка '{col}' не найдена")
                continue
                
            null_count = self.df[col].isna().sum()
            null_percent = (null_count / len(self.df)) * 100 if len(self.df) > 0 else 0
            
            if null_count == 0:
                self.add_result(
                    f"NULL в колонке '{col}'",
                    "PASS",
                    f"Нет NULL в колонке '{col}'"
                )
                print(f"   ✅ PASS: колонка '{col}' — нет NULL")
            else:
                status = "FAIL" if critical else "WARNING"
                self.add_result(
                    f"NULL в колонке '{col}'",
                    status,
                    f"Найдено {null_count} NULL ({null_percent:.1f}%) в колонке '{col}'"
                )
                print(f"   ❌ {status}: колонка '{col}' — {null_count} NULL")
    
    def check_unique_key(self, key_columns: List[str]) -> None:
        """
        Проверка 3: Уникальность бизнес-ключа
        
        Args:
            key_columns: список колонок, образующих бизнес-ключ
        """
        print(f"\n3. Проверка: уникальность ключа {key_columns}")
        
        # Проверяем, что все колонки существуют
        missing_cols = [col for col in key_columns if col not in self.df.columns]
        if missing_cols:
            self.add_result(
                f"Уникальность ключа {key_columns}",
                "FAIL",
                f"Колонки не найдены: {missing_cols}"
            )
            print(f"   ❌ FAIL: колонки не найдены: {missing_cols}")
            return
        
        # Проверяем дубликаты
        duplicates = self.df.duplicated(subset=key_columns).sum()
        
        if duplicates == 0:
            self.add_result(
                f"Уникальность ключа {key_columns}",
                "PASS",
                f"Ключ уникален, дубликатов нет"
            )
            print(f"   ✅ PASS: дубликатов нет")
        else:
            # Показываем примеры дубликатов
            dup_examples = self.df[self.df.duplicated(subset=key_columns, keep=False)]
            dup_examples_str = dup_examples[key_columns].head(3).to_dict('records')
            
            self.add_result(
                f"Уникальность ключа {key_columns}",
                "FAIL",
                f"Найдено {duplicates} дубликатов",
                details={"examples": dup_examples_str}
            )
            print(f"   ❌ FAIL: {duplicates} дубликатов")
    
    def check_value_range(self, column: str, min_val: float = None, max_val: float = None) -> None:
        """
        Проверка 4: Диапазон значений
        
        Args:
            column: имя колонки
            min_val: минимальное допустимое значение
            max_val: максимальное допустимое значение
        """
        print(f"\n4. Проверка: диапазон значений в колонке '{column}'")
        
        if column not in self.df.columns:
            self.add_result(
                f"Диапазон значений в '{column}'",
                "FAIL",
                f"Колонка '{column}' не найдена!"
            )
            print(f"   ❌ FAIL: колонка '{column}' не найдена")
            return
        
        # Убираем NULL для проверки
        values = self.df[column].dropna()
        
        if len(values) == 0:
            self.add_result(
                f"Диапазон значений в '{column}'",
                "WARNING",
                f"Нет данных для проверки (все NULL)"
            )
            print(f"   ⚠️ WARNING: нет данных для проверки")
            return
        
        violations = []
        
        if min_val is not None:
            below_min = (values < min_val).sum()
            if below_min > 0:
                violations.append(f"{below_min} значений меньше {min_val}")
        
        if max_val is not None:
            above_max = (values > max_val).sum()
            if above_max > 0:
                violations.append(f"{above_max} значений больше {max_val}")
        
        if violations:
            self.add_result(
                f"Диапазон значений в '{column}'",
                "FAIL",
                f"Нарушения: {', '.join(violations)}"
            )
            print(f"   ❌ FAIL: {', '.join(violations)}")
        else:
            self.add_result(
                f"Диапазон значений в '{column}'",
                "PASS",
                f"Все значения в диапазоне [{min_val}, {max_val}]"
            )
            print(f"   ✅ PASS: все значения в допустимом диапазоне")
    
    def check_column_types(self, expected_types: Dict[str, str]) -> None:
        """
        Проверка 5: Типы данных колонок
        
        Args:
            expected_types: словарь {column_name: expected_type}
        """
        print(f"\n5. Проверка: типы данных колонок")
        
        for col, expected_type in expected_types.items():
            if col not in self.df.columns:
                self.add_result(
                    f"Тип данных в '{col}'",
                    "FAIL",
                    f"Колонка '{col}' не найдена!"
                )
                print(f"   ❌ FAIL: колонка '{col}' не найдена")
                continue
            
            actual_type = str(self.df[col].dtype)
            
            # Простое сопоставление типов
            type_mapping = {
                'int': 'int64',
                'float': 'float64',
                'string': 'object',
                'datetime': 'datetime64[ns]'
            }
            
            expected_normalized = type_mapping.get(expected_type, expected_type)
            
            if actual_type == expected_normalized or expected_type in actual_type:
                self.add_result(
                    f"Тип данных в '{col}'",
                    "PASS",
                    f"Тип '{actual_type}' соответствует ожидаемому '{expected_type}'"
                )
                print(f"   ✅ PASS: колонка '{col}' — {actual_type}")
            else:
                self.add_result(
                    f"Тип данных в '{col}'",
                    "WARNING",
                    f"Ожидался {expected_type}, получен {actual_type}"
                )
                print(f"   ⚠️ WARNING: колонка '{col}' — ожидался {expected_type}, получен {actual_type}")
    
    def check_no_negative_values(self, column: str) -> None:
        """
        Проверка 6: Нет отрицательных значений (для стоимостных показателей)
        """
        print(f"\n6. Проверка: нет отрицательных значений в '{column}'")
        
        if column not in self.df.columns:
            self.add_result(
                f"Отрицательные значения в '{column}'",
                "FAIL",
                f"Колонка '{column}' не найдена!"
            )
            print(f"   ❌ FAIL: колонка '{column}' не найдена")
            return
        
        negative_count = (self.df[column] < 0).sum()
        
        if negative_count == 0:
            self.add_result(
                f"Отрицательные значения в '{column}'",
                "PASS",
                f"Нет отрицательных значений"
            )
            print(f"   ✅ PASS: нет отрицательных значений")
        else:
            self.add_result(
                f"Отрицательные значения в '{column}'",
                "FAIL",
                f"Найдено {negative_count} отрицательных значений"
            )
            print(f"   ❌ FAIL: {negative_count} отрицательных значений")
    
    def generate_report(self) -> Dict[str, Any]:
        """Генерирует итоговый отчет"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        warnings = sum(1 for r in self.results if r['status'] == 'WARNING')
        
        report = {
            "source": self.source_name,
            "timestamp": datetime.now().isoformat(),
            "rows_checked": len(self.df),
            "summary": {
                "total_checks": total,
                "passed": passed,
                "failed": failed,
                "warnings": warnings
            },
            "results": self.results
        }
        
        return report
    
    def print_summary(self):
        """Печатает краткую сводку"""
        print("\n" + "="*60)
        print("ИТОГИ ПРОВЕРОК КАЧЕСТВА")
        print("="*60)
        
        for r in self.results:
            status_icon = "✅" if r['status'] == 'PASS' else "❌" if r['status'] == 'FAIL' else "⚠️"
            print(f"{status_icon} {r['check_name']}: {r['status']}")
            print(f"   {r['message']}")
            print()
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        warnings = sum(1 for r in self.results if r['status'] == 'WARNING')
        
        print("="*60)
        print(f"Всего проверок: {total}")
        print(f"✅ PASS: {passed}")
        print(f"❌ FAIL: {failed}")
        print(f"⚠️ WARNING: {warnings}")
        print("="*60)


def run_dq_checks(data_path: str, source_name: str = "mart") -> Dict[str, Any]:
    """
    Запускает все проверки качества для указанного файла
    
    Args:
        data_path: путь к CSV файлу
        source_name: название источника
    """
    print("="*60)
    print("ЗАПУСК ПРОВЕРОК КАЧЕСТВА ДАННЫХ")
    print("="*60)
    print(f"Источник: {source_name}")
    print(f"Файл: {data_path}")
    
    # Загружаем данные
    df = pd.read_csv(data_path)
    print(f"Загружено {len(df)} строк, {len(df.columns)} колонок")
    
    # Создаем проверяльщик
    checker = DataQualityChecker(df, source_name)
    
    # Проверка 1: таблица не пустая
    checker.check_not_empty()
    
    # Проверка 2: NULL в ключевых колонках
    checker.check_no_null_in_columns(['year', 'country_iso3', 'indicator_code'], critical=True)
    checker.check_no_null_in_columns(['value'], critical=False)  # WARNING, а не FAIL
    
    # Проверка 3: уникальность бизнес-ключа
    checker.check_unique_key(['year', 'country_iso3', 'indicator_code'])
    
    # Проверка 4: диапазон значений
    checker.check_value_range('year', min_val=1960, max_val=2030)
    checker.check_value_range('value', min_val=0, max_val=100000)
    
    # Проверка 5: типы данных
    checker.check_column_types({
        'year': 'int',
        'value': 'float',
        'country_iso3': 'string',
        'indicator_code': 'string'
    })
    
    # Проверка 6: нет отрицательных значений
    checker.check_no_negative_values('value')
    
    # Печатаем сводку
    checker.print_summary()
    
    # Возвращаем отчет
    return checker.generate_report()


if __name__ == "__main__":
    # Запуск для mart-файла
    mart_dir = Path("data/mart/variant_10")
    mart_files = list(mart_dir.glob("mart_yearly_*.csv"))
    
    if mart_files:
        latest_mart = max(mart_files, key=lambda p: p.stat().st_mtime)
        report = run_dq_checks(str(latest_mart), "mart_world_bank")
        
        # Сохраняем отчет
        report_path = Path("data/dq_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Отчет сохранен: {report_path}")
    else:
        print("❌ Не найден mart-файл!")