from app import create_app
from app.common.database import get_db_session
from sqlalchemy import text
from datetime import date

app = create_app('development')
with app.app_context():
    session = get_db_session()
    # Period 2511 (Nov 2025)
    start_date = date(2025, 11, 1)
    end_date = date(2025, 11, 30)
    sube_id = 1 # Assuming Brandium is 1, will verify if needed
    
    # Check Revenues
    sql = text("""
        SELECT uk.UstKategori_Adi, k.Kategori_Adi, SUM(g.Tutar) as total
        FROM Gelir g
        JOIN Kategori k ON g.Kategori_ID = k.Kategori_ID
        JOIN UstKategori uk ON k.Ust_Kategori_ID = uk.UstKategori_ID
        WHERE g.Sube_ID = :sube_id 
          AND g.Tarih >= :start_date AND g.Tarih <= :end_date
        GROUP BY uk.UstKategori_Adi, k.Kategori_Adi
        ORDER BY uk.UstKategori_Adi, total DESC
    """)
    
    results = session.execute(sql, {"start_date": start_date, "end_date": end_date, "sube_id": sube_id}).fetchall()
    
    print(f"Revenue Results for Sube {sube_id} (2511):")
    total_rev = 0
    for row in results:
        print(f"{row[0]} -> {row[1]}: {row[2]:,.2f}")
        total_rev += float(row[2])
    
    print(f"TOTAL REVENUE (calculated from categories): {total_rev:,.2f}")
    
    # Check RobotPOS
    sql_robotpos = text("""
        SELECT SUM(RobotPos_Tutar) 
        FROM GelirEkstra 
        WHERE Sube_ID = :sube_id 
          AND Tarih >= :start_date AND Tarih <= :end_date
    """)
    robotpos_row = session.execute(sql_robotpos, {"start_date": start_date, "end_date": end_date, "sube_id": sube_id}).fetchone()
    print(f"RobotPOS Total: {float(robotpos_row[0] or 0):,.2f}")
    
    session.close()
