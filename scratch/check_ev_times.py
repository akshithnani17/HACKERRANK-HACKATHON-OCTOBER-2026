import csv
import json
import os

repo_root = r"c:\Users\Akash\Desktop\hacker rank oct hackathon"
dataset_dir = os.path.join(repo_root, "dataset")

samples = list(csv.DictReader(open(os.path.join(dataset_dir, 'sample_deletion_requests.csv'), encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open(os.path.join(dataset_dir, 'sample_output.csv'), encoding='utf-8'))}

evidence_files = list(csv.DictReader(open(os.path.join(dataset_dir, 'evidence_files.csv'), encoding='utf-8')))
ev_map = {e['file_id']: e for e in evidence_files}

print("Checking evidence captured_at vs case audit_at:")
for s in samples:
    cid = s['case_id']
    st, steps = outputs[cid]
    audit_at = s['audit_at']
    ev_ids = sorted(list(set(step['evidence_id'] for step in steps if step['evidence_id'])))
    ev_times = [(eid, ev_map[eid]['captured_at'], os.path.basename(ev_map[eid]['file_path'])) for eid in ev_ids]
    print(f"{cid} | audit_at: {audit_at} | evs: {ev_times}")
