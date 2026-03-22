import pymysql
from app.main import create_main_app

# DB Config
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "F5tk3515"
DB_NAME = "SilverCloud"

def get_users():
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    c = conn.cursor()
    c.execute("SELECT Kullanici_ID, Kullanici_Adi, Email, Adi_Soyadi FROM kullanici")
    users = c.fetchall()
    conn.close()
    return users

users = get_users()
admin = next((u for u in users if u[1].lower() == 'admin'), None)
normal = next((u for u in users if u[1].lower() != 'admin'), None)

print("Admin:", admin)
print("Normal:", normal)

flask_app = create_main_app()
flask_app.config['TESTING'] = True

routes_to_test = [
    "/dashboard",
    "/stok-sayimi",
    "/roller",
    "/fatura-rapor",
    "/nakit-girisi"
]

def run_tests_for_user(user_data, user_type):
    print(f"\n--- Testing Routes for {user_type} ---")
    with flask_app.test_client() as client:
        if user_data:
            with client.session_transaction() as sess:
                sess['user_id'] = user_data[0]
                sess['username'] = user_data[1]
                sess['user_name'] = user_data[3]
                sess['user_email'] = user_data[2]
                sess.modified = True
        
        for r in routes_to_test:
            res = client.get(r, follow_redirects=False)
            print(f"GET {r} -> Status: {res.status_code}")

run_tests_for_user(None, "Anonymous")
if normal:
    run_tests_for_user(normal, f"Normal ({normal[1]})")
if admin:
    run_tests_for_user(admin, "Admin")
