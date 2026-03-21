from app.common.database import get_db_session
from sqlalchemy import text
from flask import Flask
import os

app = Flask(__name__)
# Mock configuration to get the engine working
app.config['SQLALCHEMY_DATABASE_URL'] = 'sqlite:///c:/projects/SilverCloud/instance/database.db' # Adjust if needed
# Actually, I should just use the existing run.py or similar logic to get the context.
# But I can probably just check the database file directly if it's SQLite, or use the app context.

from run import app as flask_app

with flask_app.app_context():
    db = get_db_session()
    try:
        print("--- Mutabakat Columns ---")
        cols = db.execute(text("DESCRIBE Mutabakat")).fetchall()
        for col in cols:
            print(col)
        
        print("\n--- Mutabakat Sample Records ---")
        records = db.execute(text("SELECT * FROM Mutabakat LIMIT 10")).fetchall()
        for rec in records:
            print(rec)
            
        print("\n--- Cari Columns ---")
        cols = db.execute(text("DESCRIBE Cari")).fetchall()
        for col in cols:
            print(col)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()
