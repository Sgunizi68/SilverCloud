import pandas as pd

file_path = r'c:\projects\SilverCloud\Kazanç Raporu - 1.04.2026 06_00_00 - 1.05.2026 06_00_00.xlsx'
df = pd.read_excel(file_path, header=None)

print("--- First 5 rows and 10 columns ---")
print(df.iloc[:10, :10].to_string())

print("\n--- Columns ---")
print(df.iloc[0, :].tolist())
