import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.common.database import SessionLocal
from app.models import Kategori, UstKategori

app = create_app()

def run_tests():
    with app.app_context():
        db = SessionLocal()
        print("--- Gelir Kategorileri ---")
        cats = db.query(Kategori).join(UstKategori).filter(UstKategori.UstKategori_Adi.in_(['Gelir', 'Gelir Kalemi', 'Satış', 'Ödeme'])).all()
        for c in cats:
            print(f"ID: {c.Kategori_ID}, Ad: {c.Kategori_Adi}, Ust: {c.ust_kategori.UstKategori_Adi}")
            
        print("TUM Kategoriler:")
        all_cats = db.query(Kategori).all()
        for c in all_cats:
            ust = c.ust_kategori.UstKategori_Adi if c.ust_kategori else 'None'
            print(f"ID: {c.Kategori_ID}, Ad: {c.Kategori_Adi}, Ust: {ust}")
        db.close()

if __name__ == "__main__":
    run_tests()
