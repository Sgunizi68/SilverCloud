import openpyxl

file_path = r"C:\Users\sg.msa\OneDrive - ÇELEBİ AVIATION\Personel\Programming\Yüklemeler\Archieve\Şube Bazlı Toplam Tabak Sayısı - 1.03.2026 06_00_00 - 23.03.2026 06_00_00.xlsx"
wb = openpyxl.load_workbook(file_path, data_only=True)
ws = wb.active

for i, row in enumerate(ws.iter_rows(values_only=True)):
    print(f"Row {i}: {row}")
    if i > 15:
        break
