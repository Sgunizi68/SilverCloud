
from app import create_app
from app.common.database import db
from app.models import UstKategori, Kategori, OdemeReferans, Cari, YemekCeki
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
        kats = Kategori.query.filter(Kategori.Kategori_Adi.ilike('%yemek%')).all()
        for k in kats:
            output.append(f"ID: {k.Kategori_ID} | Name: {k.Kategori_Adi} | UK_ID: {k.Ust_Kategori_ID}")

        output.append("\n--- Cari and OdemeReferans (EFatura Matching) ---")
        # Join Cari with OdemeReferans
        query = db.session.query(Cari, OdemeReferans).join(OdemeReferans, Cari.Referans_ID == OdemeReferans.Referans_ID)
        results = query.all()
        for c, r in results:
            output.append(f"Cari: {c.Alici_Unvani} | Ref_ID: {r.Referans_ID} | Ref_Metin: {r.Referans_Metin} | Kat_ID: {r.Kategori_ID}")

        output.append("\n--- YemekCeki Records (Sample) ---")
        cekler = YemekCeki.query.limit(10).all()
        for cek in cekler:
            output.append(f"ID: {cek.ID} | Kat_ID: {cek.Kategori_ID} | Tutar: {cek.Tutar} | Dates: {cek.Ilk_Tarih} to {cek.Son_Tarih}")

    with open("tmp_research_yemek_ceki_v3.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))

if __name__ == "__main__":
    research()
