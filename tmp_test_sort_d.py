import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def turkish_sort_key(s):
    if not s:
        return []
    s = s.replace('İ', 'i').replace('I', 'ı').lower()
    alphabet = "abcçdefgğhıijklmnoöprsştuüvyz"
    key = []
    for char in s:
        idx = alphabet.find(char)
        if idx != -1:
            key.append(idx)
        else:
            key.append(ord(char) + 1000)
    return key

try:
    db = mysql.connector.connect( host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), database=os.getenv('DB_NAME') )
    cursor = db.cursor()
    cursor.execute("SELECT Kategori_Adi FROM Kategori WHERE Tip = 'Gider' LIMIT 1000;")
    cats = [row[0] for row in cursor.fetchall()]
    db.close()
    
    sorted_cats = sorted(cats, key=turkish_sort_key)
    for c in sorted_cats:
        if c.startswith('D'):
            print(c)
except Exception as e:
    print(f"Error: {e}")
