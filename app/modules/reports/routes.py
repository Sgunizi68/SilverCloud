from flask import jsonify, request
from . import reports_bp
from .queries import invoicing_summary, inventory_valuation, hr_summary
from .queries import dashboard_report
from .queries import get_bayi_karlilik_raporu


@reports_bp.route('/api/v1/reports/invoicing-summary', methods=['GET'])
def route_invoicing_summary():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    data = invoicing_summary(start_date=start_date, end_date=end_date)
    return jsonify(data), 200


@reports_bp.route('/api/v1/reports/inventory-valuation', methods=['GET'])
def route_inventory_valuation():
    data = inventory_valuation()
    return jsonify(data), 200


@reports_bp.route('/api/v1/reports/hr-summary', methods=['GET'])
def route_hr_summary():
    data = hr_summary()
    return jsonify(data), 200


@reports_bp.route('/api/v1/rapor/dashboard', methods=['GET'])
def route_dashboard_report():
    try:
        from flask import session
        from app.common.database import get_db_session
        from app.modules.auth import queries as auth_queries

        donem = request.args.get('donem', type=int)
        sube_id = request.args.get('sube_id', type=int)
        if not donem or not sube_id:
            return jsonify({'error': 'donem and sube_id required'}), 400

        # Determine if user can see Gizli (hidden) categories
        show_gizli = True  # Default: admins and anonymous see all
        user_id = session.get('user_id')
        if user_id:
            db = get_db_session()
            try:
                user = auth_queries.get_kullanici_by_id(db, user_id)
                is_admin = False
                if user and user.Kullanici_Adi and user.Kullanici_Adi.lower() == 'admin':
                    is_admin = True
                else:
                    roles = auth_queries.get_user_roles(db, user_id)
                    is_admin = 'admin' in [r.lower() for r in roles]

                if not is_admin:
                    # Check specific Gizli Kategori permission
                    show_gizli = auth_queries.has_permission(db, user_id, "Gizli Kategori Veri Erişimi")
            finally:
                db.close()

        data = dashboard_report(donem=donem, sube_id=sube_id, show_gizli=show_gizli)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@reports_bp.route('/api/v1/rapor/bayi-karlilik', methods=['GET'])
def route_bayi_karlilik():
    try:
        year = request.args.get('year', type=int)
        sube_id = request.args.get('sube_id', type=int)
        if not year or not sube_id:
            return jsonify({'error': 'year and sube_id required'}), 400
        data = get_bayi_karlilik_raporu(year=year, sube_id=sube_id)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
