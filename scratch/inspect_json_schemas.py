import os
import json
import sqlite3
import glob

repo_root = r"c:\Users\Akash\Desktop\hacker rank oct hackathon"
dataset_dir = os.path.join(repo_root, "dataset")
evidence_dir = os.path.join(dataset_dir, "evidence")

# 1. Check all JSON files in records/
print("--- JSON files in records/ ---")
json_files = glob.glob(os.path.join(evidence_dir, "records", "*.json"))
print(f"Total JSON files: {len(json_files)}")
# sample a few different names:
by_prefix = {}
for jf in json_files:
    base = os.path.basename(jf)
    prefix = base.split('_2026')[0]
    by_prefix.setdefault(prefix, []).append(jf)

for prefix, files in by_prefix.items():
    print(f"Prefix: {prefix} ({len(files)} files), e.g. {os.path.basename(files[0])}")
    with open(files[0], encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, dict):
            print("  Keys:", list(data.keys()))
        elif isinstance(data, list):
            print("  List of length", len(data), "item keys:", list(data[0].keys()) if data else "empty")

