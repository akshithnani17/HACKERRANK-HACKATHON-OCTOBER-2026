import csv
import json
import os
import glob
import re

dataset_dir = r"c:\Users\Akash\Desktop\hacker rank oct hackathon\dataset"

samples = list(csv.DictReader(open(os.path.join(dataset_dir, 'sample_deletion_requests.csv'), encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open(os.path.join(dataset_dir, 'sample_output.csv'), encoding='utf-8'))}
ev_map = {r['file_id']: r for r in csv.DictReader(open(os.path.join(dataset_dir, 'evidence_files.csv'), encoding='utf-8'))}

identities = {r['user_id']: r for r in csv.DictReader(open(os.path.join(dataset_dir, 'user_identities.csv'), encoding='utf-8'))}
email_to_uid = {r['email'].lower(): r['user_id'] for r in identities.values()}
with open(os.path.join(dataset_dir, 'user_audit_log.csv'), encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['field_name'] == 'email':
            email_to_uid[r['old_value'].lower()] = r['user_id']
            email_to_uid[r['new_value'].lower()] = r['user_id']

# For each sample, find all evidence files that contain the user_id or the request email
for s in samples[10:25]:
    cid = s['case_id']
    st, steps = outputs[cid]
    uid = email_to_uid[s['email'].lower()]
    cited = sorted(list(set(step['evidence_id'] for step in steps if step['evidence_id'])))
    
    # check all evidence files
    matching_files = []
    for eid, ev in ev_map.items():
        if ev['captured_at'] > s['audit_at']:
            continue
        p = os.path.join(dataset_dir, ev['file_path'])
        if not os.path.exists(p) or p.endswith(('.png', '.pdf')):
            continue
        try:
            content = open(p, encoding='utf-8', errors='ignore').read()
            if uid in content or s['email'].lower() in content.lower():
                matching_files.append((eid, ev['captured_at'], os.path.basename(p)))
        except:
            pass
    
    print(f"{cid} ({uid}) cited={cited}")
    print(f"   Files containing user: {matching_files}")
