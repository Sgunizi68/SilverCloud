from typing import Dict
from sqlalchemy import select, func, text
from app.common.database import get_db_session
from app.models import EFatura, Odeme, Nakit, Stok, StokFiyat, Calisan
from datetime import datetime, date, timedelta


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


def dashboard_report(donem: int, sube_id: int) -> Dict:
    session = get_db_session()
    try:
        try:
            start_date, end_date = _donem_to_dates(donem)
        except Exception:
            today = date.today()
            start_date = date(today.year, today.month, 1)
            end_date = date(today.year, today.month, 28)

        # Revenues grouped by parent category (UstKategori)
        sql_revenues = text("""
            SELECT uk.UstKategori_Adi as group_name, SUM(e.Tutar) as total
            FROM e_Fatura e
            LEFT JOIN Kategori k ON e.Kategori_ID = k.Kategori_ID
            LEFT JOIN UstKategori uk ON k.Ust_Kategori_ID = uk.UstKategori_ID
            WHERE e.Donem = :donem AND e.Sube_ID = :sube_id AND (e.Giden_Fatura = 0 OR e.Giden_Fatura IS NULL)
            GROUP BY uk.UstKategori_Adi
            ORDER BY total DESC
        """)
        try:
            revs = session.execute(sql_revenues, {"donem": donem, "sube_id": sube_id}).fetchall()
            gelirler = [{"label": r[0] or 'Diğer', "amount": float(r[1] or 0)} for r in revs]
        except Exception:
            gelirler = []

        # Expenses: sum of Odeme in period
        sql_expenses = text("""
            SELECT 'Ödemeler' as group_name, SUM(o.Tutar) as total
            FROM Odeme o
            WHERE o.Tarih >= :start_date AND o.Tarih <= :end_date AND o.Sube_ID = :sube_id
        """)
        try:
            exp_row = session.execute(sql_expenses, {"start_date": start_date, "end_date": end_date, "sube_id": sube_id}).fetchone()
            exp_total = 0
            if exp_row:
                try:
                    exp_total = float(exp_row[1] or 0)
                except Exception:
                    exp_total = 0
            # normalize payments as positive display values
            giderler = [{"label": 'Ödemeler', "amount": abs(exp_total)}]
        except Exception:
            giderler = []

        # RobotPos total
        sql_pos = text("""
            SELECT SUM(Net_Tutar) FROM POS_Hareketleri
            WHERE Hesaba_Gecis >= :start_date AND Hesaba_Gecis <= :end_date AND Sube_ID = :sube_id
        """)
        try:
            pos_row = session.execute(sql_pos, {"start_date": start_date, "end_date": end_date, "sube_id": sube_id}).fetchone()
            robotpos_total = float(pos_row[0] or 0)
        except Exception:
            robotpos_total = 0.0

        # Stock valuation
        sql_stock = text("""
            SELECT SUM(s.Miktar * COALESCE(sf.Fiyat,0)) FROM Stok s
            LEFT JOIN (
                SELECT st.* FROM StokFiyat st
                INNER JOIN (
                    SELECT Malzeme_Kodu, MAX(Gecerlilik_Baslangic_Tarih) as max_date
                    FROM StokFiyat
                    GROUP BY Malzeme_Kodu
                ) ms ON st.Malzeme_Kodu = ms.Malzeme_Kodu AND st.Gecerlilik_Baslangic_Tarih = ms.max_date
            ) sf ON sf.Malzeme_Kodu = s.Malzeme_Kodu
            WHERE s.Sube_ID = :sube_id
        """)
        try:
            stock_row = session.execute(sql_stock, {"sube_id": sube_id}).fetchone()
            stok_degeri = float(stock_row[0] or 0)
        except Exception:
            stok_degeri = 0.0

        # ensure totals use absolute values for expenses
        total_revenue = sum(i['amount'] for i in gelirler)
        total_expense = sum(abs(i['amount']) for i in giderler)
        financial = {
            'ciro': total_revenue,
            'gider': total_expense,
            'ciro_kalan': total_revenue - total_expense,
            'donem_kar_zarar': (total_revenue - total_expense) + stok_degeri
        }

        # Additional detailed sections inspired by GumusBulut
        # Yemek çeki breakdown (by provider)
        sql_yemek_ceki = text("""
            SELECT Y.Referans AS provider, SUM(Y.Tutar) as total
            FROM Yemek_Ceki Y
            WHERE Y.Odeme_Tarih >= :start_date AND Y.Odeme_Tarih <= :end_date AND Y.Sube_ID = :sube_id
            GROUP BY Y.Referans
            ORDER BY total DESC
        """)
        try:
            yrows = session.execute(sql_yemek_ceki, {"start_date": start_date, "end_date": end_date, "sube_id": sube_id}).fetchall()
            yemek_ceki = [{"label": r[0] or 'Diğer', "amount": float(r[1] or 0)} for r in yrows]
        except Exception:
            yemek_ceki = []

        # POS breakdown by terminal/shop description
        sql_pos_breakdown = text("""
            SELECT PH.Aciklama as channel, SUM(PH.Net_Tutar) as total
            FROM POS_Hareketleri PH
            WHERE PH.Hesaba_Gecis >= :start_date AND PH.Hesaba_Gecis <= :end_date AND PH.Sube_ID = :sube_id
            GROUP BY PH.Aciklama
            ORDER BY total DESC
        """)
        try:
            pos_rows = session.execute(sql_pos_breakdown, {"start_date": start_date, "end_date": end_date, "sube_id": sube_id}).fetchall()
            pos_breakdown = [{"label": r[0] or 'POS', "amount": float(r[1] or 0)} for r in pos_rows]
        except Exception:
            pos_breakdown = []

        # Previous period stock valuation: previous month donem
        prev_month = start_date.month - 1
        prev_year = start_date.year
        if prev_month == 0:
            prev_month = 12
            prev_year -= 1
        prev_donem = int(str(prev_year)[2:] + str(prev_month).zfill(2))
        # approximate by reusing stock valuation method (current latest prices) - GumusBulut used history, this is approximation
        try:
            prev_stock_row = session.execute(sql_stock, {"sube_id": sube_id}).fetchone()
            prev_stok_degeri = float(prev_stock_row[0] or 0)
        except Exception:
            prev_stok_degeri = 0.0

        stok_fark = stok_degeri - prev_stok_degeri

        # attach bayi karlilik (detailed profitability) rows
        try:
            # convert donem YYMM to year int for bayi report
            s = str(donem)
            if len(s) == 4:
                year = 2000 + int(s[:2])
            elif len(s) == 6:
                year = int(s[:4])
            else:
                year = date.today().year
            bayi = get_bayi_karlilik_raporu(year=year, sube_id=sube_id)
        except Exception:
            bayi = None

        # Before returning, normalize bayi_karlilik numeric signs for display
        if bayi:
            try:
                def abs_row(row):
                    vals = [abs(float(v)) for v in (row.get('values') or [])]
                    row['values'] = vals
                    row['total'] = float(sum(vals))
                    return row
                if isinstance(bayi, dict):
                    for key in ('processedExcelRows','processedDigerRows','processedMoreRows'):
                        arr = bayi.get(key) or []
                        new = []
                        for r in arr:
                            if r.get('category') in ('gider','maliyet','diger'):
                                new.append(abs_row(r))
                            else:
                                r['values'] = [float(v) for v in (r.get('values') or [])]
                                r['total'] = float(sum(r['values']))
                                new.append(r)
                        bayi[key] = new
            except Exception:
                pass

        return {
            'gelirler': gelirler,
            'giderler': giderler,
            'yemek_ceki': yemek_ceki,
            'pos_breakdown': pos_breakdown,
            'stok': {'stok_degeri': stok_degeri, 'prev_stok_degeri': prev_stok_degeri, 'stok_farki': stok_fark},
            'robotpos_total': robotpos_total,
            'financial_summary': financial,
            'bayi_karlilik': bayi
        }
    finally:
        session.close()


def get_bayi_karlilik_raporu(year: int, sube_id: int) -> Dict:
    """
    Port of GumusBulut.get_bayi_karlilik_raporu: returns categorized monthly rows.
    This is a simplified but compatible port: returns processedExcelRows and other sections.
    """
    session = get_db_session()
    try:
        from decimal import Decimal

        def get_monthly_values(query_results):
            monthly_values = [Decimal('0.0')] * 12
            for month, total in query_results:
                try:
                    m = int(month)
                except Exception:
                    continue
                if 1 <= m <= 12:
                    monthly_values[m - 1] = Decimal(total) if total else Decimal('0.0')
            return monthly_values

        # helper to find kategori id by name
        def get_kategori_id(kategori_adi: str):
            try:
                q = text("SELECT Kategori_ID FROM Kategori WHERE Kategori_Adi = :adi LIMIT 1")
                r = session.execute(q, {"adi": kategori_adi}).fetchone()
                return r[0] if r else None
            except Exception:
                return None

        # base query for e_Fatura totals per month filtered by year and sube
        base_sql = text("""
            SELECT EXTRACT(MONTH FROM e.Fatura_Tarihi) as month, SUM(e.Tutar) as total
            FROM e_Fatura e
            WHERE e.Sube_ID = :sube_id AND EXTRACT(YEAR FROM e.Fatura_Tarihi) = :year
            GROUP BY month
        """)

        # Example categories to extract (from GumusBulut): Yemek Sepeti, Trendyol, Getir, Migros
        yemeksepeti_kategori_id = get_kategori_id('Yemek Sepeti (Online) Komisyonu')
        yemeksepeti_values = [Decimal('0.0')] * 12
        if yemeksepeti_kategori_id:
            sql = text("""
                SELECT EXTRACT(MONTH FROM e.Fatura_Tarihi) as month, SUM(e.Tutar) as total
                FROM e_Fatura e
                WHERE e.Sube_ID = :sube_id AND EXTRACT(YEAR FROM e.Fatura_Tarihi) = :year
                  AND e.Kategori_ID = :kat_id AND e.Aciklama LIKE :like
                GROUP BY month
            """)
            rows = session.execute(sql, {"sube_id": sube_id, "year": year, "kat_id": yemeksepeti_kategori_id, "like": '%Yemek Sepeti%'}).fetchall()
            yemeksepeti_values = get_monthly_values(rows)

        # Trendyol
        trendyol_values = [Decimal('0.0')] * 12
        if yemeksepeti_kategori_id:
            rows = session.execute(text("""
                SELECT EXTRACT(MONTH FROM e.Fatura_Tarihi) as month, SUM(e.Tutar) as total
                FROM e_Fatura e
                WHERE e.Sube_ID = :sube_id AND EXTRACT(YEAR FROM e.Fatura_Tarihi) = :year
                  AND e.Kategori_ID = :kat_id AND e.Aciklama LIKE :like
                GROUP BY month
            """), {"sube_id": sube_id, "year": year, "kat_id": yemeksepeti_kategori_id, "like": '%Trendyol%'}).fetchall()
            trendyol_values = get_monthly_values(rows)

        # Getir
        getir_values = [Decimal('0.0')] * 12
        if yemeksepeti_kategori_id:
            rows = session.execute(text("""
                SELECT EXTRACT(MONTH FROM e.Fatura_Tarihi) as month, SUM(e.Tutar) as total
                FROM e_Fatura e
                WHERE e.Sube_ID = :sube_id AND EXTRACT(YEAR FROM e.Fatura_Tarihi) = :year
                  AND e.Kategori_ID = :kat_id AND e.Aciklama LIKE :like
                GROUP BY month
            """), {"sube_id": sube_id, "year": year, "kat_id": yemeksepeti_kategori_id, "like": '%Getir%'}).fetchall()
            getir_values = get_monthly_values(rows)

        # Migros
        migros_values = [Decimal('0.0')] * 12
        if yemeksepeti_kategori_id:
            rows = session.execute(text("""
                SELECT EXTRACT(MONTH FROM e.Fatura_Tarihi) as month, SUM(e.Tutar) as total
                FROM e_Fatura e
                WHERE e.Sube_ID = :sube_id AND EXTRACT(YEAR FROM e.Fatura_Tarihi) = :year
                  AND e.Kategori_ID = :kat_id AND e.Aciklama LIKE :like
                GROUP BY month
            """), {"sube_id": sube_id, "year": year, "kat_id": yemeksepeti_kategori_id, "like": '%Migros%'}).fetchall()
            migros_values = get_monthly_values(rows)

        # Nakit (monthly)
        try:
            sql_nakit = text("""
                SELECT EXTRACT(MONTH FROM n.Tarih) as month, SUM(n.Tutar) as total
                FROM Nakit n
                WHERE n.Sube_ID = :sube_id AND EXTRACT(YEAR FROM n.Tarih) = :year
                GROUP BY month
            """)
            nakit_rows = session.execute(sql_nakit, {"sube_id": sube_id, "year": year}).fetchall()
            nakit_values = get_monthly_values(nakit_rows)
        except Exception:
            nakit_values = [Decimal('0.0')] * 12

        # Yemek Ceki totals per month (aggregate)
        try:
            sql_y = text("""
                SELECT EXTRACT(MONTH FROM Y.Odeme_Tarih) as month, SUM(Y.Tutar) as total
                FROM Yemek_Ceki Y
                WHERE Y.Sube_ID = :sube_id AND EXTRACT(YEAR FROM Y.Odeme_Tarih) = :year
                GROUP BY month
            """)
            ytot = session.execute(sql_y, {"sube_id": sube_id, "year": year}).fetchall()
            yemek_total_values = get_monthly_values(ytot)
        except Exception:
            yemek_total_values = [Decimal('0.0')] * 12

        # Construct response similar structure
        response = {
            "processedExcelRows": [
                {"label": "Yemeksepeti Komisyon ve Lojistik Giderleri", "values": [float(v) for v in yemeksepeti_values], "total": float(sum(yemeksepeti_values)), "category": "lojistik"},
                {"label": "Trendyol Komisyon ve Lojistik Giderleri", "values": [float(v) for v in trendyol_values], "total": float(sum(trendyol_values)), "category": "lojistik"},
                {"label": "Getir Getirsin Komisyon ve Lojistik Giderleri", "values": [float(v) for v in getir_values], "total": float(sum(getir_values)), "category": "lojistik"},
                {"label": "Migros Hemen Komisyon ve Lojistik Giderleri", "values": [float(v) for v in migros_values], "total": float(sum(migros_values)), "category": "lojistik"},
                {"label": "Yemek Çeki (Toplam)", "values": [float(v) for v in yemek_total_values], "total": float(sum(yemek_total_values)), "category": "gelir"},
                {"label": "Nakit (Toplam)", "values": [float(v) for v in nakit_values], "total": float(sum(nakit_values)), "category": "gelir"},
            ],
            "processedDigerRows": [],
            "processedMoreRows": []
        }
        # Add other detailed rows: commissions, banka komisyonu, yemek cek komisyonu, demirbaş, diğer detay
        def month_from_rows(rows):
            vals = [Decimal('0.0')] * 12
            for m, t in rows:
                try:
                    mi = int(m)
                except Exception:
                    continue
                if 1 <= mi <= 12:
                    try:
                        vals[mi-1] = Decimal(t) if t else Decimal('0.0')
                    except Exception:
                        vals[mi-1] = Decimal('0.0')
            return vals

        # Satıştan İndirimler & Komisyonlar (from e_Fatura with keywords)
        try:
            rows = session.execute(text("""
                SELECT EXTRACT(MONTH FROM e.Fatura_Tarihi) as month, SUM(e.Tutar) as total
                FROM e_Fatura e
                WHERE e.Sube_ID = :sube_id AND EXTRACT(YEAR FROM e.Fatura_Tarihi) = :year
                  AND (e.Aciklama LIKE '%Komisyon%' OR e.Aciklama LIKE '%İndirim%')
                GROUP BY month
            """), {"sube_id": sube_id, "year": year}).fetchall()
            satistan_indirim_values = month_from_rows(rows)
        except Exception:
            satistan_indirim_values = [Decimal('0.0')] * 12

        # Banka Komisyonu (from Odeme descriptions)
        try:
            rows = session.execute(text("""
                SELECT EXTRACT(MONTH FROM o.Tarih) as month, SUM(o.Tutar) as total
                FROM Odeme o
                WHERE o.Sube_ID = :sube_id AND EXTRACT(YEAR FROM o.Tarih) = :year
                  AND (o.Aciklama LIKE '%Banka Komisyonu%' OR o.Aciklama LIKE '%Komisyon%')
                GROUP BY month
            """), {"sube_id": sube_id, "year": year}).fetchall()
            banka_komisyon_values = month_from_rows(rows)
        except Exception:
            banka_komisyon_values = [Decimal('0.0')] * 12

        # Yemek çekleri komisyonu (from Yemek_Ceki with keyword Komisyon)
        try:
            rows = session.execute(text("""
                SELECT EXTRACT(MONTH FROM Y.Odeme_Tarih) as month, SUM(Y.Tutar) as total
                FROM Yemek_Ceki Y
                WHERE Y.Sube_ID = :sube_id AND EXTRACT(YEAR FROM Y.Odeme_Tarih) = :year
                  AND (Y.Aciklama LIKE '%Komisyon%' OR Y.Aciklama LIKE '%Komisyonu%')
                GROUP BY month
            """), {"sube_id": sube_id, "year": year}).fetchall()
            yemek_cek_komisyon_values = month_from_rows(rows)
        except Exception:
            yemek_cek_komisyon_values = [Decimal('0.0')] * 12

        # Demirbaş giderleri (from Odeme descriptions or kategori)
        try:
            rows = session.execute(text("""
                SELECT EXTRACT(MONTH FROM o.Tarih) as month, SUM(o.Tutar) as total
                FROM Odeme o
                WHERE o.Sube_ID = :sube_id AND EXTRACT(YEAR FROM o.Tarih) = :year
                  AND (o.Aciklama LIKE '%Demirba%' OR o.Aciklama LIKE '%Demirbaş%')
                GROUP BY month
            """), {"sube_id": sube_id, "year": year}).fetchall()
            demirbas_values = month_from_rows(rows)
        except Exception:
            demirbas_values = [Decimal('0.0')] * 12

        # Diğer Detaylar: fallback to zero or try to aggregate unknown small categories
        try:
            rows = session.execute(text("""
                SELECT EXTRACT(MONTH FROM e.Fatura_Tarihi) as month, SUM(e.Tutar) as total
                FROM e_Fatura e
                WHERE e.Sube_ID = :sube_id AND EXTRACT(YEAR FROM e.Fatura_Tarihi) = :year
                  AND (e.Aciklama LIKE '%Diğer%' OR e.Aciklama LIKE '%Diger%')
                GROUP BY month
            """), {"sube_id": sube_id, "year": year}).fetchall()
            diger_values = month_from_rows(rows)
        except Exception:
            diger_values = [Decimal('0.0')] * 12

        # Append to processedDigerRows
        response['processedDigerRows'].extend([
            {"label": "Satıştan İndirimler & Komisyonlar", "values": [float(v) for v in satistan_indirim_values], "total": float(sum(satistan_indirim_values)), "category": "gider"},
            {"label": "Banka Komisyonu", "values": [float(v) for v in banka_komisyon_values], "total": float(sum(banka_komisyon_values)), "category": "gider"},
            {"label": "Yemek Çekleri Komisyonu", "values": [float(v) for v in yemek_cek_komisyon_values], "total": float(sum(yemek_cek_komisyon_values)), "category": "gider"},
            {"label": "Demirbaş Sayılmayan Giderler", "values": [float(v) for v in demirbas_values], "total": float(sum(demirbas_values)), "category": "diger"},
        ])

        # Append other rows
        response['processedMoreRows'].extend([
            {"label": "Diğer Detay Toplamı", "values": [float(v) for v in diger_values], "total": float(sum(diger_values)), "category": "diger"},
        ])

        # Add E-Ticaret Kredi Kart row (search e_Fatura for Kredi Kart keywords)
        try:
            rows = session.execute(text("""
                SELECT EXTRACT(MONTH FROM e.Fatura_Tarihi) as month, SUM(e.Tutar) as total
                FROM e_Fatura e
                WHERE e.Sube_ID = :sube_id AND EXTRACT(YEAR FROM e.Fatura_Tarihi) = :year
                  AND (e.Aciklama LIKE '%Kredi Kart%' OR e.Aciklama LIKE '%KrediKart%' OR e.Aciklama LIKE '%E-Ticaret%')
                GROUP BY month
            """), {"sube_id": sube_id, "year": year}).fetchall()
            eticaret_vals = month_from_rows(rows)
        except Exception:
            eticaret_vals = [Decimal('0.0')] * 12

        response['processedExcelRows'].insert(0, {"label": "E-Ticaret Kredi Kart", "values": [float(v) for v in eticaret_vals], "total": float(sum(eticaret_vals)), "category": "gelir"})

        # Add Yemek Çeki providers as individual rows (Multinet, Ticket, Sodexo, Metropal, Setcard)
        providers = ['Multinet','Ticket','Sodexo','Metropal','Setcard']
        for prov in providers:
            try:
                rows = session.execute(text("""
                    SELECT EXTRACT(MONTH FROM Y.Odeme_Tarih) as month, SUM(Y.Tutar) as total
                    FROM Yemek_Ceki Y
                    WHERE Y.Sube_ID = :sube_id AND EXTRACT(YEAR FROM Y.Odeme_Tarih) = :year
                      AND (Y.Referans LIKE :prov OR Y.Aciklama LIKE :prov)
                    GROUP BY month
                """), {"sube_id": sube_id, "year": year, "prov": f'%{prov}%'}).fetchall()
                prov_vals = month_from_rows(rows)
            except Exception:
                prov_vals = [Decimal('0.0')] * 12
            response['processedExcelRows'].append({"label": prov, "values": [float(v) for v in prov_vals], "total": float(sum(prov_vals)), "category": "gelir"})

        # Satışların Maliyeti breakdown: suppliers and product groups
        suppliers = ['Tavuk Dünyası','Cola','Ayran','Donuk Ekmek','Donuk Urun','Hal','Diğer yerli firmalar','Gunluk Eksik Gida']
        supplier_rows = []
        for sname in suppliers:
            try:
                rows = session.execute(text("""
                    SELECT EXTRACT(MONTH FROM o.Tarih) as month, SUM(o.Tutar) as total
                    FROM Odeme o
                    WHERE o.Sube_ID = :sube_id AND EXTRACT(YEAR FROM o.Tarih) = :year
                      AND (o.Aciklama LIKE :name OR o.Aciklama LIKE :short)
                    GROUP BY month
                """), {"sube_id": sube_id, "year": year, "name": f'%{sname}%', "short": f'%{sname.split()[0]}%'}).fetchall()
                vals = month_from_rows(rows)
            except Exception:
                vals = [Decimal('0.0')] * 12
            supplier_rows.append({"label": sname, "values": [float(v) for v in vals], "total": float(sum(vals)), "category": "maliyet"})

        # add a header for Satışların Maliyeti with total
        total_maliyet = sum(Decimal(str(r['total'])) for r in supplier_rows)
        response['processedDigerRows'].insert(0, {"label": "Satışların Maliyeti", "values": [float(v) for v in [Decimal('0.0')]*12], "total": float(total_maliyet), "category": "gider"})
        # append supplier subrows
        response['processedDigerRows'].extend(supplier_rows)

        return response
    finally:
        session.close()
