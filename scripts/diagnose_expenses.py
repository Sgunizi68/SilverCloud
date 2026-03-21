from app import create_app
from app.common.database import get_db_session
from sqlalchemy import text
import json

app = create_app('development')
with app.app_context():
    session = get_db_session()
    donem = 2511
    sube_id = 1
    
    results = {}
    
    # Tables to check
    queries = {
        "e_Fatura": text("""
            SELECT uk.UstKategori_Adi, k.Kategori_Adi, SUM(e.Tutar) 
            FROM e_Fatura e 
            JOIN Kategori k ON e.Kategori_ID = k.Kategori_ID 
            JOIN UstKategori uk ON k.Ust_Kategori_ID = uk.UstKategori_ID 
            WHERE e.Sube_ID = :sube_id AND e.Donem = :donem AND (e.Giden_Fatura = 0 OR e.Giden_Fatura IS NULL) 
            GROUP BY uk.UstKategori_Adi, k.Kategori_Adi
        """),
        "Odeme": text("""
            SELECT uk.UstKategori_Adi, k.Kategori_Adi, SUM(o.Tutar) 
            FROM Odeme o 
            JOIN Kategori k ON o.Kategori_ID = k.Kategori_ID 
            JOIN UstKategori uk ON k.Ust_Kategori_ID = uk.UstKategori_ID 
            WHERE o.Sube_ID = :sube_id AND o.Donem = :donem 
            GROUP BY uk.UstKategori_Adi, k.Kategori_Adi
        """),
        "Diger_Harcama": text("""
            SELECT uk.UstKategori_Adi, k.Kategori_Adi, SUM(dh.Tutar) 
            FROM Diger_Harcama dh 
            JOIN Kategori k ON dh.Kategori_ID = k.Kategori_ID 
            JOIN UstKategori uk ON k.Ust_Kategori_ID = uk.UstKategori_ID 
            WHERE dh.Sube_ID = :sube_id AND dh.Donem = :donem 
            GROUP BY uk.UstKategori_Adi, k.Kategori_Adi
        """),
        "B2B_Ekstre": text("""
            SELECT uk.UstKategori_Adi, k.Kategori_Adi, SUM(b.Borc) 
            FROM B2B_Ekstre b 
            JOIN Kategori k ON b.Kategori_ID = k.Kategori_ID 
            JOIN UstKategori uk ON k.Ust_Kategori_ID = uk.UstKategori_ID 
            WHERE b.Sube_ID = :sube_id AND b.Donem = :donem 
            GROUP BY uk.UstKategori_Adi, k.Kategori_Adi
        """)
    }
    
    for name, query in queries.items():
        rows = session.execute(query, {"sube_id": sube_id, "donem": donem}).fetchall()
        results[name] = [{"parent": r[0], "child": r[1], "amount": float(r[2] or 0)} for r in rows]
    
    with open('expense_diagnosis_2511.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    session.close()
