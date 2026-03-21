import os
import sys
import json
from datetime import datetime

# Set path to include current directory
sys.path.append(os.getcwd())

from app.common.database import get_db_session
from sqlalchemy import text
from run import app as flask_app

def solve():
    with flask_app.app_context():
        db = get_db_session()
        try:
            # Check Mutabakat
            mutabakat_rows = db.execute(text("SELECT * FROM Mutabakat")).fetchall()
            mut_data = [dict(row._mapping) for row in mutabakat_rows]
            
            # Check Cari
            cari_rows = db.execute(text("SELECT * FROM Cari")).fetchall()
            cari_data = [dict(row._mapping) for row in cari_rows]
            
            # Check e_Fatura counts for Giden_Fatura
            fatura_stats = db.execute(text("SELECT Giden_Fatura, COUNT(*) as cnt FROM e_Fatura GROUP BY Giden_Fatura")).fetchall()
            f_stats = [dict(row._mapping) for row in fatura_stats]
            
            output = {
                "mutabakat": mut_data,
                "cari": cari_data,
                "fatura_stats": f_stats
            }
            
            # Convert datetime to string for JSON
            def serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return str(obj)

            with open("tmp_db_analysis.json", "w", encoding="utf-8") as f:
                json.dump(output, f, default=serializer, indent=2, ensure_ascii=False)
                
            print("Analysis saved to tmp_db_analysis.json")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()

if __name__ == "__main__":
    solve()
