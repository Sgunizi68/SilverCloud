import mysql.connector
import os
from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "3306"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "SilverCloud")
)
cursor = conn.conn.cursor() if hasattr(conn, 'conn') else conn.cursor()
cursor.execute("SELECT Kullanici_Adi, Password FROM Kullanici")
users = cursor.fetchall()
conn.close()

print("Users from database:")
for user in users:
    print(user)

# Common passwords to test
common_pws = [
    "Adm123!", "Admin123!", "admin", "Admin", "123456", "12345678", "password", "pass", "F5tk3515"
]

print("\nVerifying passwords:")
for u, h in users:
    print(f"\nUser: {u}")
    for pw in common_pws:
        try:
            if pwd_context.verify(pw, h):
                print(f"  MATCH FOUND: '{pw}'")
                break
        except Exception as e:
            print(f"  Error checking '{pw}': {e}")
    else:
        print("  No common password matched.")
