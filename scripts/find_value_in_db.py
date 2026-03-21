from app import create_app
from app.common.database import get_db_session
from sqlalchemy import text

app = create_app('development')
with app.app_context():
    session = get_db_session()
    val = 45167.86
    
    tables = ["e_Fatura", "Odeme", "Diger_Harcama", "B2B_Ekstre", "Gelir", "GelirEkstra"]
    
    for table in tables:
        # We search for values close to 45167.86 due to float precision
        sql = text(f"SELECT * FROM {table} WHERE Tutar BETWEEN :v1 AND :v2 OR Borc BETWEEN :v1 AND :v2 OR Alacak BETWEEN :v1 AND :v2")
        try:
            rows = session.execute(sql, {"v1": val - 1, "v2": val + 1}).fetchall()
            if rows:
                print(f"FOUND IN {table}:")
                for r in rows:
                    print(f"  {r}")
        except Exception as e:
            # Table might not have Tutar/Borc/Alacak
            pass
            
    session.close()
