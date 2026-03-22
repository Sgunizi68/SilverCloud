from app.app import create_app
from app.common.database import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        result = db.session.execute(text("SELECT TOP 1 * FROM e_Fatura"))
        print(result.keys())
    except Exception as e:
        print(f"Error: {e}")
