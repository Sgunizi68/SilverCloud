from app.main import create_main_app
from app.common.database import get_db_session
from sqlalchemy import text

app = create_main_app()
with app.app_context():
    db = get_db_session()
    print("Database Engine:", db.get_bind().url)
    
    # Let's test the CONCAT query
    sql = """
    SELECT s.Fatura_Numarasi AS Ana, t.Fatura_Numarasi AS Child, t.Tutar 
    FROM e_Fatura s
    INNER JOIN Kategori k ON s.Kategori_ID = k.Kategori_ID AND k.Kategori_ID = 88
    LEFT JOIN e_Fatura t ON t.Fatura_Numarasi LIKE CONCAT(s.Fatura_Numarasi, '-%') AND t.Fatura_Numarasi != s.Fatura_Numarasi
    WHERE s.Fatura_Numarasi LIKE 'T022026000011717%'
    """
    try:
        rows = db.execute(text(sql)).fetchall()
        for r in rows:
            print(dict(r._mapping))
    except Exception as e:
        print("Error:", e)
        
    db.close()
