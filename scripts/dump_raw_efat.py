from app import create_app
from app.common.database import get_db_session
from sqlalchemy import text

app = create_app('development')
with app.app_context():
    session = get_db_session()
    donem = 2511
    sube_id = 1
    
    sql = text("""
        SELECT uk.UstKategori_Adi, k.Kategori_Adi, e.Aciklama, e.Tutar
        FROM e_Fatura e
        JOIN Kategori k ON e.Kategori_ID = k.Kategori_ID
        JOIN UstKategori uk ON k.Ust_Kategori_ID = uk.UstKategori_ID
        WHERE e.Sube_ID = :sube_id AND e.Donem = :donem
          AND uk.UstKategori_Adi IN ('Satıştan İndirimler & Komisyonlar', 'TD Ciro/Reklam Primi & Lojistik', 'Bilgi')
    """)
    rows = session.execute(sql, {"sube_id": sube_id, "donem": donem}).fetchall()
    for r in rows:
        print(f"Parent: {r[0]} | Child: {r[1]} | Desc: {r[2]} | Amount: {float(r[3] or 0):,.2f}")
    
    session.close()
