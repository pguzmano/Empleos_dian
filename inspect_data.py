import pandas as pd
import os

file_path = r'c:/Users/Pedro Luis/Downloads/Empleos_dian/EmpleosDIAN_2025.xlsx'

try:
    df = pd.read_excel(file_path)
    print("Columns:")
    for col in df.columns:
        print(f"- {col}")
    print("\nFirst 3 rows:")
    print(df.head(3))
except Exception as e:
    print(f"Error reading file: {e}")
