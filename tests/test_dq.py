"""
Модульные тесты для функций проверки качества данных
"""

import pytest
import pandas as pd
import sys
from pathlib import Path

# Добавляем путь к src для импорта
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.dq import DataQualityChecker


class TestDataQualityChecker:
    """Тесты для класса DataQualityChecker"""
    
    # ------------------------------------------------------------
    # ПОЗИТИВНЫЙ ТЕСТ: данные хорошие
    # ------------------------------------------------------------
    def test_check_not_empty_positive(self):
        """Позитивный тест: таблица не пустая"""
        df = pd.DataFrame({'col1': [1, 2, 3]})
        checker = DataQualityChecker(df, "test")
        checker.check_not_empty()
        
        assert checker.results[0]['status'] == 'PASS'
        assert '3 строк' in checker.results[0]['message']
    
    # ------------------------------------------------------------
    # НЕГАТИВНЫЙ ТЕСТ: таблица пустая
    # ------------------------------------------------------------
    def test_check_not_empty_negative(self):
        """Негативный тест: таблица пустая"""
        df = pd.DataFrame()
        checker = DataQualityChecker(df, "test")
        checker.check_not_empty()
        
        assert checker.results[0]['status'] == 'FAIL'
        assert 'пустая' in checker.results[0]['message']
    
    # ------------------------------------------------------------
    # ГРАНИЧНЫЙ ТЕСТ: таблица с одной строкой
    # ------------------------------------------------------------
    def test_check_not_empty_boundary(self):
        """Граничный тест: таблица с одной строкой"""
        df = pd.DataFrame({'col1': [1]})
        checker = DataQualityChecker(df, "test")
        checker.check_not_empty()
        
        assert checker.results[0]['status'] == 'PASS'
        assert '1 строк' in checker.results[0]['message']
    
    # ------------------------------------------------------------
    # ПОЗИТИВНЫЙ ТЕСТ: нет NULL
    # ------------------------------------------------------------
    def test_check_no_null_positive(self):
        """Позитивный тест: нет NULL в колонке"""
        df = pd.DataFrame({'col1': [1, 2, 3]})
        checker = DataQualityChecker(df, "test")
        checker.check_no_null_in_columns(['col1'], critical=True)
        
        assert checker.results[0]['status'] == 'PASS'
    
    # ------------------------------------------------------------
    # НЕГАТИВНЫЙ ТЕСТ: есть NULL
    # ------------------------------------------------------------
    def test_check_no_null_negative(self):
        """Негативный тест: есть NULL в колонке"""
        df = pd.DataFrame({'col1': [1, None, 3]})
        checker = DataQualityChecker(df, "test")
        checker.check_no_null_in_columns(['col1'], critical=True)
        
        assert checker.results[0]['status'] == 'FAIL'
        assert '1 NULL' in checker.results[0]['message']
    
    # ------------------------------------------------------------
    # ГРАНИЧНЫЙ ТЕСТ: колонка не существует
    # ------------------------------------------------------------
    def test_check_no_null_boundary(self):
        """Граничный тест: колонка не существует"""
        df = pd.DataFrame({'col1': [1, 2, 3]})
        checker = DataQualityChecker(df, "test")
        checker.check_no_null_in_columns(['non_existent'], critical=True)
        
        assert checker.results[0]['status'] == 'FAIL'
        assert 'не найдена' in checker.results[0]['message']
    
    # ------------------------------------------------------------
    # ПОЗИТИВНЫЙ ТЕСТ: уникальность ключа
    # ------------------------------------------------------------
    def test_check_unique_key_positive(self):
        """Позитивный тест: ключ уникален"""
        df = pd.DataFrame({'id': [1, 2, 3], 'name': ['A', 'B', 'C']})
        checker = DataQualityChecker(df, "test")
        checker.check_unique_key(['id'])
        
        assert checker.results[0]['status'] == 'PASS'
    
    # ------------------------------------------------------------
    # НЕГАТИВНЫЙ ТЕСТ: есть дубликаты
    # ------------------------------------------------------------
    def test_check_unique_key_negative(self):
        """Негативный тест: есть дубликаты ключа"""
        df = pd.DataFrame({'id': [1, 1, 2], 'name': ['A', 'A', 'B']})
        checker = DataQualityChecker(df, "test")
        checker.check_unique_key(['id'])
        
        assert checker.results[0]['status'] == 'FAIL'
        assert 'дубликатов' in checker.results[0]['message']
    
    # ------------------------------------------------------------
    # ГРАНИЧНЫЙ ТЕСТ: пустой DataFrame
    # ------------------------------------------------------------
    def test_check_unique_key_boundary(self):
        """Граничный тест: пустой DataFrame"""
        df = pd.DataFrame({'id': [], 'name': []})
        checker = DataQualityChecker(df, "test")
        checker.check_unique_key(['id'])
        
        assert checker.results[0]['status'] == 'PASS'
    
    # ------------------------------------------------------------
    # ПОЗИТИВНЫЙ ТЕСТ: значения в диапазоне
    # ------------------------------------------------------------
    def test_check_value_range_positive(self):
        """Позитивный тест: все значения в диапазоне"""
        df = pd.DataFrame({'value': [10, 20, 30]})
        checker = DataQualityChecker(df, "test")
        checker.check_value_range('value', min_val=0, max_val=100)
        
        assert checker.results[0]['status'] == 'PASS'
    
    # ------------------------------------------------------------
    # НЕГАТИВНЫЙ ТЕСТ: значения вне диапазона
    # ------------------------------------------------------------
    def test_check_value_range_negative(self):
        """Негативный тест: значения вне диапазона"""
        df = pd.DataFrame({'value': [-10, 20, 200]})
        checker = DataQualityChecker(df, "test")
        checker.check_value_range('value', min_val=0, max_val=100)
        
        assert checker.results[0]['status'] == 'FAIL'
        # Проверяем, что в сообщении есть слово о нарушениях
        message = checker.results[0]['message']
        assert 'Нарушения' in message or 'нарушения' in message
    
    # ------------------------------------------------------------
    # ГРАНИЧНЫЙ ТЕСТ: все значения NULL
    # ------------------------------------------------------------
    def test_check_value_range_boundary(self):
        """Граничный тест: все значения NULL"""
        df = pd.DataFrame({'value': [None, None, None]})
        checker = DataQualityChecker(df, "test")
        checker.check_value_range('value', min_val=0, max_val=100)
        
        assert checker.results[0]['status'] == 'WARNING'


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
