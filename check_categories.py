from app.main import create_main_app
from app.common.database import get_db_session
from sqlalchemy import text
import sys

def check_categories():
    app = create_main_app()
    with app.app_context():
        db = get_db_session()
        print("Existing Categories:")
        res = db.execute(text("SELECT Kategori_ID, Kategori_Adi, Tip FROM Kategori")).fetchall()
        for r in res:
            try:
                print(f"ID: {r.Kategori_ID}, Name: {r.Kategori_Adi}, Type: {r.Tip}")
            except UnicodeEncodeError:
                # Handle potential console encoding issues
                print(f"ID: {r.Kategori_ID}, Name: {r.Kategori_Adi.encode('ascii', 'ignore').decode()}, Type: {r.Tip}")
        db.close()

if __name__ == "__main__":
    check_categories()
