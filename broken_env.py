import sys

# Ожидаем, что pandas установлен (сначала может не быть)
try:
    import pandas as pd
    print("python:", sys.executable)
    print("pandas version:", pd.__version__)  # Исправлено: было pd._version_, правильно pd.__version__
except ImportError as e:
    print("python:", sys.executable)
    print("ОШИБКА: Библиотека pandas не найдена:", e)
    sys.exit(1)  # Завершаем программу с кодом ошибки, если pandas нет