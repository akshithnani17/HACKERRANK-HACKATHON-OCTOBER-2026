import csv
import json
import os
import glob
from datetime import datetime

repo_root = r"c:\Users\Akash\Desktop\hacker rank oct hackathon"
dataset_dir = os.path.join(repo_root, "dataset")

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

# Load ev92 to test
with open(os.path.join(dataset_dir, 'evidence/records/service_resource_export_20260915_114455.json'), encoding='utf-8') as f:
    ev92 = json.load(f)

# Build a mapping of resource_id -> email / user_id from evidence
res_to_user = {}
se = ev92['service_exports']
for q in se.get('search_service', {}).get('index_queries', []):
    if q.get('query'): res_to_user[q['resource_id']] = q['query'].lower()
for ap in se.get('analytics_platform', {}).get('profiles', []):
    if ap.get('email'): res_to_user[ap['resource_id']] = ap['email'].lower()
    if ap.get('customer_reference'): res_to_user[ap['resource_id']] = ap['customer_reference']
for t in se.get('support_platform', {}).get('tickets', []):
    if t.get('requester_email'): res_to_user[t['resource_id']] = t['requester_email'].lower()
    if t.get('customer_reference'): res_to_user[t['resource_id']] = t['customer_reference']
for c in se.get('integration_service', {}).get('connectors', []):
    if c.get('customer_email'): res_to_user[c['resource_id']] = c['customer_email'].lower()
    if c.get('customer_reference'): res_to_user[c['resource_id']] = c['customer_reference']
for b in se.get('backup_service', {}).get('restore_entries', []):
    if b.get('customer_email'): res_to_user[b['resource_id']] = b['customer_email'].lower()
    if b.get('customer_reference'): res_to_user[b['resource_id']] = b['customer_reference']

# Check cases 26, 27, 28, 29, 30
for cid in ['case_26', 'case_27', 'case_28', 'case_29', 'case_30']:
    s = [x for x in samples if x['case_id'] == cid][0]
    uid = email_to_uid[s['email'].lower()]
    st, steps = outputs[cid]
    exp_acc = None
    for stp in steps:
        if stp['system_id'] == 'account_service':
            exp_acc = stp['resource_id']
            break
            
    # Find all worker acts that mention any resource belonging to this user
    user_res_known = set()
    for res, user_id_or_em in res_to_user.items():
        if user_id_or_em in uid_to_emails[uid] or user_id_or_em == uid:
            user_res_known.add(res)
            
    print(f"{cid} ({uid}) exp_acc={exp_acc}, known_aux_res={user_res_known}")
