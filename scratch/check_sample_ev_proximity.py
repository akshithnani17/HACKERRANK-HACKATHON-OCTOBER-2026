import csv
import json
from datetime import datetime

samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}
evidence_files = {r['file_id']: r for r in csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8'))}

for s in samples:
    cid = s['case_id']
    st, steps = outputs[cid]
    cited_eids = sorted(list(set(step['evidence_id'] for step in steps if step['evidence_id'])))
    audit_dt = datetime.fromisoformat(s['audit_at'].replace('Z', '+00:00'))
    
    # candidate evidence files <= audit_dt
    candidates = []
    for eid, ev in evidence_files.items():
        ev_dt = datetime.fromisoformat(ev['captured_at'].replace('Z', '+00:00'))
        if ev_dt <= audit_dt:
            diff_h = (audit_dt - ev_dt).total_seconds() / 3600.0
            candidates.append((diff_h, eid, ev['file_path']))
    candidates.sort()
    
    print(f"{cid} (audit={s['audit_at']}): cited={cited_eids}")
    print(f"   Top 3 closest evidence files:")
    for diff_h, eid, p in candidates[:3]:
        print(f"      {eid} ({diff_h:.1f}h ago): {p}")
