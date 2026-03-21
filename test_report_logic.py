from app.main import create_main_app
from app.common.database import get_db_session
from app.modules.reports.queries import get_ozet_kontrol_raporu
import sys

def test():
    app = create_main_app()
    with app.app_context():
        try:
            db_session = get_db_session()
            sube_id = 1
            donem = 2603  # March 2026 as seen in user error
            print(f"Testing get_ozet_kontrol_raporu(sube_id={sube_id}, donem={donem})...")
            data = get_ozet_kontrol_raporu(db_session, sube_id, donem)
            print("SUCCESS! Report data fetched:")
            print(data)
            db_session.close()
        except Exception as e:
            print("FAILED! Error encountered:")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    test()
