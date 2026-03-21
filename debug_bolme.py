"""Deep dive into what the query actually returns for our Bolunmus Fatura."""
from app.main import create_main_app
from app.common.database import get_db_session
from sqlalchemy import text

def main():
    app = create_main_app()
    with app.app_context():
        db = get_db_session()

        # Full query result 
        print("=== Full bolunmus-faturalar query result ===")
        rows = db.execute(text("""
        SELECT
            s.Fatura_Numarasi  AS Ana_Fatura,
            s.Tutar            AS Ana_Tutar,
            s.Alici_Unvani     AS Ana_Alici_Unvani,
            t.Fatura_ID,
            t.Fatura_Numarasi,
            t.Tutar
        FROM e_Fatura t
        INNER JOIN e_Fatura s
            ON t.Fatura_Numarasi LIKE (s.Fatura_Numarasi || '-%')
            AND t.Fatura_Numarasi != s.Fatura_Numarasi
        INNER JOIN Kategori k
            ON s.Kategori_ID = k.Kategori_ID
        WHERE k.Kategori_ID = 88
        ORDER BY s.Fatura_Numarasi, t.Fatura_Numarasi
        LIMIT 30
        """)).fetchall()
        print(f"Total rows: {len(rows)}")
        for r in rows:
            m = r._mapping
            print(f"  Ana:{m['Ana_Fatura']}  Child:{m['Fatura_Numarasi']}  ChildTutar:{m['Tutar']}")

        print()
        print("=== Total invoices with KatID=88 ===")
        cnt = db.execute(text("SELECT COUNT(*) FROM e_Fatura WHERE Kategori_ID=88")).scalar()
        print(f"Count: {cnt}")

        print()
        print("=== Does T022026000011717 have any potential children? ===")
        rows2 = db.execute(text(
            "SELECT Fatura_ID, Fatura_Numarasi, Kategori_ID, Tutar FROM e_Fatura "
            "WHERE Fatura_Numarasi LIKE 'T022026000011717-%'"
        )).fetchall()
        if not rows2:
            print("  NO CHILDREN FOUND in database")
        else:
            for r in rows2:
                m = r._mapping
                print(f"  {m['Fatura_Numarasi']} KatID:{m['Kategori_ID']} Tutar:{m['Tutar']}")

        print()
        print("=== The UI shows T022026000011717 as a child - why? ===")
        # Could T022026000011717 be a child of a shorter parent?
        rows3 = db.execute(text("""
            SELECT s.Fatura_Numarasi AS Possible_Parent, s.Kategori_ID
            FROM e_Fatura s
            WHERE 'T022026000011717' LIKE (s.Fatura_Numarasi || '-%')
            AND s.Kategori_ID = 88
        """)).fetchall()
        if not rows3:
            print("  No parent found - T022026000011717 cannot be a child")
        else:
            for r in rows3:
                m = r._mapping
                print(f"  Possible parent: {m['Possible_Parent']}")

        db.close()

if __name__ == "__main__":
    main()
