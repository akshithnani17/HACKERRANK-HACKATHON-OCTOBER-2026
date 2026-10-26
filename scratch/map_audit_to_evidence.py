import csv
from datetime import datetime

with open('dataset/evidence_files.csv', encoding='utf-8') as f:
    evidence_files = list(csv.DictReader(f))

with open('dataset/deletion_requests.csv', encoding='utf-8') as f:
    requests = list(csv.DictReader(f))

# Collect all distinct audit_at values in deletion_requests.csv
audit_times = sorted(list(set(r['audit_at'] for r in requests)))
print(f"Total distinct audit_at timestamps in deletion_requests.csv: {len(audit_times)}")
for at in audit_times[:20]:
    print(" ", at)

# For each audit_at, which evidence files are captured at or shortly before audit_at?
print("\nMatching audit_at to evidence files:")
for at in audit_times:
    at_dt = datetime.fromisoformat(at.replace('Z', '+00:00'))
    candidates = []
    for ef in evidence_files:
        ef_dt = datetime.fromisoformat(ef['captured_at'].replace('Z', '+00:00'))
        if ef_dt <= at_dt:
            diff = (at_dt - ef_dt).total_seconds()
            candidates.append((diff, ef['file_id'], ef['captured_at'], ef['file_path']))
    candidates.sort(key=lambda x: x[0])
    # print top 2 candidates
    top2 = candidates[:2]
    req_count = sum(1 for r in requests if r['audit_at'] == at)
    print(f"audit_at={at} ({req_count} requests):")
    for diff, fid, cap, path in top2:
        print(f"   {fid} (diff={diff/3600:.1f}h) | {cap} | {path}")
