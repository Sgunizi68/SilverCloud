from app import create_app
from app.common.database import get_db_session
from sqlalchemy import text
from datetime import date

app = create_app('development')
with app.app_context():
    session = get_db_session()
    donem = 2511
    sube_id = 1
    
    print(f"--- e_Fatura (Gider) for Sube {sube_id} ---")
    sql = text("""
        SELECT uk.UstKategori_Adi, SUM(e.Tutar) 
        FROM e_Fatura e 
        JOIN Kategori k ON e.Kategori_ID = k.Kategori_ID 
        JOIN UstKategori uk ON k.Ust_Kategori_ID = uk.UstKategori_ID 
        WHERE e.Sube_ID = :sube_id AND e.Donem = :donem AND (e.Giden_Fatura = 0 OR e.Giden_Fatura IS NULL) 
        GROUP BY uk.UstKategori_Adi
    """)
    for row in session.execute(sql, {"sube_id": sube_id, "donem": donem}):
        print(f"  {row[0]}: {float(row[1] or 0):,.2f}")

    print(f"\n--- Odeme for Sube {sube_id} ---")
    sql = text("""
        SELECT uk.UstKategori_Adi, SUM(o.Tutar) 
        FROM Odeme o 
        JOIN Kategori k ON o.Kategori_ID = k.Kategori_ID 
        JOIN UstKategori uk ON k.Ust_Kategori_ID = uk.UstKategori_ID 
        WHERE o.Sube_ID = :sube_id AND o.Donem = :donem 
        GROUP BY uk.UstKategori_Adi
    """)
    for row in session.execute(sql, {"sube_id": sube_id, "donem": donem}):
        print(f"  {row[0]}: {float(row[1] or 0):,.2f}")
    
    session.close()
