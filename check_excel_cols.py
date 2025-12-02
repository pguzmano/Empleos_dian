import pandas as pd
import os

file_path = "EmpleosDIAN_2025.xlsx"
if os.path.exists(file_path):
    try:
        df = pd.read_excel(file_path)
        print("Columns found in Excel file:")
        for col in df.columns:
            print(f"- {col}")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
else:
    print(f"File not found: {file_path}")
