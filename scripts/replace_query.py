import os

filepath = 'app/modules/reports/queries.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

prefix = content[:content.find("def get_cari_borc_takip_raporu")]

new_func = r"""def get_cari_borc_takip_raporu(start_date: str, sube_id: int):
    from sqlalchemy import text
    from app.common.database import get_db_session
    from datetime import datetime
    from decimal import Decimal
    db = get_db_session()
    try:
        report_date = start_date
        
        # 1. Fetch all firms with their status and category
        sql_firms = text('''
            SELECT Cari_ID, Alici_Unvani, e_Fatura_Kategori_ID, Referans_ID, Cari
            FROM Cari
            WHERE Aktif_Pasif = 1
        ''')
        firm_rows = db.execute(sql_firms).fetchall()
        
        # 2. Get latest mutabakat per firm
        sql_mutabakat = text('''
            SELECT M1.*
            FROM Mutabakat M1
            INNER JOIN (
                SELECT Cari_ID, MAX(Mutabakat_Tarihi) as MaxDate
                FROM Mutabakat
                WHERE Mutabakat_Tarihi <= :rd AND Sube_ID = :sube_id
                GROUP BY Cari_ID
            ) M2 ON M1.Cari_ID = M2.Cari_ID AND M1.Mutabakat_Tarihi = M2.MaxDate
            WHERE M1.Sube_ID = :sube_id
        ''')
        mutabakat_rows = db.execute(sql_mutabakat, {"rd": report_date, "sube_id": sube_id}).fetchall()
        mutabakat_map = {row.Cari_ID: row for row in mutabakat_rows}
        
        # 3. Fetch all invoices/returns up to report_date
        sql_all_fatura = text('''
            SELECT Alici_Unvani, Fatura_Tarihi, Fatura_Numarasi, Tutar, Giden_Fatura
            FROM e_Fatura
            WHERE Fatura_Tarihi <= :rd AND Sube_ID = :sube_id
            ORDER BY Fatura_Tarihi ASC
        ''')
        fatura_rows = db.execute(sql_all_fatura, {"rd": report_date, "sube_id": sube_id}).fetchall()
        
        # 4. Fetch all payments up to report_date
        sql_all_odeme = text('''
            SELECT C.Alici_Unvani, C.Referans_ID, O.Tarih, O.Aciklama, O.Tutar, ORF.Referans_Metin
            FROM Cari C
            INNER JOIN Odeme_Referans ORF ON C.Referans_ID = ORF.Referans_ID
            INNER JOIN Odeme O ON O.Kategori_ID = ORF.Kategori_ID AND O.Aciklama LIKE CONCAT('%', ORF.Referans_Metin, '%')
            WHERE O.Tarih <= :rd AND O.Sube_ID = :sube_id
            ORDER BY O.Tarih ASC
        ''')
        odeme_rows = db.execute(sql_all_odeme, {"rd": report_date, "sube_id": sube_id}).fetchall()
        
        # Group data by firm
        fatura_by_firm = {}
        for r in fatura_rows:
            unvan = r.Alici_Unvani or "Bilinmeyen"
            if unvan not in fatura_by_firm: fatura_by_firm[unvan] = []
            fatura_by_firm[unvan].append(r)
            
        odeme_by_firm = {}
        for r in odeme_rows:
            unvan = r.Alici_Unvani or "Bilinmeyen"
            if unvan not in odeme_by_firm: odeme_by_firm[unvan] = []
            odeme_by_firm[unvan].append(r)
            
        processed_list = []
        
        for firm in firm_rows:
            unvan = firm.Alici_Unvani
            mut = mutabakat_map.get(firm.Cari_ID)
            
            mut_tutar = float(mut.Tutar) if mut else 0.0
            mut_date = mut.Mutabakat_Tarihi if mut else datetime.strptime('1900-01-01', '%Y-%m-%d').date()
            
            f_list = fatura_by_firm.get(unvan, [])
            o_list = odeme_by_firm.get(unvan, [])
            
            # Filter since mutabakat
            current_faturalar = [f for f in f_list if f.Fatura_Tarihi > mut_date]
            current_odemeler = [o for o in o_list if o.Tarih > mut_date]
            
            fatura_toplam = sum(float(f.Tutar) for f in current_faturalar if not f.Giden_Fatura)
            iade_toplam = sum(float(f.Tutar) for f in current_faturalar if f.Giden_Fatura == 1)
            odeme_toplam = sum(float(o.Tutar) for o in current_odemeler)
            
            balance = mut_tutar + fatura_toplam - iade_toplam - odeme_toplam
            
            # Skip if everything is zero and no recent activity
            if balance == 0 and not current_faturalar and not current_odemeler and mut_tutar == 0:
                continue
            
            # Details for UI
            details = []
            if mut:
                details.append({
                    "date": mut.Mutabakat_Tarihi.strftime('%d.%m.%Y'),
                    "description": "Mutabakat Kaydı",
                    "amount": mut_tutar,
                    "type": "mutabakat"
                })
            
            for f in current_faturalar:
                details.append({
                    "date": f.Fatura_Tarihi.strftime('%d.%m.%Y'),
                    "description": f"Fatura: {f.Fatura_Numarasi}",
                    "amount": float(f.Tutar) * (-1 if f.Giden_Fatura == 1 else 1),
                    "type": "invoice" if not f.Giden_Fatura else "return"
                })
                
            for o in current_odemeler:
                details.append({
                    "date": o.Tarih.strftime('%d.%m.%Y'),
                    "description": f"Ödeme: {o.Aciklama}",
                    "amount": -float(o.Tutar),
                    "type": "payment"
                })
            
            # Sort details by date desc
            details.sort(key=lambda x: datetime.strptime(x["date"], '%d.%m.%Y'), reverse=True)
            
            status = "Cari Borç" if firm.Cari == 1 else ("Cari Olmayan Borç" if firm.Cari == 0 else "Belirsiz")
            
            processed_list.append({
                "name": unvan,
                "status": status,
                "balance": balance,
                "mutabakat_tutar": mut_tutar,
                "fatura_toplam": fatura_toplam,
                "iade_toplam": iade_toplam,
                "odeme_toplam": odeme_toplam,
                "details": details[:30] # Limit display
            })
            
        # Categorize results
        cari_borclar = [x for x in processed_list if x["status"] == "Cari Borç"]
        cari_olmayan = [x for x in processed_list if x["status"] == "Cari Olmayan Borç"]
        belirsiz = [x for x in processed_list if x["status"] == "Belirsiz"]
        
        # Sort each
        cari_borclar.sort(key=lambda x: x["balance"], reverse=True)
        cari_olmayan.sort(key=lambda x: x["balance"], reverse=True)
        belirsiz.sort(key=lambda x: abs(x["balance"]), reverse=True)
        
        summary = {
            "tumu_count": len(processed_list),
            "tumu_bakiye": sum(x["balance"] for x in processed_list),
            "cari_count": len(cari_borclar),
            "cari_bakiye": sum(x["balance"] for x in cari_borclar),
            "cari_olmayan_count": len(cari_olmayan),
            "cari_olmayan_bakiye": sum(x["balance"] for x in cari_olmayan),
            "belirsiz_count": len(belirsiz),
            "belirsiz_bakiye": sum(x["balance"] for x in belirsiz)
        }
        
        return {
            "summary": summary,
            "lists": {
                "cari_borclar": cari_borclar,
                "cari_olmayan": cari_olmayan,
                "belirsiz": belirsiz,
                "tumu": cari_borclar + cari_olmayan + belirsiz
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "summary": { "tumu_count": 0, "tumu_bakiye": 0.0, "cari_count": 0, "cari_bakiye": 0.0, "cari_olmayan_count": 0, "cari_olmayan_bakiye": 0.0, "belirsiz_count": 0, "belirsiz_bakiye": 0.0 },
            "lists": { "cari_borclar": [], "cari_olmayan": [], "belirsiz": [], "tumu": [] }
        }
    finally:
        db.close()
"""

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(prefix + new_func)
