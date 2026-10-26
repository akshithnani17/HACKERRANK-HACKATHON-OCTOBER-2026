import sqlite3
import os

db_dir = "dataset/evidence/databases"
sf = os.path.join(db_dir, "customer_accounts_failover_replica_20260902.sql")
conn = sqlite3.connect(":memory:")
with open(sf, encoding="utf-8") as f:
    conn.executescript(f.read())
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = c.fetchall()
print("Tables in evidence_54:", tables)
for t in tables:
    c.execute(f"PRAGMA table_info({t[0]});")
    print(t[0], c.fetchall())
    c.execute(f"SELECT * FROM {t[0]} WHERE email LIKE '%leila%' LIMIT 5;")
    print("Rows:", c.fetchall())
