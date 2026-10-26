import csv
import json
import os
import glob
import re
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

activities = list(csv.DictReader(open(os.path.join(dataset_dir, 'system_activity.csv'), encoding='utf-8')))
worker_acts = [a for a in activities if a['source_system'] == 'deletion_worker']

# Check how accurately we identify the exact set of resources for each sample case!
for s in samples:
    cid = s['case_id']
    st, steps = outputs[cid]
    uid = email_to_uid[s['email'].lower()]
    expected_resources = set((step['system_id'], step['resource_id']) for step in steps)
    
    rep_dt = datetime.fromisoformat(s['reported_at'].replace('Z', '+00:00'))
    
    # 1. Nearby worker activities
    nearby_res = set()
    for a in worker_acts:
        a_dt = datetime.fromisoformat(a['event_time'].replace('Z', '+00:00'))
        if -90 <= (a_dt - rep_dt).total_seconds() / 60.0 <= 90:
            nearby_res.add((a['target_system'], a['resource_id']))
            
    print(f"{cid} ({uid}) expected {len(expected_resources)} resources, nearby worker acts: {len(nearby_res)}")
    # compare
    missing = expected_resources - nearby_res
    extra = nearby_res - expected_resources
    if missing:
        print(f"   Missing from nearby acts: {missing}")
