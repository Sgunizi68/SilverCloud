import pandas as pd
import json

file_path = r"C:\Users\sg.msa\OneDrive - ÇELEBİ AVIATION\Personel\Programming\Yüklemeler\Archieve\export (3).xlsx"

try:
    df = pd.read_excel(file_path, header=None)
    print(f"Total rows in Excel: {len(df)}")
    
    # Print first few rows to find header
    print("\nFirst 10 rows:")
    for i, row in df.head(10).iterrows():
        print(f"Row {i}: {list(row)}")
        
    # Search for header row
    header_row_idx = -1
    for i, row in df.iterrows():
        row_str = " ".join([str(x).lower() for x in row if pd.notna(x)])
        if "tarih" in row_str and ("fiş no" in row_str or "fis no" in row_str):
            header_row_idx = i
            print(f"\nPotential header found at row {i}")
            break
            
    if header_row_idx != -1:
        # Re-read with proper header
        df_data = pd.read_excel(file_path, skiprows=header_row_idx)
        print(f"\nData rows (excluding header): {len(df_data)}")
        
        # Check for empty Date or Fis No
        # We need to normalize columns to find Tarih and Fis No
        tarih_col = [c for c in df_data.columns if "tarih" in str(c).lower() or "date" in str(c).lower()]
        fisno_col = [c for c in df_data.columns if "fiş no" in str(c).lower() or "fis no" in str(c).lower()]
        
        if tarih_col and fisno_col:
            t_col = tarih_col[0]
            f_col = fisno_col[0]
            valid_rows = df_data.dropna(subset=[t_col, f_col])
            print(f"Rows with both Tarih and Fiş No: {len(valid_rows)}")
            
            # Show some rows that were skipped
            skipped_rows = df_data[df_data[t_col].isna() | df_data[f_col].isna()]
            if not skipped_rows.empty:
                print(f"\nSkipped {len(skipped_rows)} rows due to missing Tarih or Fiş No.")
                print("First 5 skipped rows data:")
                print(skipped_rows.head(5))
        else:
            print(f"\nCould not identify Tarih ({tarih_col}) or Fiş No ({fisno_col}) columns correctly.")
            print(f"Available columns: {list(df_data.columns)}")

except Exception as e:
    print(f"Error reading file: {e}")
