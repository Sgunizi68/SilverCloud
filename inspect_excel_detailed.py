import pandas as pd

file_path = r"C:\Users\sg.msa\OneDrive - ÇELEBİ AVIATION\Personel\Programming\Yüklemeler\Archieve\export (3).xlsx"

try:
    df = pd.read_excel(file_path, header=None)
    header_row_idx = 0 # Based on previous run
    df_data = pd.read_excel(file_path, skiprows=header_row_idx)
    
    tarih_col = [c for c in df_data.columns if "tarih" in str(c).lower() or "date" in str(c).lower()][0]
    fisno_col = [c for c in df_data.columns if "fiş no" in str(c).lower() or "fis no" in str(c).lower()][0]
    
    results = []
    for i, row in df_data.iterrows():
        t_val = row[tarih_col]
        f_val = row[fisno_col]
        
        # Mimic JS logic: fisNo = String(row[foundHeaders.fisNo] || "").trim();
        f_str = str(f_val).strip() if pd.notna(f_val) else ""
        
        # Mimic JS logic: dateStr = parseDMYDateString(row[foundHeaders.tarih]);
        # parseDMYDateString handles DMY strings and Excel numbers
        t_ok = False
        if pd.notna(t_val):
            t_ok = True
            
        is_valid = bool(f_str and t_ok)
        results.append((i, t_val, f_str, is_valid))
        
    print(f"Index | Tarih | FisNo | Valid")
    for r in results:
        if not r[3]:
            print(f"{r[0]:5} | {r[1]} | {r[2]} | {r[3]}")
            
    print(f"\nTotal rows: {len(results)}")
    print(f"Valid rows: {sum(1 for r in results if r[3])}")

except Exception as e:
    print(f"Error: {e}")
