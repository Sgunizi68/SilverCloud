import pandas as pd

file_path = r"C:\Users\sg.msa\OneDrive - ÇELEBİ AVIATION\Personel\Programming\Yüklemeler\Archieve\export (3).xlsx"

try:
    df_data = pd.read_excel(file_path, skiprows=0)
    
    tarih_col = [c for c in df_data.columns if "tarih" in str(c).lower() or "date" in str(c).lower()][0]
    fisno_col = [c for c in df_data.columns if "fiş no" in str(c).lower() or "fis no" in str(c).lower()][0]
    aciklama_col = [c for c in df_data.columns if "açıklama" in str(c).lower() or "description" in str(c).lower()]
    ac_col = aciklama_col[0] if aciklama_col else None
    
    invalid_rows = []
    for i, row in df_data.iterrows():
        f_val = row[fisno_col]
        f_str = str(f_val).strip() if pd.notna(f_val) else ""
        if not f_str:
            invalid_rows.append((i, row[tarih_col], row[ac_col] if ac_col else "N/A"))
            
    print(f"Index | Tarih | Aciklama (First 10 invalid)")
    for r in invalid_rows[:10]:
        print(f"{r[0]:5} | {r[1]} | {r[2]}")
        
    print(f"\nTotal invalid: {len(invalid_rows)}")

except Exception as e:
    print(f"Error: {e}")
