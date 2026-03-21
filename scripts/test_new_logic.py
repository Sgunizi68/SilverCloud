import os
import sys
import io
from datetime import datetime
from decimal import Decimal

# Set path to include current directory
sys.path.append(os.getcwd())
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.common.database import get_db_session
from sqlalchemy import text
from run import app as flask_app

def calculate_firm_balance(firma_unvani, report_date_str, sube_id=1):
    with flask_app.app_context():
        db = get_db_session()
        try:
            report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
            
            # 1. Get Cari_ID and other info
            cari = db.execute(text("SELECT * FROM Cari WHERE Alici_Unvani = :unvan"), {"unvan": firma_unvani}).fetchone()
            if not cari:
                print(f"Firm {firma_unvani} not found in Cari table.")
                return
            
            cari_id = cari.Cari_ID
            referans_id = cari.Referans_ID
            
            # 2. Get latest mutabakat before or on report_date
            mutabakat = db.execute(text("""
                SELECT * FROM Mutabakat 
                WHERE Cari_ID = :cari_id AND Mutabakat_Tarihi <= :report_date
                ORDER BY Mutabakat_Tarihi DESC LIMIT 1
            """), {"cari_id": cari_id, "report_date": report_date}).fetchone()
            
            if mutabakat:
                base_balance = Decimal(str(mutabakat.Tutar))
                start_date = mutabakat.Mutabakat_Tarihi
                print(f"Mutabakat found at {start_date}: {base_balance}")
            else:
                base_balance = Decimal('0.0')
                start_date = datetime.strptime('1970-01-01', '%Y-%m-%d').date()
                print(f"No mutabakat found. Start date: {start_date}")

            # 3. Get Invoices since start_date
            invoices = db.execute(text("""
                SELECT SUM(Tutar) as total FROM e_Fatura 
                WHERE Alici_Unvani = :unvan AND Sube_ID = :sube_id 
                AND Fatura_Tarihi > :start_date AND Fatura_Tarihi <= :report_date
                AND (Giden_Fatura = 0 OR Giden_Fatura IS NULL)
            """), {"unvan": firma_unvani, "sube_id": sube_id, "start_date": start_date, "report_date": report_date}).fetchone()
            
            invoice_total = Decimal(str(invoices.total or 0))
            print(f"Invoices since {start_date}: {invoice_total}")

            # 4. Get Return Invoices since start_date
            returns = db.execute(text("""
                SELECT SUM(Tutar) as total FROM e_Fatura 
                WHERE Alici_Unvani = :unvan AND Sube_ID = :sube_id 
                AND Fatura_Tarihi > :start_date AND Fatura_Tarihi <= :report_date
                AND Giden_Fatura = 1
            """), {"unvan": firma_unvani, "sube_id": sube_id, "start_date": start_date, "report_date": report_date}).fetchone()
            
            return_total = Decimal(str(returns.total or 0))
            print(f"Returns since {start_date}: {return_total}")

            # 5. Get Payments since start_date
            # The join logic from legacy:
            payment_total = Decimal('0.0')
            if referans_id:
                payments = db.execute(text("""
                    SELECT SUM(O.Tutar) as total
                    FROM Odeme AS O
                    INNER JOIN Odeme_Referans AS ORF ON O.Kategori_ID = ORF.Kategori_ID
                    WHERE ORF.Referans_ID = :ref_id
                      AND O.Aciklama LIKE CONCAT('%', ORF.Referans_Metin, '%')
                      AND O.Sube_ID = :sube_id
                      AND O.Tarih > :start_date AND O.Tarih <= :report_date
                """), {"ref_id": referans_id, "sube_id": sube_id, "start_date": start_date, "report_date": report_date}).fetchone()
                payment_total = Decimal(str(payments.total or 0))
            
            print(f"Payments since {start_date}: {payment_total}")

            # Final Balance
            final_balance = base_balance + invoice_total - return_total - payment_total
            print(f"\nFinal Balance for {firma_unvani} at {report_date_str}: {final_balance}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()

if __name__ == "__main__":
    calculate_firm_balance("Pepsi Cola Servis ve Dağıtım Ltd. Şti.", "2026-03-15")
    print("-" * 30)
    calculate_firm_balance("FASDAT GIDA DAĞITIM SANAYİ VE TİCARET ANONİM ŞİRKETİ", "2026-03-15")
