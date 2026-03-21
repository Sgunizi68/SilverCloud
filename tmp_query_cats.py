import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

try:
    db = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    cursor = db.cursor()
    cursor.execute("SELECT Kategori_ID, Kategori_Adi FROM Kategori WHERE Kategori_Adi LIKE '%Plan%'")
    rows = cursor.fetchall()
    for row in rows:
        print(f"ID: {row[0]}, Name: {row[1]}")
    db.close()
except Exception as e:
    print(f"Error: {e}")
