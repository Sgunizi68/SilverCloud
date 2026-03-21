
from app import create_app
from app.common.database import db
from app.models import UstKategori, Kategori, OdemeReferans
import os

def research():
    app = create_app()
    output = []
    with app.app_context():
        output.append("--- UstKategoriler ---")
        uks = UstKategori.query.all()
        for u in uks:
            output.append(f"ID: {u.UstKategori_ID} | Name: {u.UstKategori_Adi}")
        
        output.append("\n--- Kategoriler for Yemek Çeki ---")
        # Assuming we find UK ID from above, but let's list all with 'yemek'
        kats = Kategori.query.filter(Kategori.Kategori_Adi.ilike('%yemek%')).all()
        for k in kats:
            output.append(f"ID: {k.Kategori_ID} | Name: {k.Kategori_Adi} | UK_ID: {k.Ust_Kategori_ID}")

        output.append("\n--- OdemeReferans samples ---")
        refs = OdemeReferans.query.limit(20).all()
        for r in refs:
            output.append(f"ID: {r.Referans_ID} | Code: {r.Referans_Kodu} | Title: {r.Alici_Unvani} | Kat_ID: {r.Kategori_ID}")

    with open("tmp_research_yemek_ceki_v2.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))

if __name__ == "__main__":
    research()
