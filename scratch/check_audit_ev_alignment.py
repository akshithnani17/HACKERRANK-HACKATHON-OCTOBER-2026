import csv
from datetime import datetime

requests = list(csv.DictReader(open('dataset/deletion_requests.csv', encoding='utf-8')))
evidence_files = list(csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8')))

matches = 0
for r in requests:
    audit_dt = datetime.fromisoformat(r['audit_at'].replace('Z', '+00:00'))
    closest_ev = None
    min_diff = float('inf')
    for ev in evidence_files:
        ev_dt = datetime.fromisoformat(ev['captured_at'].replace('Z', '+00:00'))
        if ev_dt <= audit_dt:
            diff = (audit_dt - ev_dt).total_seconds()
            if diff < min_diff:
                min_diff = diff
                closest_ev = ev
    if closest_ev and min_diff <= 86400 * 2: # within 2 days
        matches += 1

print(f"Total requests: {len(requests)}, matched evidence within 2 days: {matches}")
