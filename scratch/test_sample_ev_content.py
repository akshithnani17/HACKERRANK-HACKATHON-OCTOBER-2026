import csv
import json
import os
import glob
import re

repo_root = r"c:\Users\Akash\Desktop\hacker rank oct hackathon"
dataset_dir = os.path.join(repo_root, "dataset")

# Load samples & outputs
samples = list(csv.DictReader(open(os.path.join(dataset_dir, 'sample_deletion_requests.csv'), encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open(os.path.join(dataset_dir, 'sample_output.csv'), encoding='utf-8'))}

# Load identities & audits
identities = {r['user_id']: r for r in csv.DictReader(open(os.path.join(dataset_dir, 'user_identities.csv'), encoding='utf-8'))}
email_to_uid = {r['email'].lower(): r['user_id'] for r in identities.values()}

user_all_emails = {}
for uid, u in identities.items():
    user_all_emails[uid] = {u['email'].lower()}

with open(os.path.join(dataset_dir, 'user_audit_log.csv'), encoding='utf-8') as f:
    for r in csv.DictReader(f):
        uid = r['user_id']
        if r['field_name'] == 'email':
            email_to_uid[r['old_value'].lower()] = uid
            email_to_uid[r['new_value'].lower()] = uid
            user_all_emails.setdefault(uid, set()).add(r['old_value'].lower())
            user_all_emails.setdefault(uid, set()).add(r['new_value'].lower())

evidence_manifest = list(csv.DictReader(open(os.path.join(dataset_dir, 'evidence_files.csv'), encoding='utf-8')))
ev_file_map = {e['file_id']: e for e in evidence_manifest}

print("Testing evidence lookup on all 32 sample cases:")
for s in samples:
    cid = s['case_id']
    st, steps = outputs[cid]
    uid = email_to_uid[s['email'].lower()]
    emails = user_all_emails[uid]
    
    cited_evs = set(step['evidence_id'] for step in steps if step['evidence_id'])
    step_res = set(step['resource_id'] for step in steps)
    
    # Read cited evidence file contents and look for occurrences of emails, uid, or step_res
    print(f"\n{cid} ({uid}, {s['email']}, {st}) cited_evs={cited_evs}:")
    print(f"  Expected resources: {step_res}")
    for eid in cited_evs:
        ef = ev_file_map[eid]
        fpath = os.path.join(dataset_dir, ef['file_path'])
        ext = os.path.splitext(fpath)[1].lower()
        if ext in ['.log', '.json', '.sql', '.txt']:
            with open(fpath, encoding='utf-8', errors='ignore') as f:
                content = f.read()
            # check which expected resources are in content
            in_content = [r for r in step_res if r in content]
            not_in_content = [r for r in step_res if r not in content]
            print(f"  In {eid} ({os.path.basename(fpath)}): found={in_content}, not_found={not_in_content}")
