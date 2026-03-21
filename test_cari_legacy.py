import os, sys, io
sys.path.append(os.getcwd())
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app import create_app
from app.common.database import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Cumulative calculation till the given date
    report_date = '2026-03-15'
    
    # Let's aggregate for Pepsi specifically
    pepsi = "Pepsi%"
    
    f_total = db.session.execute(text("""
        SELECT SUM(E.Tutar) FROM e_Fatura E 
        WHERE E.Sube_ID = 1 AND E.Alici_Unvani LIKE :firm 
        AND E.Fatura_Tarihi <= :date AND (E.Giden_Fatura = 0 OR E.Giden_Fatura IS NULL)
    """), {"firm": pepsi, "date": report_date}).scalar() or 0
    
    o_total = db.session.execute(text("""
        SELECT SUM(O.Tutar)
        FROM Cari AS C
        INNER JOIN Odeme_Referans AS ORF ON C.Referans_ID = ORF.Referans_ID
        INNER JOIN Odeme AS O ON O.Kategori_ID = ORF.Kategori_ID
           AND O.Aciklama LIKE CONCAT('%', ORF.Referans_Metin, '%')
        WHERE O.Sube_ID = 1 AND O.Tarih <= :date AND C.Alici_Unvani LIKE :firm
    """), {"firm": pepsi, "date": report_date}).scalar() or 0
    
    print(f"\nPepsi Total Fatura: {f_total}")
    print(f"Pepsi Total Odeme:  {o_total}")
    pepsi_balance = float(f_total) - float(o_total)
    print(f"Pepsi Balance:      {pepsi_balance}")

    fasdat = "FASDAT%"
    f_total_fasdat = db.session.execute(text("""
        SELECT SUM(E.Tutar) FROM e_Fatura E 
        WHERE E.Sube_ID = 1 AND E.Alici_Unvani LIKE :firm 
        AND E.Fatura_Tarihi <= :date AND (E.Giden_Fatura = 0 OR E.Giden_Fatura IS NULL)
    """), {"firm": fasdat, "date": report_date}).scalar() or 0
    o_total_fasdat = db.session.execute(text("""
        SELECT SUM(O.Tutar) FROM Cari AS C
        INNER JOIN Odeme_Referans AS ORF ON C.Referans_ID = ORF.Referans_ID
        INNER JOIN Odeme AS O ON O.Kategori_ID = ORF.Kategori_ID
           AND O.Aciklama LIKE CONCAT('%', ORF.Referans_Metin, '%')
        WHERE O.Sube_ID = 1 AND O.Tarih <= :date AND C.Alici_Unvani LIKE :firm
    """), {"firm": fasdat, "date": report_date}).scalar() or 0
    fasdat_balance = float(f_total_fasdat) - float(o_total_fasdat)
    print(f"\nFasdat Total Fatura: {f_total_fasdat}")
    print(f"Fasdat Total Odeme:  {o_total_fasdat}")
    print(f"Fasdat Balance:      {fasdat_balance}")

    g2 = "G2MEKSPER%"
    f_total_g2 = db.session.execute(text("""
        SELECT SUM(E.Tutar) FROM e_Fatura E 
        WHERE E.Sube_ID = 1 AND E.Alici_Unvani LIKE :firm 
        AND E.Fatura_Tarihi <= :date AND (E.Giden_Fatura = 0 OR E.Giden_Fatura IS NULL)
    """), {"firm": g2, "date": report_date}).scalar() or 0
    o_total_g2 = db.session.execute(text("""
        SELECT SUM(O.Tutar) FROM Cari AS C
        INNER JOIN Odeme_Referans AS ORF ON C.Referans_ID = ORF.Referans_ID
        INNER JOIN Odeme AS O ON O.Kategori_ID = ORF.Kategori_ID
           AND O.Aciklama LIKE CONCAT('%', ORF.Referans_Metin, '%')
        WHERE O.Sube_ID = 1 AND O.Tarih <= :date AND C.Alici_Unvani LIKE :firm
    """), {"firm": g2, "date": report_date}).scalar() or 0
    g2_balance = float(f_total_g2) - float(o_total_g2)
    print(f"\nG2meksper Total Fatura: {f_total_g2}")
    print(f"G2meksper Total Odeme:  {o_total_g2}")
    print(f"G2meksper Balance:      {g2_balance}")
