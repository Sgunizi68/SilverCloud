
from app import create_app
from app.common.database import db
from app.models import B2BEkstre, Kategori, Gelir, EFatura
from sqlalchemy import func
import os

def research():
    app = create_app()
    output = []
    with app.app_context():
        output.append("--- EFatura Sample (Komisyon) ---")
        fats = EFatura.query.filter(EFatura.Aciklama.ilike('%Komisyon%')).limit(20).all()
        for f in fats:
            output.append(f"Date: {f.Fatura_Tarihi} | Vendor: {f.Alici_Unvani} | Total: {f.Tutar} | Desc: {f.Aciklama}")
        
        output.append("\n--- B2BEkstre with Borc > 0 (Likely Commissions) ---")
        extra_borc = B2BEkstre.query.filter(B2BEkstre.Borc > 0).limit(20).all()
        for b in extra_borc:
             output.append(f"Date: {b.Tarih} | Desc: {b.Aciklama} | Borc: {b.Borc}")

    with open("tmp_research_output_v4.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))

if __name__ == "__main__":
    research()
