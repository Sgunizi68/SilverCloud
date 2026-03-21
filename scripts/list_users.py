import sqlite3
import os

db_path = 'silvercloud.db'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
c = conn.cursor()
try:
    c.execute('SELECT Kullanici_Adi, Password FROM Kullanici')
    users = c.fetchall()
    for user in users:
        print(f"Username: {user[0]}, Hashed Password: {user[1]}")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
