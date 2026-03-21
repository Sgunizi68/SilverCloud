from app import create_app
from app.common.database import get_db_session
from sqlalchemy import text
from datetime import date

app = create_app('development')
with app.app_context():
    session = get_db_session()
    # Period 2511 (Nov 2025)
    donem = 2511
    sube_id = 1 # Brandium
    
    print(f"--- EXPENSE ANALYSIS FOR SUBE {sube_id} (PERIOD {donem}) ---")
    
    tables = [
        ("e_Fatura", text("SELECT uk.UstKategori_Adi, SUM(e.Tutar) FROM e_Fatura e JOIN Kategori k ON e.Kategori_ID = k.Kategori_ID JOIN UstKategori uk ON k.Ust_Kategori_ID = uk.UstKategori_ID WHERE e.Sube_ID = :sube_id AND e.Donem = :donem AND (e.Giden_Fatura = 0 OR e.Giden_Fatura IS NULL) GROUP BY uk.UstKategori_Adi")),
        ("Diger_Harcama", text("SELECT uk.UstKategori_Adi, SUM(dh.Tutar) FROM Diger_Harcama dh JOIN Kategori k ON dh.Kategori_ID = k.Kategori_ID JOIN UstKategori uk ON k.Ust_Kategori_ID = uk.UstKategori_ID WHERE dh.Sube_ID = :sube_id AND dh.Donem = :donem GROUP BY uk.UstKategori_Adi")),
        ("B2B_Ekstre", text("SELECT uk.UstKategori_Adi, SUM(b.Borc) FROM B2B_Ekstre b JOIN Kategori k ON b.Kategori_ID = k.Kategori_ID JOIN UstKategori uk ON k.Ust_Kategori_ID = uk.UstKategori_ID WHERE b.Sube_ID = :sube_id AND b.Donem = :donem GROUP BY uk.UstKategori_Adi")),
        ("Odeme", text("SELECT uk.UstKategori_Adi, SUM(o.Tutar) FROM Odeme o JOIN Kategori k ON o.Kategori_ID = k.Kategori_ID JOIN UstKategori uk ON k.Ust_Kategori_ID = uk.UstKategori_ID WHERE o.Sube_ID = :sube_id AND o.Donem = :donem GROUP BY uk.UstKategori_Adi"))
    ]
    
    total_all = 0
    for name, sql in tables:
        print(f"\nSOURCE: {name}")
        results = session.execute(sql, {"sube_id": sube_id, "donem": donem}).fetchall()
        table_total = 0
        for row in results:
            print(f"  {row[0]}: {float(row[1] or 0):,.2f}")
            table_total += float(row[1] or 0)
        print(f"  TOTAL {name}: {table_total:,.2f}")
        total_all += table_total
    
    print(f"\nGRAND TOTAL EXPENSE: {total_all:,.2f}")
    
    # Check specific problem: "Bilgi" category
    print("\n--- DETAIL FOR 'Bilgi' CATEGORY ---")
    sql_bilgi = text("""
        SELECT k.Kategori_Adi, SUM(e.Tutar) 
        FROM e_Fatura e 
        JOIN Kategori k ON e.Kategori_ID = k.Kategori_ID 
        JOIN UstKategori uk ON k.Ust_Kategori_ID = uk.UstKategori_ID 
        WHERE e.Sube_ID = :sube_id AND e.Donem = :donem AND uk.UstKategori_Adi = 'Bilgi'
        GROUP BY k.Kategori_Adi
    """)
    res_bilgi = session.execute(sql_bilgi, {"sube_id": sube_id, "donem": donem}).fetchall()
    for row in res_bilgi:
        print(f"  {row[0]}: {float(row[1] or 0):,.2f}")

    session.close()
