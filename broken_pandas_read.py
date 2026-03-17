import pandas as pd
from io import StringIO

# "Битые" данные: разделитель ;, но pandas думает, что это запятая
csv_text = "id;value\n1;10\n2;20\n3;30"

# BUG: не указан разделитель -> pandas ожидает запятую
df = pd.read_csv(StringIO(csv_text), sep=";")

print("Типы столбцов:")
print(df.dtypes)

print("\nПытаемся посчитать среднее:")
print(df["value"].mean())  # ожидаем 20.0, но будет ошибка

print("\n" + "="*50)
print("ТЕСТ 1: Пустая строка")
print("="*50)

csv_text_2 = "id;value\n1;10\n\n3;30\n"
df2 = pd.read_csv(StringIO(csv_text_2), sep=";")
print(df2)
print("\nТипы:")
print(df2.dtypes)
print(f"Среднее: {df2['value'].mean()}")

print("\n" + "="*50)
print("ТЕСТ 2: Пропуск в value")
print("="*50)

csv_text_3 = "id;value\n1;10\n2;\n3;30"
df3 = pd.read_csv(StringIO(csv_text_3), sep=";")
print(df3)
print("\nТипы:")
print(df3.dtypes)
print(f"Среднее: {df3['value'].mean()}")
