import pandas as pd

file_path = r"C:\Users\sg.msa\OneDrive - ÇELEBİ AVIATION\Personel\Programming\Yüklemeler\Archieve\export (3).xlsx"

try:
    df_data = pd.read_excel(file_path, skiprows=0)
    
    borc_col = [c for c in df_data.columns if "borç" in str(c).lower() or "debit" in str(c).lower()]
    alacak_col = [c for c in df_data.columns if "alacak" in str(c).lower() or "credit" in str(c).lower()]
    fisno_col = [c for c in df_data.columns if "fiş no" in str(c).lower() or "fis no" in str(c).lower()][0]
    
    b_col = borc_col[0] if borc_col else None
    a_col = alacak_col[0] if alacak_col else None
    
    invalid_with_data = []
    for i, row in df_data.iterrows():
        f_val = row[fisno_col]
        f_str = str(f_val).strip() if pd.notna(f_val) else ""
        if not f_str:
            b_val = row[b_col] if b_col else 0
            a_val = row[a_col] if a_col else 0
            # If either Borc or Alacak is non-zero
            if (pd.notna(b_val) and b_val != 0) or (pd.notna(a_val) and a_val != 0):
                invalid_with_data.append((i, row[fisno_col], b_val, a_val))
                
    print(f"Index | FisNo | Borc | Alacak (Invalid but has money)")
    for r in invalid_with_data:
        print(f"{r[0]:5} | {r[1]} | {r[2]} | {r[3]}")
        
    print(f"\nTotal invalid with money: {len(invalid_with_data)}")

except Exception as e:
    print(f"Error: {e}")
