import csv

files = list(csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8')))
files.sort(key=lambda x: x['captured_at'])
print(f"{'file_id':<12} {'captured_at':<22} {'origin':<35} {'file_path'}")
print("-" * 100)
for f in files:
    print(f"{f['file_id']:<12} {f['captured_at']:<22} {f['origin']:<35} {f['file_path']}")
