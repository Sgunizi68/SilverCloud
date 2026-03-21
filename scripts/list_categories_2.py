import sys
import io
import os
sys.path.append('c:\\projects\\SilverCloud')

from app import create_app
from app.common.database import get_db_session
from app.models import Kategori, UstKategori

app = create_app()
with app.app_context():
    db = get_db_session()
    kategoriler = db.query(Kategori, UstKategori).outerjoin(
        UstKategori, Kategori.Ust_Kategori_ID == UstKategori.UstKategori_ID
    ).filter(Kategori.Aktif_Pasif == True, Kategori.Tip == 'Gelir').order_by(Kategori.Kategori_Adi).all()

    with open('scripts/categories.txt', 'w', encoding='utf-8') as f:
        f.write("--- GELİR KATEGORİSİ LİSTESİ ---\n")
        for kat, ust in kategoriler:
            ust_adi = ust.UstKategori_Adi if ust else "Yok"
            f.write(f"ID:{kat.Kategori_ID} | {kat.Kategori_Adi} | Üst:{ust_adi} | Tip:{kat.Tip}\n")
        
        f.write("\n--- GİDER vs DİĞER KATEGORİ LİSTESİ ---\n")
        diger_kategoriler = db.query(Kategori, UstKategori).outerjoin(
            UstKategori, Kategori.Ust_Kategori_ID == UstKategori.UstKategori_ID
        ).filter(Kategori.Aktif_Pasif == True, Kategori.Tip != 'Gelir').order_by(Kategori.Kategori_Adi).all()
        for kat, ust in diger_kategoriler:
            ust_adi = ust.UstKategori_Adi if ust else "Yok"
            f.write(f"ID:{kat.Kategori_ID} | {kat.Kategori_Adi} | Üst:{ust_adi} | Tip:{kat.Tip}\n")
