from app import create_app
from app.common.database import get_db_session
from sqlalchemy import text
import pandas as pd

def check_db():
    app = create_app()
    with app.app_context():
        session = get_db_session()
        try:
            sql = text("SELECT * FROM GelirEkstra LIMIT 5")
            df = pd.read_sql(sql, session.bind)
            print("--- GelirEkstra sample ---")
            print(df)
            
            sql2 = text("SELECT * FROM Robotpos_Gelir LIMIT 5")
            df2 = pd.read_sql(sql2, session.bind)
            print("\n--- Robotpos_Gelir sample ---")
            print(df2)
        except Exception as e:
            print(f"Error in inner try: {e}")
        finally:
            session.close()

if __name__ == "__main__":
    check_db()
