from app import create_app
from app.common.database import db
from sqlalchemy import text

app = create_app()

def investigate_cari():
    with app.app_context():
        print("--- CARI TABLE ---")
        cari_list = db.session.execute(text("SELECT * FROM Cari LIMIT 5")).fetchall()
        for c in cari_list:
            print(c)
            
        print("\n--- B2B_EKSTRE TABLE (Unique descriptions/firms) ---")
        b2b_list = db.session.execute(text("SELECT Aciklama, SUM(Borc) - SUM(Alacak) as Balance FROM B2B_Ekstre GROUP BY Aciklama LIMIT 5")).fetchall()
        for b in b2b_list:
            print(b)
            
        print("\n--- B2B_EKSTRE with CATEGORY ---")
        b2b_cat = db.session.execute(text("""
            SELECT b.Aciklama, k.Kategori_Adi 
            FROM B2B_Ekstre b
            JOIN Kategori k ON b.Kategori_ID = k.Kategori_ID
            LIMIT 5
        """)).fetchall()
        for bc in b2b_cat:
            print(bc)

if __name__ == "__main__":
    investigate_cari()
