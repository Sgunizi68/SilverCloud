import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

try:
    db = mysql.connector.connect( host=os.getenv('DB_HOST'), user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), database=os.getenv('DB_NAME') )
    cursor = db.cursor()
    
    print("Checking e_Fatura for Category 48:")
    cursor.execute("SELECT Sube_ID, Donem, COUNT(*) FROM e_Fatura WHERE Kategori_ID = 48 GROUP BY Sube_ID, Donem LIMIT 5")
    for r in cursor.fetchall(): print(r)

    print("\nChecking Diger_Harcama for Category 48:")
    cursor.execute("SELECT Sube_ID, Donem, COUNT(*) FROM Diger_Harcama WHERE Kategori_ID = 48 GROUP BY Sube_ID, Donem LIMIT 5")
    for r in cursor.fetchall(): print(r)

    print("\nChecking B2B_Ekstre for Category 48:")
    cursor.execute("SELECT Sube_ID, Donem, COUNT(*) FROM B2B_Ekstre WHERE Kategori_ID = 48 GROUP BY Sube_ID, Donem LIMIT 5")
    for r in cursor.fetchall(): print(r)

    db.close()
except Exception as e:
    print(f"Error: {e}")
