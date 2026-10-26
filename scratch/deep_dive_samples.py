import csv
import json
import os
import glob
import sqlite3

repo_root = r"c:\Users\Akash\Desktop\hacker rank oct hackathon"
dataset_dir = os.path.join(repo_root, "dataset")

# Load samples and outputs
samples = list(csv.DictReader(open(os.path.join(dataset_dir, 'sample_deletion_requests.csv'), encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open(os.path.join(dataset_dir, 'sample_output.csv'), encoding='utf-8'))}

# Load identities & audits
identities = {r['user_id']: r for r in csv.DictReader(open(os.path.join(dataset_dir, 'user_identities.csv'), encoding='utf-8'))}
email_to_uid = {r['email'].lower(): r['user_id'] for r in identities.values()}
with open(os.path.join(dataset_dir, 'user_audit_log.csv'), encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['field_name'] == 'email':
            email_to_uid[r['old_value'].lower()] = r['user_id']
            email_to_uid[r['new_value'].lower()] = r['user_id']

# Load rules
rules = list(csv.DictReader(open(os.path.join(dataset_dir, 'deletion_rules.csv'), encoding='utf-8')))

print("Analyzing sample cases...")
for s in samples:
    cid = s['case_id']
    st, steps = outputs[cid]
    uid = email_to_uid[s['email'].lower()]
    print(f"\n==========================================")
    print(f"{cid} | uid: {uid} | email: {s['email']} | status: {st}")
    print(f"req_at: {s['requested_at']} | rep_at: {s['reported_at']} | aud_at: {s['audit_at']}")
    print(f"request_text: {s['request_text']}")
    print(f"Steps count: {len(steps)}")
    for step in steps:
        print(f"  [{step['step_no']}] {step['phase']} | {step['system_id']} | {step['resource_id']} | {step['operation']} | {step['state']} | ev='{step['evidence_id']}'")
