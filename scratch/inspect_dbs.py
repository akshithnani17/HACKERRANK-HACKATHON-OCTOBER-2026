import glob
import sqlite3
import os

db_dir = "dataset/evidence/databases"
for sf in sorted(glob.glob(os.path.join(db_dir, "*.sql"))):
    conn = sqlite3.connect(":memory:")
    with open(sf, encoding="utf-8") as f:
        conn.executescript(f.read())
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in c.fetchall()]
    table_info = {}
    for t in tables:
        c.execute(f"PRAGMA table_info({t});")
        cols = [col[1] for col in c.fetchall()]
        table_info[t] = cols
    print(os.path.basename(sf), table_info)
