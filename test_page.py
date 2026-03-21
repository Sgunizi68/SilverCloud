import requests

s = requests.Session()

# Login
r = s.post('http://localhost:5000/login', data={'username': 'admin', 'password': 'Adm123!'}, allow_redirects=True)
print(f"Login status: {r.status_code}, URL: {r.url}")

# Get the page
r2 = s.get('http://localhost:5000/diger-harcamalar')
print(f"Page status: {r2.status_code}")
print(f"Content length: {len(r2.text)}")

if r2.status_code != 200 or len(r2.text) < 500:
    print("FULL RESPONSE:")
    print(r2.text)
elif 'Internal Server Error' in r2.text or 'Traceback' in r2.text or 'Error' in r2.text[:500]:
    print("ERROR DETECTED:")
    print(r2.text[:3000])
else:
    print("First 500 chars:")
    print(r2.text[:500])
    print("...")
    # Check if table rows exist
    if 'tableBody' in r2.text:
        import re
        tbody_match = re.search(r'<tbody id="tableBody">(.*?)</tbody>', r2.text, re.DOTALL)
        if tbody_match:
            tbody = tbody_match.group(1)
            row_count = tbody.count('<tr')
            print(f"\nTable rows found: {row_count}")
            if row_count > 0:
                print("First 300 chars of tbody:")
                print(tbody[:300])
