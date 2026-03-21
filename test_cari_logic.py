import os, sys, io
sys.path.append(os.getcwd())
# Fix console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app import create_app
from app.common.database import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("=== Checking tables and data ===")
    
    # Check Cari table
    try:
        c = db.session.execute(text("SELECT COUNT(*) FROM Cari")).scalar()
        print(f"Cari rows: {c}")
        rows = db.session.execute(text("SELECT Cari_ID, Alici_Unvani, Cari, e_Fatura_Kategori_ID, Referans_ID FROM Cari LIMIT 5")).fetchall()
        for r in rows:
            print(f"  {r}")
    except Exception as e:
        print(f"Cari table error: {e}")

    # Check e_Fatura rows count
    try:
        c = db.session.execute(text("SELECT COUNT(*) FROM e_Fatura WHERE Sube_ID=1 AND (Giden_Fatura=0 OR Giden_Fatura IS NULL)")).scalar()
        print(f"\ne_Fatura (incoming) rows for sube 1: {c}")
    except Exception as e:
        print(f"e_Fatura error: {e}")

    # Check join - see if any matches
    try:
        rows = db.session.execute(text("""
            SELECT E.Alici_Unvani, C.Cari, C.Cari_ID, E.Tutar
            FROM e_Fatura E
            LEFT JOIN Cari C ON C.Alici_Unvani = E.Alici_Unvani AND C.e_Fatura_Kategori_ID = E.Kategori_ID
            WHERE E.Sube_ID = 1 AND (E.Giden_Fatura = 0 OR E.Giden_Fatura IS NULL)
            AND C.Cari_ID IS NOT NULL
            LIMIT 5
        """)).fetchall()
        print(f"\nJoin matches (Cari found): {len(rows)}")
        for r in rows:
            print(f"  {r}")
    except Exception as e:
        print(f"Join error: {e}")
    
    # Check join without cari filter (all efaturas)
    try:
        rows = db.session.execute(text("""
            SELECT DISTINCT E.Alici_Unvani, C.Cari, E.Kategori_ID
            FROM e_Fatura E
            LEFT JOIN Cari C ON C.Alici_Unvani = E.Alici_Unvani
            WHERE E.Sube_ID = 1 AND (E.Giden_Fatura = 0 OR E.Giden_Fatura IS NULL)
            LIMIT 10
        """)).fetchall()
        print(f"\nAll e_Fatura firms (with Cari status, no kategori join):")
        for r in rows:
            print(f"  {r}")
    except Exception as e:
        print(f"Error: {e}")

    # Check Cari column names
    try:
        rows = db.session.execute(text("DESCRIBE Cari")).fetchall()
        print(f"\nCari table columns:")
        for r in rows:
            print(f"  {r}")
    except Exception as e:
        print(f"DESCRIBE error: {e}")
