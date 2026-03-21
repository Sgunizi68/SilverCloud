import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "SilverCloud")
    )
    c = conn.cursor()
    c.execute('SELECT Kullanici_Adi, Password FROM Kullanici')
    users = c.fetchall()
    for user in users:
        print(f"User: {user[0]}, Pass: {user[1]}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
