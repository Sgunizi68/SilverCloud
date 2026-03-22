import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

try:
    db = mysql.connector.connect( host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), database=os.getenv('DB_NAME') )
    cursor = db.cursor()
    cursor.execute("SHOW VARIABLES LIKE 'collation_database';")
    print(cursor.fetchone())
    db.close()
except Exception as e:
    print(f"Error: {e}")
