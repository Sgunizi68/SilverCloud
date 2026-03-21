
from app import create_app
from app.common.database import db
from app.models import Kategori, EFatura, Odeme, Gelir
from sqlalchemy import func

def research():
    app = create_app()
    output = []
    with app.app_context():
        # 1. Categories for Yemek Çeki
        output.append("--- Meal Voucher Categories ---")
        kats = Kategori.query.filter(
            (Kategori.Kategori_Adi.ilike('%Multinet%')) |
            (Kategori.Kategori_Adi.ilike('%Ticket%')) |
            (Kategori.Kategori_Adi.ilike('%Sodexo%')) |
            (Kategori.Kategori_Adi.ilike('%Metropol%')) |
            (Kategori.Kategori_Adi.ilike('%Setcard%')) |
            (Kategori.Kategori_Adi.ilike('%Winwin%'))
        ).all()
        for k in kats:
            output.append(f"ID: {k.Kategori_ID} | Name: {k.Kategori_Adi} | Tip: {k.Tip}")

        # 2. EFatura samples for these platforms
        output.append("\n--- EFatura Samples ---")
        keywords = ['Multinet', 'Ticket', 'Sodexo', 'Metropol', 'Setcard', 'Winwin', 'Edenred']
        for kw in keywords:
            fats = EFatura.query.filter(EFatura.Aciklama.ilike(f'%{kw}%')).limit(3).all()
            for f in fats:
                output.append(f"KW: {kw} | Date: {f.Fatura_Tarihi} | Desc: {f.Aciklama} | Tutar: {f.Tutar}")

        # 3. Odeme types/descriptions
        output.append("\n--- Odeme Samples ---")
        for kw in keywords:
            odemes = Odeme.query.filter(Odeme.Aciklama.ilike(f'%{kw}%')).limit(3).all()
            for o in odemes:
                 output.append(f"KW: {kw} | Date: {o.Tarih} | Desc: {o.Aciklama} | Tutar: {o.Tutar}")

    with open("tmp_research_yemek_ceki.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))

if __name__ == "__main__":
    research()
