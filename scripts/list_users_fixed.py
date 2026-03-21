import sqlite3
import os

db_path = 'app.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()
try:
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in c.fetchall()]
    print(f"Tables: {tables}")
    
    if 'Kullanici' in tables:
        c.execute('SELECT Kullanici_Adi, Password FROM Kullanici')
        users = c.fetchall()
        for user in users:
            print(f"User: {user[0]}, Pass: {user[1]}")
    else:
        print("Kullanici table not found")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
