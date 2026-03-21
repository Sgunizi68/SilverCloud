"""Inspect legacy DB."""
import sqlite3
import os

paths = [
    r'GumusBulut/backend/app.db',
    r'GumusBulut/app.db',
]
for path in paths:
    if not os.path.exists(path):
        print(f"NOT FOUND: {path}")
        continue
    conn = sqlite3.connect(path)
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f"\n{path} tables: {tables[:10]}")
    
    # Look for invoice table
    for t in tables:
        try:
            cols = [r[1] for r in conn.execute(f"PRAGMA table_info({t})").fetchall()]
            if any(c.lower() in ('fatura_numarasi','fatura_no') for c in cols):
                print(f"  >> {t}: cols={cols}")
                # Sample
                samp = conn.execute(f"SELECT * FROM [{t}] WHERE {'fatura_no' if 'fatura_no' in [c.lower() for c in cols] else 'fatura_numarasi'} LIKE 'T022026000011717%' LIMIT 5").fetchall()
                for r in samp: print("   ", r)
        except Exception as e:
            pass
    conn.close()
