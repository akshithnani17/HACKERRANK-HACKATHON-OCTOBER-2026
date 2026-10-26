import csv
import json
import os
import glob
import re
import sqlite3
from datetime import datetime

dataset_dir = r"c:\Users\Akash\Desktop\hacker rank oct hackathon\dataset"

samples = list(csv.DictReader(open(os.path.join(dataset_dir, 'sample_deletion_requests.csv'), encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open(os.path.join(dataset_dir, 'sample_output.csv'), encoding='utf-8'))}

identities = {r['user_id']: r for r in csv.DictReader(open(os.path.join(dataset_dir, 'user_identities.csv'), encoding='utf-8'))}
email_to_uid = {r['email'].lower(): r['user_id'] for r in identities.values()}
uid_to_emails = {uid: {identities[uid]['email'].lower()} for uid in identities}

with open(os.path.join(dataset_dir, 'user_audit_log.csv'), encoding='utf-8') as f:
    for r in csv.DictReader(f):
        uid = r['user_id']
        if r['field_name'] == 'email':
            email_to_uid[r['old_value'].lower()] = uid
            email_to_uid[r['new_value'].lower()] = uid
            uid_to_emails.setdefault(uid, set()).add(r['old_value'].lower())
            uid_to_emails.setdefault(uid, set()).add(r['new_value'].lower())

# Let's see: for each sample case, which evidence file is the PRIMARY audit evidence?
# We saw earlier that the primary audit evidence is the closest evidence file at or before audit_at
# that contains data for that user.
ev_manifest = list(csv.DictReader(open(os.path.join(dataset_dir, 'evidence_files.csv'), encoding='utf-8')))

# Check if every sample's cited evidence is in fact the latest evidence file at or before audit_at containing the user
matched_ev = 0
for s in samples:
    cid = s['case_id']
    st, steps = outputs[cid]
    uid = email_to_uid[s['email'].lower()]
    expected_eids = set(step['evidence_id'] for step in steps if step['evidence_id'])
    audit_dt = datetime.fromisoformat(s['audit_at'].replace('Z', '+00:00'))
    
    # candidate files <= audit_dt
    user_files = []
    for ev in ev_manifest:
        ev_dt = datetime.fromisoformat(ev['captured_at'].replace('Z', '+00:00'))
        if ev_dt <= audit_dt:
            # check if file contains user
            p = os.path.join(dataset_dir, ev['file_path'])
            if not os.path.exists(p) or p.endswith(('.png', '.pdf')):
                continue
            try:
                text = open(p, encoding='utf-8', errors='ignore').read()
                if uid in text or any(em in text.lower() for em in uid_to_emails[uid]):
                    user_files.append((ev_dt, ev['file_id'], os.path.basename(p)))
            except:
                pass
    user_files.sort(reverse=True)
    latest_eid = user_files[0][1] if user_files else None
    if latest_eid in expected_eids or (not expected_eids and not user_files):
        matched_ev += 1
    else:
        print(f"{cid} ({uid}) expected {expected_eids}, found latest: {latest_eid}")

print(f"Sample cases evidence file match: {matched_ev} / {len(samples)}")
