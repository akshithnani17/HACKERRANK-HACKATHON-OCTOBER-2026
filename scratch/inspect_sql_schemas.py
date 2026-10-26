import os
import glob
import sqlite3

repo_root = r"c:\Users\Akash\Desktop\hacker rank oct hackathon"
dataset_dir = os.path.join(repo_root, "dataset")
evidence_dir = os.path.join(dataset_dir, "evidence")

sql_files = glob.glob(os.path.join(evidence_dir, "databases", "*.sql"))
print(f"Total SQL files: {len(sql_files)}")

by_prefix = {}
for sf in sql_files:
    base = os.path.basename(sf)
    prefix = base.split('_2026')[0]
    by_prefix.setdefault(prefix, []).append(sf)

for prefix, files in by_prefix.items():
    print(f"\nPrefix: {prefix} ({len(files)} files), e.g. {os.path.basename(files[0])}")
    # execute in in-memory sqlite
    conn = sqlite3.connect(":memory:")
    with open(files[0], encoding='utf-8') as f:
        sql = f.read()
    conn.executescript(sql)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall()]
    print("  Tables:", tables)
    for t in tables:
        cursor.execute(f"PRAGMA table_info({t});")
        cols = [c[1] for c in cursor.fetchall()]
        cursor.execute(f"SELECT COUNT(*) FROM {t};")
        cnt = cursor.fetchone()[0]
        print(f"    Table {t} ({cnt} rows): {cols}")
