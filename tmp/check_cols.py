import pandas as pd

file_path = r"C:\Users\sg.msa\OneDrive - ÇELEBİ AVIATION\Personel\Programming\Yüklemeler\Archieve\Şube Bazlı Toplam Tabak Sayısı - 1.03.2026 06_00_00 - 23.03.2026 06_00_00.xlsx"
df = pd.read_excel(file_path)

print("Columns:")
print(df.columns.tolist())

print("\nFirst row:")
print(df.iloc[0].to_dict())
