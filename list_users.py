import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def list_users():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "3306"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "SilverCloud")
        )
        cursor = conn.cursor()
        cursor.execute("SELECT Kullanici_Adi, Password FROM Kullanici")
        users = cursor.fetchall()
        print("Users in database:")
        for user in users:
            print(user)
        conn.close()
    except Exception as e:
        print(f"Error checking MySQL: {e}")

list_users()
