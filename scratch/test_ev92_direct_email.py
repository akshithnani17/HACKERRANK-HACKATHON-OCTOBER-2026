import csv
import json
import os

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

with open(os.path.join(dataset_dir, 'evidence/records/service_resource_export_20260915_114455.json'), encoding='utf-8') as f:
    ev92 = json.load(f)

for cid in ['case_29', 'case_30']:
    s = [x for x in samples if x['case_id'] == cid][0]
    uid = email_to_uid[s['email'].lower()]
    user_emails = uid_to_emails[uid]
    st, steps = outputs[cid]
    exp_res = set(st['resource_id'] for st in steps)
    print(f"\n{cid} ({uid}) Expected resources: {exp_res}")
    
    found_res = set()
    # Check ev92
    for q in ev92['service_exports']['search_service']['index_queries']:
        if q.get('query') and q.get('query').lower() in user_emails:
            found_res.add(q.get('resource_id'))
    for ap in ev92['service_exports']['analytics_platform']['profiles']:
        if ap.get('email') and ap.get('email').lower() in user_emails:
            found_res.add(ap.get('resource_id'))
    for t in ev92['service_exports']['support_platform']['tickets']:
        if t.get('requester_email') and t.get('requester_email').lower() in user_emails:
            found_res.add(t.get('resource_id'))
    for c in ev92['service_exports']['integration_service']['connectors']:
        if c.get('customer_email') and c.get('customer_email').lower() in user_emails:
            found_res.add(c.get('resource_id'))
    for b in ev92['service_exports']['backup_service']['restore_entries']:
        if b.get('customer_email') and b.get('customer_email').lower() in user_emails:
            found_res.add(b.get('resource_id'))
            
    print(f"  Found directly via email in ev92: {found_res}")
