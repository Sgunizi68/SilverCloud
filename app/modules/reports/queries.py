from typing import Dict
from sqlalchemy import select, func, text
from app.common.database import get_db_session
from app.models import EFatura, Odeme, Nakit, Stok, StokFiyat, Calisan
from datetime import datetime, date, timedelta
from decimal import Decimal
import calendar


def invoicing_summary(start_date=None, end_date=None) -> Dict:
    session = get_db_session()
    try:
        stmt = select(func.coalesce(func.sum(EFatura.tutar), 0).label('total_invoices'))
        if start_date:
            stmt = stmt.where(EFatura.created_at >= start_date)
        if end_date:
            stmt = stmt.where(EFatura.created_at <= end_date)
        total = session.execute(stmt).scalar_one()

        payments_stmt = select(func.coalesce(func.sum(Odeme.tutar), 0).label('total_payments'))
        if start_date:
            payments_stmt = payments_stmt.where(Odeme.created_at >= start_date)
        if end_date:
            payments_stmt = payments_stmt.where(Odeme.created_at <= end_date)
        total_payments = session.execute(payments_stmt).scalar_one()

        cash_stmt = select(func.coalesce(func.sum(Nakit.tutar), 0).label('total_cash'))
        if start_date:
            cash_stmt = cash_stmt.where(Nakit.created_at >= start_date)
        if end_date:
            cash_stmt = cash_stmt.where(Nakit.created_at <= end_date)
        total_cash = session.execute(cash_stmt).scalar_one()

        return {
            'total_invoices': float(total),
            'total_payments': float(total_payments),
            'total_cash': float(total_cash),
        }
    finally:
        session.close()


def inventory_valuation() -> Dict:
    session = get_db_session()
    try:
        # Sum of (quantity * latest_price) across stocks
        # Join Stok and latest StokFiyat per stok
        subq = select(StokFiyat.stok_id, func.max(StokFiyat.id).label('max_id')).group_by(StokFiyat.stok_id).subquery()
        latest = select(StokFiyat).join(subq, StokFiyat.id == subq.c.max_id).subquery()
        stmt = select(func.coalesce(func.sum(Stok.miktar * latest.c.fiyat), 0))
        total = session.execute(stmt).scalar_one()
        return {'inventory_valuation': float(total)}
    finally:
        session.close()


def hr_summary() -> Dict:
    session = get_db_session()
    try:
        stmt = select(func.count(Calisan.id))
        count = session.execute(stmt).scalar_one()
        return {'employee_count': int(count)}
    finally:
        session.close()


def _donem_to_dates(donem: int):
    s = str(donem)
    if len(s) == 4:
        yy = int(s[:2])
        mm = int(s[2:4])
        year = 2000 + yy
    elif len(s) == 6:
        year = int(s[:4])
        mm = int(s[4:6])
    else:
        raise ValueError('invalid donem')
    start = date(year, mm, 1)
    # compute end as last day of month
    if mm == 12:
        end = date(year, 12, 31)
    else:
        end = date(year, mm + 1, 1) - timedelta(days=1)
    return start, end


def dashboard_report(donem: int, sube_id: int, show_gizli: bool = True) -> Dict:
    session = get_db_session()
    try:
        try:
            start_date, end_date = _donem_to_dates(donem)
        except Exception:
            today = date.today()
            start_date = date(today.year, today.month, 1)
            end_date = date(today.year, today.month, 28)

        # 1. COLUMN: GELİRLER (Revenue from Gelir table with hierarchical details)
        # ---------------------------------------------------------------------
        # show_gizli=False → filter out categories where Kategori.Gizli = 1
        gizli_filter_gelir = "" if show_gizli else "AND k.Gizli = 0"
        gizli_filter_gider = "" if show_gizli else "AND k.Gizli = 0"

        sql_revenues = text(f"""
            SELECT 
                uk.UstKategori_Adi as parent_label, 
                k.Kategori_Adi as child_label, 
                SUM(g.Tutar) as total
            FROM Gelir g
            JOIN Kategori k ON g.Kategori_ID = k.Kategori_ID
            JOIN UstKategori uk ON k.Ust_Kategori_ID = uk.UstKategori_ID
            WHERE g.Sube_ID = :sube_id 
              AND g.Tarih >= :start_date AND g.Tarih <= :end_date
              {gizli_filter_gelir}
            GROUP BY uk.UstKategori_Adi, k.Kategori_Adi
            ORDER BY uk.UstKategori_Adi, total DESC
        """)
        
        sql_robotpos = text("""
            SELECT SUM(RobotPos_Tutar) 
            FROM GelirEkstra 
            WHERE Sube_ID = :sube_id 
              AND Tarih >= :start_date AND Tarih <= :end_date
        """)

        try:
            rev_rows = session.execute(sql_revenues, {"start_date": start_date, "end_date": end_date, "sube_id": sube_id}).fetchall()
            
            # Group into hierarchy
            gelir_groups = {}
            for row in rev_rows:
                parent = row[0] or 'Diğer'
                child = row[1]
                amount = float(row[2] or 0)
                
                if parent not in gelir_groups:
                    gelir_groups[parent] = {"label": parent, "amount": 0, "children": []}
                
                gelir_groups[parent]["amount"] += amount
                gelir_groups[parent]["children"].append({"label": child, "amount": amount})
            
            gelirler = list(gelir_groups.values())
            
            robotpos_row = session.execute(sql_robotpos, {"start_date": start_date, "end_date": end_date, "sube_id": sube_id}).fetchone()
            robotpos_total = float(robotpos_row[0] or 0)
            # RobotPOS is kept separate, NOT added to 'gelirler' to avoid double counting in TOTAL REVENUE
        except Exception:
            gelirler = []
            robotpos_total = 0.0

        total_revenue = sum(i['amount'] for i in gelirler)

        # 2. COLUMN: GİDERLER (Aggregate all monthly costs hierarchically)
        # ---------------------------------------------------------------------
        # e_Fatura (Expenses)
        sql_efat_gider = text(f"""
            SELECT uk.UstKategori_Adi, k.Kategori_Adi, SUM(e.Tutar)
            FROM e_Fatura e
            JOIN Kategori k ON e.Kategori_ID = k.Kategori_ID
            JOIN UstKategori uk ON k.Ust_Kategori_ID = uk.UstKategori_ID
            WHERE e.Sube_ID = :sube_id AND e.Donem = :donem AND (e.Giden_Fatura = 0 OR e.Giden_Fatura IS NULL)
              {gizli_filter_gider}
            GROUP BY uk.UstKategori_Adi, k.Kategori_Adi
        """)
        
        # Diger Harcama
        sql_diger_gider = text(f"""
            SELECT uk.UstKategori_Adi, k.Kategori_Adi, SUM(dh.Tutar)
            FROM Diger_Harcama dh
            JOIN Kategori k ON dh.Kategori_ID = k.Kategori_ID
            JOIN UstKategori uk ON k.Ust_Kategori_ID = uk.UstKategori_ID
            WHERE dh.Sube_ID = :sube_id AND dh.Donem = :donem
              {gizli_filter_gider}
            GROUP BY uk.UstKategori_Adi, k.Kategori_Adi
        """)

        # B2B Ekstre (Borç)
        sql_b2b_gider = text(f"""
            SELECT uk.UstKategori_Adi, k.Kategori_Adi, SUM(b.Borc)
            FROM B2B_Ekstre b
            JOIN Kategori k ON b.Kategori_ID = k.Kategori_ID
            JOIN UstKategori uk ON k.Ust_Kategori_ID = uk.UstKategori_ID
            WHERE b.Sube_ID = :sube_id AND b.Donem = :donem
              {gizli_filter_gider}
            GROUP BY uk.UstKategori_Adi, k.Kategori_Adi
        """)

        # Odeme
        sql_odeme_gider = text("""
            SELECT uk.UstKategori_Adi, k.Kategori_Adi, SUM(o.Tutar)
            FROM Odeme o
            JOIN Kategori k ON o.Kategori_ID = k.Kategori_ID
            JOIN UstKategori uk ON k.Ust_Kategori_ID = uk.UstKategori_ID
            WHERE o.Sube_ID = :sube_id AND o.Donem = :donem
            GROUP BY uk.UstKategori_Adi, k.Kategori_Adi
        """)

        gider_groups = {}
        def add_to_gider_hier(rows):
            for r in rows:
                parent = r[0] or 'Diğer Gider'
                child = r[1]
                val = float(r[2] or 0)
                
                
                if parent not in gider_groups:
                    gider_groups[parent] = {"label": parent, "amount": 0, "children": []}
                
                gider_groups[parent]["amount"] += val
                # Find if child already exists in children
                existing_child = next((c for c in gider_groups[parent]["children"] if c["label"] == child), None)
                if existing_child:
                    existing_child["amount"] += val
                else:
                    gider_groups[parent]["children"].append({"label": child, "amount": val})

        try:
            add_to_gider_hier(session.execute(sql_efat_gider, {"donem": donem, "sube_id": sube_id}).fetchall())
            add_to_gider_hier(session.execute(sql_diger_gider, {"donem": donem, "sube_id": sube_id}).fetchall())
            add_to_gider_hier(session.execute(sql_b2b_gider, {"donem": donem, "sube_id": sube_id}).fetchall())
            # sql_odeme_gider is excluded as per the correction plan (bank transfers/CC payments, not P&L expenses)
        except Exception:
            pass

        # Filter out summary headers and handle specific mappings
        # 1. 'Bilgi' is a summary of TD prims/logistics already included
        if 'Bilgi' in gider_groups:
            del gider_groups['Bilgi']
            
        # 2. 'Ödeme Sistemleri' usually comes from Odeme table, if it somehow slipped from others, filter it
        if 'Ödeme Sistemleri' in gider_groups:
             del gider_groups['Ödeme Sistemleri']

        # Sort children by amount
        for g in gider_groups.values():
            g["children"].sort(key=lambda x: x["amount"], reverse=True)

        giderler = list(gider_groups.values())
        total_expense = sum(i['amount'] for i in giderler)

        # 3. COLUMN: FINANSAL ÖZET & STOK
        # ---------------------------------------------------------------------
        # Stock valuation helper
        sql_stock_val = text("""
            SELECT SUM(s.Miktar * COALESCE(sf.Fiyat,0)) FROM Stok_Sayim s
            LEFT JOIN (
                SELECT st.* FROM Stok_Fiyat st
                INNER JOIN (
                    SELECT Malzeme_Kodu, MAX(Gecerlilik_Baslangic_Tarih) as max_date
                    FROM Stok_Fiyat
                    GROUP BY Malzeme_Kodu
                ) ms ON st.Malzeme_Kodu = ms.Malzeme_Kodu AND st.Gecerlilik_Baslangic_Tarih = ms.max_date
            ) sf ON sf.Malzeme_Kodu = s.Malzeme_Kodu
            WHERE s.Sube_ID = :sube_id AND s.Donem = :donem
        """)
        
        try:
            stok_row = session.execute(sql_stock_val, {"sube_id": sube_id, "donem": donem}).fetchone()
            stok_degeri = float(stok_row[0] or 0)
        except Exception:
            stok_degeri = 0.0

        # Prev month stock
        prev_month = start_date.month - 1
        prev_year = start_date.year
        if prev_month == 0:
            prev_month = 12
            prev_year -= 1
        prev_donem = int(str(prev_year)[2:] + str(prev_month).zfill(2))
        
        try:
            prev_stock_row = session.execute(sql_stock_val, {"sube_id": sube_id, "donem": prev_donem}).fetchone()
            prev_stok_degeri = float(prev_stock_row[0] or 0)
        except Exception:
            prev_stok_degeri = 0.0

        stok_fark = stok_degeri - prev_stok_degeri
        cirodan_kalan = total_revenue - total_expense
        donem_kar_zarar = cirodan_kalan + stok_fark

        financial = {
            'total_revenue': total_revenue,
            'total_expense': total_expense,
            'cirodan_kalan': cirodan_kalan,
            'stok_farki': stok_fark,
            'donem_kar_zarar': donem_kar_zarar,
            'current_stock': stok_degeri,
            'prev_stock': prev_stok_degeri
        }

        # Giden Fatura – only visible to users with Gizli Kategori permission (or Admin)
        giden_faturalar = []
        giden_total = 0.0
        if show_gizli:
            sql_giden = text("""
                SELECT e.Alici_Unvani as label, SUM(e.Tutar) as total
                FROM e_Fatura e
                WHERE e.Donem = :donem AND e.Sube_ID = :sube_id AND e.Giden_Fatura = 1
                GROUP BY e.Alici_Unvani
            """)
            try:
                g_rows = session.execute(sql_giden, {"donem": donem, "sube_id": sube_id}).fetchall()
                giden_faturalar = [{"label": r[0] or 'Diğer', "amount": float(r[1] or 0)} for r in g_rows]
                giden_total = sum(i['amount'] for i in giden_faturalar)
            except Exception:
                pass

        # Plandışı Giderler (Category 48) - Detailed items
        unplanned_expenses = []
        unplanned_total = 0.0
        try:
            # 1. e_Fatura (Plan Dışı Giderler)
            sql_efat_unp = text("""
                SELECT Alici_Unvani, COALESCE(Aciklama, Fatura_Numarasi) as detail, Tutar
                FROM e_Fatura
                WHERE Sube_ID = :sube_id AND Donem = :donem AND Kategori_ID = 48 
                  AND (Giden_Fatura = 0 OR Giden_Fatura IS NULL)
            """)
            efat_unp_rows = session.execute(sql_efat_unp, {"sube_id": sube_id, "donem": donem}).fetchall()
            for r in efat_unp_rows:
                unplanned_expenses.append({
                    "label": f"{r[0] or ''} - {r[1] or ''}".strip(" -"),
                    "amount": float(r[2] or 0)
                })

            # 2. Diger Harcama (Plan Dışı Giderler)
            sql_diger_unp = text("""
                SELECT Alici_Adi, COALESCE(Açıklama, '') as detail, Tutar
                FROM Diger_Harcama
                WHERE Sube_ID = :sube_id AND Donem = :donem AND Kategori_ID = 48
            """)
            d_unp_rows = session.execute(sql_diger_unp, {"sube_id": sube_id, "donem": donem}).fetchall()
            for r in d_unp_rows:
                unplanned_expenses.append({
                    "label": f"{r[0] or ''} - {r[1] or ''}".strip(" -"),
                    "amount": float(r[2] or 0)
                })

            # 3. B2B Ekstre (Plan Dışı Giderler - Borç)
            sql_b2b_unp = text("""
                SELECT Fis_No, COALESCE(Aciklama, COALESCE(Fis_Turu, Fatura_Metni)) as detail, Borc
                FROM B2B_Ekstre
                WHERE Sube_ID = :sube_id AND Donem = :donem AND Kategori_ID = 48
            """)
            b_unp_rows = session.execute(sql_b2b_unp, {"sube_id": sube_id, "donem": donem}).fetchall()
            for r in b_unp_rows:
                unplanned_expenses.append({
                    "label": f"{r[0] or ''} - {r[1] or ''}".strip(" -"),
                    "amount": float(r[2] or 0)
                })
            
            unplanned_total = sum(i['amount'] for i in unplanned_expenses)
        except Exception:
            pass

        return {
            'gelirler': sorted(gelirler, key=lambda x: x['amount'], reverse=True),
            'giderler': sorted(giderler, key=lambda x: x['amount'], reverse=True),
            'financial_summary': financial,
            'giden_fatura': {'items': giden_faturalar, 'total': giden_total},
            'unplanned_expenses': {'items': unplanned_expenses, 'total': unplanned_total},
            'robotpos_total': robotpos_total
        }
    finally:
        session.close()


def get_bayi_karlilik_raporu(sube_id: int, year: int) -> Dict:
    """
    Calculates the Bayi Karlılık Raporu for a given branch and year.
    Matches legacy GümüşBulut logic 1:1.
    """
    session = get_db_session()
    try:
        months_range = range(1, 13)
        
        def init_row(label, category):
            return {"label": label, "values": [0.0] * 12, "total": 0.0, "category": category}

        # Sub-groups
        rows_operasyonel = [
            init_row("Tabak Sayısı", "operasyonel"),
            init_row("Çalışma Gün Sayısı", "operasyonel"),
            init_row("Günlük Ziyaretçi Sayısı", "operasyonel"),
        ]
        rows_ciro = [
            init_row("Toplam Ciro", "ciro"),
            init_row("Şefteniste Ciro", "ciro"),
            init_row("Restoran Ciro", "ciro"),
        ]
        rows_stok = [
            init_row("Ay Başı Stok Değeri", "stok"),
            init_row("Ay içerisindeki Alımlar", "stok"),
            init_row("Ay içerisindeki İade", "stok"),
            init_row("Ay Sonu Sayılan Stok Değeri", "stok"),
        ]
        rows_maliyet = [
            init_row("Maliyet", "maliyet"),
            init_row("Maliyet %", "maliyet"),
        ]
        rows_personel = [
            init_row("Personel Sayısı (Sürücü Sayısı Hariç)", "personel"),
            init_row("Toplam Maaş Gideri (Sürücü Maaşı Hariç)", "personel"),
            init_row("Personel Maaş Giderleri; SGK, Stopaj (Muhtasar) Dahil", "personel"),
            init_row("Ortalama Kişi Başı Maaş", "personel"),
            init_row("Maaş Giderleri %", "personel"),
            init_row("VPS (Personel Başına Ziyaretçi Sayısı)", "personel"),
        ]
        rows_kira = [
            init_row("Stopajlı Kira", "kira"),
            init_row("Sabit Kira", "kira"),
            init_row("Ciro kira", "kira"),
            init_row("Depo Kira", "kira"),
            init_row("Ortak alan ve Genel Giderler", "kira"),
            init_row("Toplam Kira", "kira"),
            init_row("Toplam Kira %", "kira"),
        ]
        rows_lojistik = [
            init_row("Sürücü Sayısı", "lojistik"),
            init_row("Yemeksepeti Komisyon ve Lojistik Giderleri", "lojistik"),
            init_row("Paket Taxi Lojistik Giderleri", "lojistik"),
            init_row("Trendyol Komisyon ve Lojistik Giderleri", "lojistik"),
            init_row("Getir Getirsin Komisyon ve Lojistik Giderleri", "lojistik"),
            init_row("Migros Hemen Komisyon ve Lojistik Giderleri", "lojistik"),
            init_row("Dış Paket Kurye Giderleri", "lojistik"),
            init_row("İç Paket Kurye Giderleri (Personel Maaş vb.)", "lojistik"),
            init_row("İç Paket Yakıt Gideleri", "lojistik"),
            init_row("İç Paket Bakım Giderleri", "lojistik"),
            init_row("İç Paket Kiralama Giderleri", "lojistik"),
        ]

        diger_detayi_labels = [
            "Elektrik", "Su", "Doğalgaz Gideri", "İnternet ve Telefon", "Demirbaş Sayılmayan Giderler", 
            "Kredi Kartı Komisyon Giderleri", "Yemek Kartı Komisyon Giderleri", "Personel Yemek Giderleri", 
            "Temizlik Giderleri", "Bakım Onarım", "Personel Tazminat (Kıdem, İhbar vb.)",
            "İlaçlama", "Baca Temizliği", "ÇTV, İşgaliye, İlan Reklam Vergi Bedelleri", "Kırtasiye", 
            "İş güvenliği Uzmanı", "Müşavirlik Ücreti", "Hijyen / Gizli Müşteri Denetimi", "İşyeri Sigorta Gideri"
        ]
        rows_diger_detay = [init_row(label, "diger") for label in diger_detayi_labels]

        rows_summary = [
            init_row("Paket Komisyon ve Lojistik Giderleri", "komisyon"),
            init_row("Paket Komisyon ve Lojistik (Paket Satış) %", "komisyon"),
            init_row("Diğer Giderler", "gider"),
            init_row("Kredi Kartı Komisyon Giderleri", "komisyon"),
            init_row("Yemek Kartı Komisyon Giderleri", "komisyon"),
            init_row("Diğer Detay Toplamı", "gider"),
            init_row("Tavuk Dünyası Lojistik Giderleri", "gider"),
            init_row("Toplam Diğer Giderler", "gider"),
            init_row("Diğer Giderler %", "gider"),
            init_row("Tavuk Dünyası Ciro Primi", "prim"),
            init_row("Tavuk Dünyası Reklam Primi", "prim"),
            init_row("Ciro Primi ve Reklam Primi", "prim"),
            init_row("Ciro Primi ve Reklam %", "prim"),
            init_row("Toplam Kar / Zarar", "kar"),
            init_row("Toplam Kar / Zarar %", "kar"),
        ]

        # --- DATA FETCHING ---
        start_date_year = date(year, 1, 1)
        end_date_year = date(year, 12, 31)

        # 1. Gelir Ekstra (Tabak, Robotpos)
        gelir_ekstra = session.execute(
            text("SELECT Tarih, RobotPos_Tutar, Tabak_Sayisi FROM GelirEkstra WHERE Sube_ID = :sube_id AND Tarih BETWEEN :s AND :e"),
            {"sube_id": sube_id, "s": start_date_year, "e": end_date_year}
        ).fetchall()
        for d, r_pos, t_sayisi in gelir_ekstra:
            m_idx = d.month - 1
            rows_operasyonel[0]["values"][m_idx] += float(t_sayisi or 0)
            rows_ciro[0]["values"][m_idx] += float(r_pos or 0)

        for m in months_range:
            idx = m - 1
            days = calendar.monthrange(year, m)[1]
            rows_operasyonel[1]["values"][idx] = days
            tabak = rows_operasyonel[0]["values"][idx]
            rows_operasyonel[2]["values"][idx] = round(tabak / days, 2) if days > 0 else 0

        # 2. Gelir (Şefteniste - Ust_Kategori_ID = 1)
        sefteniste_res = session.execute(
            text("""
                SELECT g.Tarih, g.Tutar 
                FROM Gelir g
                JOIN Kategori k ON g.Kategori_ID = k.Kategori_ID
                WHERE g.Sube_ID = :sube_id AND g.Tarih BETWEEN :s AND :e AND k.Ust_Kategori_ID = 1
            """),
            {"sube_id": sube_id, "s": start_date_year, "e": end_date_year}
        ).fetchall()
        for d, t in sefteniste_res:
            rows_ciro[1]["values"][d.month - 1] += float(t or 0)
        
        for i in range(12):
            rows_ciro[2]["values"][i] = rows_ciro[0]["values"][i] - rows_ciro[1]["values"][i]

        # 3. Stok (Ay Sonu Sayılan Stok Değeri)
        sayimlar = session.execute(
            text("SELECT Donem, Malzeme_Kodu, Miktar FROM Stok_Sayim WHERE Sube_ID = :sube_id AND Donem DIV 100 = :yy"),
            {"sube_id": sube_id, "yy": int(str(year)[2:])}
        ).fetchall()
        
        fiyatlar = session.execute(
            text("SELECT Malzeme_Kodu, Fiyat, Gecerlilik_Baslangic_Tarih FROM Stok_Fiyat WHERE Sube_ID = :sube_id"),
            {"sube_id": sube_id}
        ).fetchall()
        
        def get_price(m_kodu, d_date):
            relevant = sorted([f for f in fiyatlar if f[0] == m_kodu and f[2] <= d_date], key=lambda x: x[2], reverse=True)
            return float(relevant[0][1]) if relevant else 0.0

        for donem, m_kodu, miktar in sayimlar:
            m = donem % 100
            if m < 1 or m > 12: continue
            end_date_val = date(year, m, calendar.monthrange(year, m)[1])
            price = get_price(m_kodu, end_date_val)
            rows_stok[3]["values"][m-1] += float(miktar or 0) * price

        # Ay Başı Stok Değeri
        prev_dec_donem = int(f"{str(year-1)[2:]}12")
        prev_dec_sayim = session.execute(
            text("SELECT Malzeme_Kodu, Miktar FROM Stok_Sayim WHERE Sube_ID = :sube_id AND Donem = :d"),
            {"sube_id": sube_id, "d": prev_dec_donem}
        ).fetchall()
        
        dec_date_prev = date(year-1, 12, 31)
        prev_stock_val = 0.0
        for mk, mq in prev_dec_sayim:
            prev_stock_val += float(mq or 0) * get_price(mk, dec_date_prev)
        
        rows_stok[0]["values"][0] = prev_stock_val
        for i in range(1, 12):
            rows_stok[0]["values"][i] = rows_stok[3]["values"][i-1]

        # 4. Expenses (Alımlar, Maaş, Kira, etc.)
        expense_rows = session.execute(
            text("""
                SELECT src, Donem, Tutar, Kategori_Adi, UstKategori_Adi, Aciklama 
                FROM (
                    SELECT 'efat' as src, Donem, Tutar, k.Kategori_Adi, uk.UstKategori_Adi, e.Aciklama
                    FROM e_Fatura e
                    JOIN Kategori k ON e.Kategori_ID = k.Kategori_ID
                    JOIN UstKategori uk ON k.Ust_Kategori_ID = uk.UstKategori_ID
                    WHERE e.Sube_ID = :sube_id AND e.Donem BETWEEN :s_donem AND :e_donem AND (e.Giden_Fatura = 0 OR e.Giden_Fatura IS NULL)
                    UNION ALL
                    SELECT 'diger' as src, Donem, Tutar, k.Kategori_Adi, uk.UstKategori_Adi, dh.Açıklama as Aciklama
                    FROM Diger_Harcama dh
                    JOIN Kategori k ON dh.Kategori_ID = k.Kategori_ID
                    JOIN UstKategori uk ON k.Ust_Kategori_ID = uk.UstKategori_ID
                    WHERE dh.Sube_ID = :sube_id AND dh.Donem BETWEEN :s_donem AND :e_donem
                ) t
            """),
            {"sube_id": sube_id, "s_donem": int(f"{str(year)[2:]}01"), "e_donem": int(f"{str(year)[2:]}12")}
        ).fetchall()

        # Group Expenses
        e_m = lambda d: (d % 100) - 1
        for src, donem, tutar, kat_ad, ust_ad, acik in expense_rows:
            m_idx = e_m(donem)
            val = float(tutar or 0)
            
            if ust_ad == 'Satışların Maliyeti':
                rows_stok[1]["values"][m_idx] += val
            
            if ust_ad == 'Maaş Giderleri':
                rows_personel[2]["values"][m_idx] += val
                
            if ust_ad == 'Diğer Giderler':
                rows_summary[2]["values"][m_idx] += val
            
            if kat_ad == 'Sabit Kira': rows_kira[1]["values"][m_idx] += val
            if kat_ad == 'Ciro Kira': rows_kira[2]["values"][m_idx] += val
            if kat_ad == 'Depo Kira': rows_kira[3]["values"][m_idx] += val
            if kat_ad == 'Ortak Gider': rows_kira[4]["values"][m_idx] += val

            if kat_ad == 'Yemek Sepeti (Online) Komisyonu':
                acik_l = (acik or "").lower()
                if 'yemek sepeti' in acik_l: rows_lojistik[1]["values"][m_idx] += val
                elif 'trendyol' in acik_l: rows_lojistik[3]["values"][m_idx] += val
                elif 'getir' in acik_l: rows_lojistik[4]["values"][m_idx] += val
                elif 'migros' in acik_l: rows_lojistik[5]["values"][m_idx] += val
            
            if kat_ad == 'Tavuk Dünyası Lojistik': rows_summary[6]["values"][m_idx] += val
            if kat_ad == 'Tavuk Dünyası Ciro Primi': rows_summary[9]["values"][m_idx] += val
            if kat_ad == 'Tavuk Dünyası Reklam Primi': rows_summary[10]["values"][m_idx] += val

            if kat_ad == 'Banka Komisyonu':
                rows_diger_detay[5]["values"][m_idx] += val
            elif kat_ad == 'Yemek Çekleri Komisyonu':
                rows_diger_detay[6]["values"][m_idx] += val
            elif kat_ad == 'Hijyen / Gizli Müşteri Denetimi':
                rows_diger_detay[17]["values"][m_idx] += val
            else:
                for r_d in rows_diger_detay:
                    if kat_ad == r_d["label"]:
                        r_d["values"][m_idx] += val
                        break

        # 5. Personnel Calculations
        calisanlar_res = session.execute(
            text("SELECT Sigorta_Giris, Sigorta_Cikis FROM Calisan WHERE Sube_ID = :sube_id"),
            {"sube_id": sube_id}
        ).fetchall()
        for m in months_range:
            m_idx = m - 1
            days_in_m = rows_operasyonel[1]["values"][m_idx]
            if days_in_m <= 0: continue
            m_start = date(year, m, 1)
            m_end = date(year, m, int(days_in_m))
            total_days_active = 0
            for g, c in calisanlar_res:
                if not g: continue
                eff_s = max(g, m_start)
                eff_e = min(c or date(2099,12,31), m_end)
                if eff_s <= eff_e:
                    total_days_active += (eff_e - eff_s).days + 1
            rows_personel[0]["values"][m_idx] = round(total_days_active / days_in_m, 2)
        
        # 6. derived & Totals
        for i in range(12):
            ciro = rows_ciro[0]["values"][i]
            # Maliyet
            maliyet = rows_stok[0]["values"][i] + rows_stok[1]["values"][i] - rows_stok[2]["values"][i] - rows_stok[3]["values"][i]
            rows_maliyet[0]["values"][i] = maliyet
            rows_maliyet[1]["values"][i] = round(maliyet / ciro * 100, 2) if ciro > 0 else 0
            
            # Personnel %
            p_maas = rows_personel[2]["values"][i]
            rows_personel[4]["values"][i] = round(p_maas / ciro * 100, 2) if ciro > 0 else 0
            p_count = rows_personel[0]["values"][i]
            rows_personel[3]["values"][i] = round(p_maas / p_count, 2) if p_count > 0 else 0
            rows_personel[5]["values"][i] = round(rows_operasyonel[2]["values"][i] / p_count, 2) if p_count > 0 else 0
            
            # Kira
            t_kira = sum(rows_kira[j]["values"][i] for j in range(1, 5))
            rows_kira[5]["values"][i] = t_kira
            rows_kira[6]["values"][i] = round(t_kira / ciro * 100, 2) if ciro > 0 else 0
            
            # Paket Komisyon
            t_pak = rows_lojistik[1]["values"][i] + rows_lojistik[3]["values"][i] + rows_lojistik[4]["values"][i] + rows_lojistik[5]["values"][i]
            rows_summary[0]["values"][i] = t_pak
            rows_summary[1]["values"][i] = round(t_pak / ciro * 100, 2) if ciro > 0 else 0
            
            # Diger Detay Toplami (Diger Giderler + Kredi Karti + Yemek Karti)
            t_diger_ust = rows_summary[2]["values"][i]
            t_kredi = rows_diger_detay[5]["values"][i]
            t_yemek = rows_diger_detay[6]["values"][i]
            t_detay = t_diger_ust + t_kredi + t_yemek
            
            rows_summary[5]["values"][i] = t_detay
            
            # Kredi/Yemek Kartı Komisyon (copied to summary)
            rows_summary[3]["values"][i] = t_kredi
            rows_summary[4]["values"][i] = t_yemek
            
            # Demirbaş Sayılmayan Giderler = Diğer Detay Toplamı - sum(other spesifik diger detay rows)
            sum_other_diger = sum(rows_diger_detay[j]["values"][i] for j in range(len(rows_diger_detay)) if j != 4)
            rows_diger_detay[4]["values"][i] = t_detay - sum_other_diger
            
            # Toplam Diğer Giderler = Diğer Detay Toplamı + Tavuk Dünyası Lojistik Giderleri (summary 6)
            t_toplam_diger = t_detay + rows_summary[6]["values"][i]
            rows_summary[7]["values"][i] = t_toplam_diger
            rows_summary[8]["values"][i] = round(t_toplam_diger / ciro * 100, 2) if ciro > 0 else 0
            
            # Ciro Primi & Reklam Primi
            t_prim = rows_summary[9]["values"][i] + rows_summary[10]["values"][i]
            rows_summary[11]["values"][i] = t_prim
            rows_summary[12]["values"][i] = round(t_prim / ciro * 100, 2) if ciro > 0 else 0
            
            # Kar / Zarar
            kar = ciro - maliyet - p_maas - t_kira - t_pak - t_toplam_diger - t_prim
            rows_summary[13]["values"][i] = kar
            rows_summary[14]["values"][i] = round(kar / ciro * 100, 2) if ciro > 0 else 0

        # Totals
        def finalize(all_rows):
            for r in all_rows:
                non_zero_vals = [v for v in r["values"] if v != 0]
                if r["category"] == "percentage" or " %" in r["label"]:
                    r["total"] = sum(non_zero_vals) / len(non_zero_vals) if non_zero_vals else 0.0
                else:
                    r["total"] = sum(r["values"])

        all_processed = rows_operasyonel + rows_ciro + rows_stok + rows_maliyet + rows_personel + rows_kira + rows_lojistik
        finalize(all_processed)
        finalize(rows_diger_detay)
        finalize(rows_summary)

        return {
            "processedExcelRows": all_processed,
            "processedDigerRows": rows_diger_detay,
            "processedMoreRows": rows_summary
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"processedExcelRows": [], "processedDigerRows": [], "processedMoreRows": []}
    finally:
        session.close()

def get_ozet_kontrol_raporu(db, sube_id: int, donem: int, show_gizli: bool = False) -> Dict:
    """Gets the consolidated summary metrics for Ozet Kontrol Raporu."""
    
    year = 2000 + (donem // 100)
    month = donem % 100
    start_date = date(year, month, 1)

    gizli_filter = "" if show_gizli else "AND k.Gizli = 0"

    # 1. Gelir Ekstra (Robotpos Tutar)
    robotpos_tutar = db.execute(
        text("SELECT IFNULL(SUM(RobotPos_Tutar), 0) FROM GelirEkstra WHERE Sube_ID = :sube_id AND YEAR(Tarih) = :year AND MONTH(Tarih) = :month"),
        {"sube_id": sube_id, "year": year, "month": month}
    ).scalar() or 0.0

    # 2. Toplam Satis (All Gelir)
    toplam_satis = db.execute(
        text(f"""
        SELECT IFNULL(SUM(g.Tutar), 0) FROM Gelir g
        JOIN Kategori k ON g.Kategori_ID = k.Kategori_ID
        WHERE g.Sube_ID = :sube_id AND YEAR(g.Tarih) = :year AND MONTH(g.Tarih) = :month
        {gizli_filter}
        """),
        {"sube_id": sube_id, "year": year, "month": month}
    ).scalar() or 0.0

    # 3. Nakit (Gelir that goes to Nakit)
    nakit = db.execute(
        text(f"""
        SELECT IFNULL(SUM(g.Tutar), 0) FROM Gelir g
        JOIN Kategori k ON g.Kategori_ID = k.Kategori_ID
        WHERE g.Sube_ID = :sube_id AND YEAR(g.Tarih) = :year AND MONTH(g.Tarih) = :month 
          AND (k.Kategori_Adi LIKE '%Nakit%')
          {gizli_filter}
        """),
        {"sube_id": sube_id, "year": year, "month": month}
    ).scalar() or 0.0

    # 4. Gunluk Harcama Diger
    dh_sql = text(f"""
        SELECT IFNULL(SUM(dh.Tutar), 0) FROM Diger_Harcama dh
        JOIN Kategori k ON dh.Kategori_ID = k.Kategori_ID
        WHERE dh.Sube_ID = :sube_id AND dh.Donem = :donem AND dh.Gunluk_Harcama = 1
        {gizli_filter}
    """)
    gh_diger = db.execute(dh_sql, {"sube_id": sube_id, "donem": donem}).scalar() or 0.0

    # 5. Gunluk Harcama eFatura
    ef_sql = text(f"""
        SELECT IFNULL(SUM(ef.Tutar), 0) FROM e_Fatura ef
        JOIN Kategori k ON ef.Kategori_ID = k.Kategori_ID
        WHERE ef.Sube_ID = :sube_id AND ef.Donem = :donem AND ef.Gunluk_Harcama = 1 AND (ef.Giden_Fatura = 0 OR ef.Giden_Fatura IS NULL)
        {gizli_filter}
    """)
    gh_efatura = db.execute(ef_sql, {"sube_id": sube_id, "donem": donem}).scalar() or 0.0

    # 6. Nakit Girisi Toplam (Fix: Sourced from all Nakit records to match Nakit Yatirma Kontrol Raporu)
    nakit_girisi = db.execute(
        text("SELECT IFNULL(SUM(Tutar), 0) FROM Nakit WHERE Sube_ID = :sube_id AND Donem = :donem"),
        {"sube_id": sube_id, "donem": donem}
    ).scalar() or 0.0

    # 7. Bankaya Yatan (Fix: Sourced from Odeme table Kategori_ID 60 to match Nakit Yatirma Kontrol Raporu)
    bankaya_yatan = db.execute(
        text("SELECT IFNULL(SUM(Tutar), 0) FROM Odeme WHERE Sube_ID = :sube_id AND Donem = :donem AND Kategori_ID = 60"),
        {"sube_id": sube_id, "donem": donem}
    ).scalar() or 0.0

    # 8. Gelir POS (Kredi Kartı)
    gelir_pos = db.execute(
        text(f"""
        SELECT IFNULL(SUM(g.Tutar), 0) FROM Gelir g
        JOIN Kategori k ON g.Kategori_ID = k.Kategori_ID
        WHERE g.Sube_ID = :sube_id AND YEAR(g.Tarih) = :year AND MONTH(g.Tarih) = :month 
          AND (k.Kategori_Adi LIKE '%POS%')
          {gizli_filter}
        """),
        {"sube_id": sube_id, "year": year, "month": month}
    ).scalar() or 0.0

    # 9. POS Hareketleri (Banka)
    pos_hareket = db.execute(
        text("SELECT IFNULL(SUM(Islem_Tutari), 0) FROM POS_Hareketleri WHERE Sube_ID = :sube_id AND YEAR(Islem_Tarihi) = :year AND MONTH(Islem_Tarihi) = :month"),
        {"sube_id": sube_id, "year": year, "month": month}
    ).scalar() or 0.0

    # 10. Online & Yemek Çeki Metrics (Sourced from Dashboard logic)
    from app.modules.invoicing.queries import get_online_kontrol_dashboard_data, get_yemek_ceki_kontrol_dashboard_data
    online_res = get_online_kontrol_dashboard_data(db, sube_id, donem)
    online_summary = online_res.get('summary', {})
    online_gelir = float(online_summary.get('gelir_toplam', 0))
    online_virman = float(online_summary.get('toplam_virman', 0))

    # 12 & 13. Yemek Çeki Metrics (Sourced from Yemek Çeki Kontrol Dashboard logic)
    yemek_res = get_yemek_ceki_kontrol_dashboard_data(db, sube_id, donem)
    yemek_stats = yemek_res.get('stats', {})
    yemek_ceki_aylik = float(yemek_stats.get('total_gelir', 0))
    yemek_ceki_toplam = float(yemek_stats.get('total_donem_tutar', 0))

    # 14. TOTAL REVENUE & EXPENSE for Summary Cards (aligned with Dashboard logic)
    # Total Revenue (already fetched as toplam_satis but let's be explicit)
    total_rev = float(toplam_satis)

    # EFatura Expenses (ALL monthly, not just Gunluk)
    total_efat_exp = db.execute(
        text(f"""
        SELECT IFNULL(SUM(ef.Tutar), 0) FROM e_Fatura ef
        JOIN Kategori k ON ef.Kategori_ID = k.Kategori_ID
        WHERE ef.Sube_ID = :sube_id AND ef.Donem = :donem AND (ef.Giden_Fatura = 0 OR ef.Giden_Fatura IS NULL)
        {gizli_filter}
        """),
        {"sube_id": sube_id, "donem": donem}
    ).scalar() or 0.0

    # Diger Harcama (ALL monthly)
    total_dh_exp = db.execute(
        text(f"""
        SELECT IFNULL(SUM(dh.Tutar), 0) FROM Diger_Harcama dh
        JOIN Kategori k ON dh.Kategori_ID = k.Kategori_ID
        WHERE dh.Sube_ID = :sube_id AND dh.Donem = :donem
        {gizli_filter}
        """),
        {"sube_id": sube_id, "donem": donem}
    ).scalar() or 0.0

    # B2B Borç
    total_b2b_exp = db.execute(
        text(f"""
        SELECT IFNULL(SUM(b.Borc), 0) FROM B2B_Ekstre b
        JOIN Kategori k ON b.Kategori_ID = k.Kategori_ID
        WHERE b.Sube_ID = :sube_id AND b.Donem = :donem
        {gizli_filter}
        """),
        {"sube_id": sube_id, "donem": donem}
    ).scalar() or 0.0

    total_exp = float(total_efat_exp) + float(total_dh_exp) + float(total_b2b_exp)

    # Stok Farkı (Optionally include if shown in old system)
    stok_degeri = 0.0
    stok_fark = 0.0
    if show_gizli:
        sql_stock_val = text("""
            SELECT SUM(s.Miktar * COALESCE(sf.Fiyat,0)) FROM Stok_Sayim s
            LEFT JOIN (
                SELECT st.* FROM Stok_Fiyat st
                INNER JOIN (
                    SELECT Malzeme_Kodu, MAX(Gecerlilik_Baslangic_Tarih) as max_date
                    FROM Stok_Fiyat
                    GROUP BY Malzeme_Kodu
                ) ms ON st.Malzeme_Kodu = ms.Malzeme_Kodu AND st.Gecerlilik_Baslangic_Tarih = ms.max_date
            ) sf ON sf.Malzeme_Kodu = s.Malzeme_Kodu
            WHERE s.Sube_ID = :sube_id AND s.Donem = :donem
        """)
        stok_degeri = db.execute(sql_stock_val, {"sube_id": sube_id, "donem": donem}).scalar() or 0.0
        
        prev_month_date = start_date - timedelta(days=1)
        prev_donem = int(f"{prev_month_date.year % 100:02d}{prev_month_date.month:02d}")
        prev_stok_degeri = db.execute(sql_stock_val, {"sube_id": sube_id, "donem": prev_donem}).scalar() or 0.0
        stok_fark = float(stok_degeri) - float(prev_stok_degeri)

    cirodan_kalan = total_rev - total_exp
    donem_kar_zarar = cirodan_kalan + stok_fark

    return {
        "robotposTutar": float(robotpos_tutar),
        "toplamSatis": float(toplam_satis),
        "nakit": float(nakit),
        "gunlukHarcamaDiger": float(gh_diger),
        "gunlukHarcamaEFatura": float(gh_efatura),
        "nakitGirisiToplam": float(nakit_girisi),
        "bankayaYatan": float(bankaya_yatan),
        "gelirPOS": float(gelir_pos),
        "posHareketleri": float(pos_hareket),
        "onlineGelirToplam": float(online_gelir),
        "onlineVirmanToplam": float(online_virman),
        "yemekCekiAylikGelir": float(yemek_ceki_aylik),
        "yemekCekiDonemToplam": float(yemek_ceki_toplam),
        "financial": {
            "total_revenue": total_rev,
            "total_expense": total_exp,
            "cirodan_kalan": cirodan_kalan,
            "stok_farki": stok_fark,
            "donem_kar_zarar": donem_kar_zarar
        }
    }

def get_nakit_akis_gelir_raporu(start_date: str, end_date: str, sube_id: int):
    """
    Returns daily cash flow and income data for a given branch and date range.
    """
    from datetime import datetime, timedelta
    from sqlalchemy import text
    from app.common.database import get_db_session

    db = get_db_session()
    
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    results = []
    current_dt = start_dt
    
    # Pre-fetch branch info if needed or just use sube_id
    
    while current_dt <= end_dt:
        date_str = current_dt.strftime('%Y-%m-%d')
        
        # 1. Tahmini Nakit Components
        # Nakit Gelir
        nakit_gelir = db.execute(
            text("""
            SELECT IFNULL(SUM(g.Tutar), 0) FROM Gelir g
            JOIN Kategori k ON g.Kategori_ID = k.Kategori_ID
            WHERE g.Sube_ID = :sube_id AND g.Tarih = :date AND k.Kategori_Adi LIKE '%Nakit%'
            """),
            {"sube_id": sube_id, "date": date_str}
        ).scalar() or 0.0
        
        # Daily Expenses (e-Fatura)
        expenses_efatura = db.execute(
            text("""
            SELECT IFNULL(SUM(Tutar), 0) FROM e_Fatura 
            WHERE Sube_ID = :sube_id AND Fatura_Tarihi = :date AND Gunluk_Harcama = 1 AND (Giden_Fatura = 0 OR Giden_Fatura IS NULL)
            """),
            {"sube_id": sube_id, "date": date_str}
        ).scalar() or 0.0
        
        # Daily Expenses (Other)
        expenses_other = db.execute(
            text("""
            SELECT IFNULL(SUM(Tutar), 0) FROM Diger_Harcama 
            WHERE Sube_ID = :sube_id AND Belge_Tarihi = :date AND Gunluk_Harcama = 1
            """),
            {"sube_id": sube_id, "date": date_str}
        ).scalar() or 0.0
        
        tahmini_nakit = float(nakit_gelir) - float(expenses_efatura) - float(expenses_other)
        
        # 2. POS Ödemesi
        pos_odeme = db.execute(
            text("SELECT IFNULL(SUM(Islem_Tutari), 0) FROM POS_Hareketleri WHERE Sube_ID = :sube_id AND Islem_Tarihi = :date"),
            {"sube_id": sube_id, "date": date_str}
        ).scalar() or 0.0
        pos_odeme = float(pos_odeme)
        
        # 3. Yemek Çeki
        yemek_ceki = db.execute(
            text("SELECT IFNULL(SUM(Tutar), 0) FROM Yemek_Ceki WHERE Sube_ID = :sube_id AND Tarih = :date"),
            {"sube_id": sube_id, "date": date_str}
        ).scalar() or 0.0
        yemek_ceki = float(yemek_ceki)
        
        # 4. Online Virman (From B2B_Ekstre with Online filters)
        online_virman = db.execute(
            text("""
            SELECT IFNULL(SUM(b.Alacak), 0) FROM B2B_Ekstre b
            JOIN Kategori k ON b.Kategori_ID = k.Kategori_ID
            WHERE b.Sube_ID = :sube_id AND b.Tarih = :date 
              AND (
                  k.Kategori_Adi LIKE '%Yemeksepeti%' OR 
                  k.Kategori_Adi LIKE '%Yemek Sepeti%' OR 
                  k.Kategori_Adi LIKE '%Trendyol%' OR 
                  k.Kategori_Adi LIKE '%Getir%' OR 
                  k.Kategori_Adi LIKE '%Migros%'
              )
            """),
            {"sube_id": sube_id, "date": date_str}
        ).scalar() or 0.0
        online_virman = float(online_virman)
        
        # Calculations for the row
        daily_total = float(tahmini_nakit) + pos_odeme + yemek_ceki + online_virman
        
        results.append({
            "date": date_str,
            "display_date": current_dt.strftime('%d.%m.%Y'),
            "day_name": current_dt.strftime('%A'), # Needs localization if handled in template
            "tahmini_nakit": tahmini_nakit,
            "pos_odeme": pos_odeme,
            "yemek_ceki": yemek_ceki,
            "online_virman": online_virman,
            "total": daily_total
        })
        
        current_dt += timedelta(days=1)
        
    db.close()
    
    # Calculate Grand Totals
    summary = {
        "total_tahmini_nakit": sum(r["tahmini_nakit"] for r in results),
        "total_pos_odeme": sum(r["pos_odeme"] for r in results),
        "total_yemek_ceki": sum(r["yemek_ceki"] for r in results),
        "total_online_virman": sum(r["online_virman"] for r in results),
        "grand_total": sum(r["total"] for r in results)
    }
    
    return {"daily": results, "summary": summary}


def get_cari_borc_takip_raporu(start_date: str, sube_id: int):
    """
    Exact mirror of GumusBulut CariBorcTakipSistemiPage.tsx logic:
    1. get_cari_mutabakat  → per firm: SUM(all Mutabakat.Tutar), MAX(Mutabakat_Tarihi)
    2. Use the EARLIEST mutabakat date (across all firms) as the floor for query
    3. get_cari_fatura     → invoices WHERE Fatura_Tarihi >= floor  (no upper limit)
    4. get_cari_odeme      → payments WHERE Tarih >= floor (-1*Tutar in SQL)
    5. Per firm, the effective start = mutabakat_date (for Cari Borç) OR start_date (others)
    6. Balance = SUM(mutabakat) + SUM(invoices >= startDate) + SUM(payments >= startDate)
       (payments are already negative from the SQL)
    """
    from sqlalchemy import text
    from app.common.database import get_db_session
    from datetime import datetime
    from dateutil.parser import parse as date_parse

    db = get_db_session()
    try:
        def fmt_date(d):
            if d is None:
                return ""
            if hasattr(d, 'strftime'):
                return d.strftime('%d.%m.%Y')
            return str(d)

        # ── 1. get_cari_mutabakat: SUM(Tutar) all-time, MAX(Mutabakat_Tarihi) ──
        sql_mutabakat = text("""
            SELECT
                C.Cari_ID,
                C.Alici_Unvani,
                C.Cari,
                MAX(M.Mutabakat_Tarihi) AS Son_Mutabakat_Tarihi,
                SUM(M.Tutar)            AS Toplam_Mutabakat_Tutari
            FROM Cari AS C
            LEFT JOIN Mutabakat AS M ON M.Cari_ID = C.Cari_ID
            WHERE C.Aktif_Pasif = 1
            GROUP BY C.Cari_ID, C.Alici_Unvani, C.Cari
            ORDER BY Son_Mutabakat_Tarihi DESC
        """)
        mutabakat_rows = db.execute(sql_mutabakat).fetchall()
        if not mutabakat_rows:
            return _empty_cari_result()

        # Build mutabakat map indexed by Alici_Unvani
        mut_map = {}
        for m in mutabakat_rows:
            mut_map[m.Alici_Unvani] = m

        # Determine effective start date for fetching invoices/payments:
        # Use the EARLIEST mutabakat date across all firms as the floor (GumusBulut logic)
        mut_dates = [
            m.Son_Mutabakat_Tarihi
            for m in mutabakat_rows
            if m.Son_Mutabakat_Tarihi is not None
        ]
        if mut_dates:
            earliest_mut = min(mut_dates)
            # Compare as dates
            try:
                sd = datetime.strptime(start_date, '%Y-%m-%d').date()
            except Exception:
                sd = datetime.today().date()
            # If earliest mutabakat is before the selected date, use it as the floor
            if hasattr(earliest_mut, 'date'):
                em_date = earliest_mut.date()
            else:
                em_date = earliest_mut
            effective_floor = em_date if em_date < sd else sd
        else:
            effective_floor = start_date

        # ── 2. get_cari_fatura: invoices >= effective_floor (the critical GumusBulut >=) ──
        sql_fatura = text("""
            SELECT
                E.Fatura_ID,
                E.Alici_Unvani,
                E.Fatura_Tarihi,
                E.Fatura_Numarasi,
                E.Tutar,
                E.Kategori_ID,
                C.Cari_ID,
                CASE
                    WHEN C.Cari IS NULL THEN 'Belirsiz'
                    WHEN C.Cari = 0    THEN 'Cari Olmayan Borç'
                    ELSE 'Cari Borç'
                END AS Cari_Durumu
            FROM e_Fatura E
            LEFT JOIN Cari C
                ON C.Alici_Unvani = E.Alici_Unvani
               AND C.e_Fatura_Kategori_ID = E.Kategori_ID
            WHERE E.Fatura_Tarihi >= :floor
              AND E.Sube_ID = :sube_id
              AND (E.Giden_Fatura = 0 OR E.Giden_Fatura IS NULL)
            ORDER BY E.Alici_Unvani, E.Fatura_Tarihi ASC
        """)
        fatura_rows = db.execute(sql_fatura, {
            "floor": effective_floor, "sube_id": sube_id
        }).fetchall()

        # ── 3. get_cari_odeme: payments >= effective_floor, Tutar negative (−1 * Tutar) ──
        sql_odeme = text("""
            SELECT
                C.Cari_ID,
                C.Alici_Unvani,
                -1 * O.Tutar AS Tutar,
                O.Tarih
            FROM Cari C
            INNER JOIN Odeme_Referans ORF
                ON C.Referans_ID = ORF.Referans_ID
            INNER JOIN Odeme O
                ON O.Kategori_ID = ORF.Kategori_ID
               AND O.Aciklama LIKE CONCAT('%', ORF.Referans_Metin, '%')
            WHERE O.Tarih >= :floor
              AND O.Sube_ID = :sube_id
            ORDER BY C.Alici_Unvani, O.Tarih DESC
        """)
        odeme_rows = db.execute(sql_odeme, {
            "floor": effective_floor, "sube_id": sube_id
        }).fetchall()

        # ── 4. Group by Alici_Unvani ──────────────────────────────────────────
        fatura_by_unvan = {}
        for f in fatura_rows:
            key = f.Alici_Unvani or "Bilinmeyen"
            fatura_by_unvan.setdefault(key, []).append(f)

        odeme_by_unvan = {}
        for o in odeme_rows:
            key = o.Alici_Unvani or "Bilinmeyen"
            odeme_by_unvan.setdefault(key, []).append(o)

        # ── 5. Build result per firm (GumusBulut firmaListesi memo logic) ───────
        try:
            sd_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except Exception:
            sd_date = datetime.today().date()

        def to_date(v):
            if v is None:
                return None
            if hasattr(v, 'date'):
                return v.date()
            if hasattr(v, 'year'):
                return v
            return None

        processed = []
        handled_unvanlar = set()

        for m in mutabakat_rows:
            unvan = m.Alici_Unvani
            handled_unvanlar.add(unvan)

            # Determine Cari_Durumu from fatura join results (same as GumusBulut)
            firm_faturalar_all = fatura_by_unvan.get(unvan, [])
            cari_durumlari = [f.Cari_Durumu for f in firm_faturalar_all if f.Cari_Durumu]
            if 'Cari Borç' in cari_durumlari:
                status = 'Cari Borç'
            elif 'Cari Olmayan Borç' in cari_durumlari:
                status = 'Cari Olmayan Borç'
            else:
                # Fallback: use Cari column from Cari table (already in mut_map)
                cari_col = m.Cari
                if cari_col == 1:
                    status = 'Cari Borç'
                elif cari_col == 0:
                    status = 'Cari Olmayan Borç'
                else:
                    status = 'Belirsiz'

            mut_tarih = to_date(m.Son_Mutabakat_Tarihi)
            mut_tutar = float(m.Toplam_Mutabakat_Tutari or 0)

            # Per-firm effective start: mutabakat date for "Cari Borç", else baslangic_tarih
            if status == 'Cari Borç' and mut_tarih:
                firm_start = mut_tarih
            else:
                firm_start = sd_date

            # Filter invoices and payments >= firm_start (GumusBulut uses >=)
            faturalar = [f for f in firm_faturalar_all
                         if to_date(f.Fatura_Tarihi) and to_date(f.Fatura_Tarihi) >= firm_start]
            odemeler  = [o for o in odeme_by_unvan.get(unvan, [])
                         if to_date(o.Tarih) and to_date(o.Tarih) >= firm_start]

            if not faturalar and not odemeler and mut_tutar == 0:
                continue

            fatura_toplam = sum(float(f.Tutar or 0) for f in faturalar)
            # o.Tutar from the SQL is positive (-1 * negative db value = positive)
            odeme_toplam = sum(float(o.Tutar or 0) for o in odemeler)

            # Balance = mutabakat + faturalar - odemeler
            balance = mut_tutar + fatura_toplam - odeme_toplam

            # Build detail lists
            fatura_details = []
            for f in faturalar:
                fatura_details.append({
                    "no": f.Fatura_Numarasi or "N/A",
                    "date": fmt_date(f.Fatura_Tarihi),
                    "amount": float(f.Tutar or 0),
                })

            odeme_details = []
            for o in odemeler:
                odeme_details.append({
                    "date": fmt_date(o.Tarih),
                    "amount": float(o.Tutar or 0),  # positive value
                })

            processed.append({
                "name": unvan,
                "status": status,
                "balance": balance,
                "mutabakat_tutar": mut_tutar,
                "mutabakat_tarih": fmt_date(mut_tarih),
                "fatura_toplam": fatura_toplam,
                "odeme_toplam": odeme_toplam,
                "fatura_details": fatura_details,
                "odeme_details": odeme_details,
            })

        # ── 6. Belirsiz: invoices for firms NOT in Cari table ─────────────────
        for unvan, invoices in fatura_by_unvan.items():
            if unvan in handled_unvanlar:
                continue
            fatura_toplam = sum(float(f.Tutar or 0) for f in invoices)
            if fatura_toplam == 0:
                continue
            fatura_details = [{"no": f.Fatura_Numarasi or "N/A",
                                "date": fmt_date(f.Fatura_Tarihi),
                                "amount": float(f.Tutar or 0)} for f in invoices]
            processed.append({
                "name": unvan,
                "status": "Belirsiz",
                "balance": fatura_toplam,
                "mutabakat_tutar": 0.0,
                "mutabakat_tarih": "",
                "fatura_toplam": fatura_toplam,
                "odeme_toplam": 0.0,
                "fatura_details": fatura_details,
                "odeme_details": [],
            })

        # ── 7. Categorize & sort ──────────────────────────────────────────────
        cari_borclar = sorted([x for x in processed if x["status"] == "Cari Borç"],
                              key=lambda x: x["balance"], reverse=True)
        cari_olmayan = sorted([x for x in processed if x["status"] == "Cari Olmayan Borç"],
                              key=lambda x: x["balance"], reverse=True)
        belirsiz     = sorted([x for x in processed if x["status"] == "Belirsiz"],
                              key=lambda x: abs(x["balance"]), reverse=True)

        tumu = cari_borclar + cari_olmayan + belirsiz
        return {
            "summary": {
                "tumu_count": len(tumu),
                "tumu_bakiye": sum(x["balance"] for x in tumu),
                "cari_count": len(cari_borclar),
                "cari_bakiye": sum(x["balance"] for x in cari_borclar),
                "cari_olmayan_count": len(cari_olmayan),
                "cari_olmayan_bakiye": sum(x["balance"] for x in cari_olmayan),
                "belirsiz_count": len(belirsiz),
                "belirsiz_bakiye": sum(x["balance"] for x in belirsiz),
            },
            "lists": {
                "cari_borclar": cari_borclar,
                "cari_olmayan": cari_olmayan,
                "belirsiz": belirsiz,
                "tumu": tumu,
            }
        }
    except Exception:
        import traceback
        traceback.print_exc()
        return _empty_cari_result()

