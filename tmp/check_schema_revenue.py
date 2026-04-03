from app import create_app
from app.common.database import get_db_session
from sqlalchemy import text

def check_schema():
    app = create_app()
    with app.app_context():
        session = get_db_session()
        try:
            res = session.execute(text("DESCRIBE GelirEkstra")).fetchall()
            print("--- GelirEkstra columns ---")
            for r in res:
                print(r)
            
            res2 = session.execute(text("DESCRIBE Robotpos_Gelir")).fetchall()
            print("\n--- Robotpos_Gelir columns ---")
            for r in res2:
                print(r)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            session.close()

if __name__ == "__main__":
    check_schema()
