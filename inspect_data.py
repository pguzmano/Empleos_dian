import pandas as pd

try:
    df = pd.read_excel("EmpleosDIAN_2025.xlsx")
    print("Columns:", df.columns.tolist())
    # Print first few rows of potential vacancy columns
    for col in df.columns:
        if "vacan" in col.lower() or "cant" in col.lower():
            print(f"\nValues in '{col}':")
            print(df[col].head())
except Exception as e:
    print(e)
