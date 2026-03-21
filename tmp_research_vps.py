
from app import create_app
from app.common.database import db
from app.models import PuantajSecimi, GelirEkstra
import os

def research():
    app = create_app()
    output = []
    with app.app_context():
        output.append("--- PuantajSecimi ---")
        secs = PuantajSecimi.query.all()
        for s in secs:
            output.append(f"ID: {s.Secim_ID} | Name: {s.Secim} | Value: {s.Degeri} | Color: {s.Renk_Kodu}")
        
        output.append("\n--- GelirEkstra Sample ---")
        extras = GelirEkstra.query.limit(5).all()
        for e in extras:
            output.append(f"ID: {e.GelirEkstra_ID} | Date: {e.Tarih} | Tabak: {e.Tabak_Sayisi} | Sube: {e.Sube_ID}")

    with open("tmp_research_vps.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))

if __name__ == "__main__":
    research()
