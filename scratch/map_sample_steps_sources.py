import csv
import json
import os
import glob
import re

repo_root = r"c:\Users\Akash\Desktop\hacker rank oct hackathon"
dataset_dir = os.path.join(repo_root, "dataset")

samples = list(csv.DictReader(open(os.path.join(dataset_dir, 'sample_deletion_requests.csv'), encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open(os.path.join(dataset_dir, 'sample_output.csv'), encoding='utf-8'))}

identities = {r['user_id']: r for r in csv.DictReader(open(os.path.join(dataset_dir, 'user_identities.csv'), encoding='utf-8'))}
email_to_uid = {r['email'].lower(): r['user_id'] for r in identities.values()}
with open(os.path.join(dataset_dir, 'user_audit_log.csv'), encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['field_name'] == 'email':
            email_to_uid[r['old_value'].lower()] = r['user_id']
            email_to_uid[r['new_value'].lower()] = r['user_id']

# Load all activities
activities = list(csv.DictReader(open(os.path.join(dataset_dir, 'system_activity.csv'), encoding='utf-8')))

print(f"{'Case':<8} {'User':<9} {'Req Email':<28} {'Audit Ev':<12} {'Resources in Sample Output'}")
print("-" * 80)
for s in samples:
    cid = s['case_id']
    st, steps = outputs[cid]
    uid = email_to_uid.get(s['email'].lower(), "UNKNOWN")
    ev_ids = set(step['evidence_id'] for step in steps if step['evidence_id'])
    res_list = [(step['system_id'], step['resource_id'], step['operation']) for step in steps if step['phase'] in ['FINDING', 'VERIFICATION']]
    print(f"{cid:<8} {uid:<9} {s['email']:<28} {str(ev_ids):<12} {res_list}")
