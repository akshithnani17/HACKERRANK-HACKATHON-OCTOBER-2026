import csv
import json
import os
import glob
import re

repo_root = r"c:\Users\Akash\Desktop\hacker rank oct hackathon"
dataset_dir = os.path.join(repo_root, "dataset")

# 1. Load users & audits
identities = {r['user_id']: r for r in csv.DictReader(open(os.path.join(dataset_dir, 'user_identities.csv'), encoding='utf-8'))}
email_to_uid = {r['email'].lower(): r['user_id'] for r in identities.values()}

user_all_emails = {}
user_all_phones = {}
for uid, u in identities.items():
    user_all_emails[uid] = {u['email'].lower()}
    user_all_phones[uid] = {u['phone']}

with open(os.path.join(dataset_dir, 'user_audit_log.csv'), encoding='utf-8') as f:
    for r in csv.DictReader(f):
        uid = r['user_id']
        if r['field_name'] == 'email':
            email_to_uid[r['old_value'].lower()] = uid
            email_to_uid[r['new_value'].lower()] = uid
            user_all_emails.setdefault(uid, set()).add(r['old_value'].lower())
            user_all_emails.setdefault(uid, set()).add(r['new_value'].lower())
        elif r['field_name'] == 'phone':
            user_all_phones.setdefault(uid, set()).add(r['old_value'])
            user_all_phones.setdefault(uid, set()).add(r['new_value'])

# 2. Load sample outputs
samples = list(csv.DictReader(open(os.path.join(dataset_dir, 'sample_deletion_requests.csv'), encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open(os.path.join(dataset_dir, 'sample_output.csv'), encoding='utf-8'))}

# 3. For each sample, let's see how each resource links to the user
print("=== HOW ARE RESOURCES LINKED TO USERS IN SAMPLE OUTPUTS? ===")

# Pre-read evidence files text for quick grep
evidence_manifest = list(csv.DictReader(open(os.path.join(dataset_dir, 'evidence_files.csv'), encoding='utf-8')))
ev_file_map = {e['file_id']: e for e in evidence_manifest}

evidence_texts = {}
for e in evidence_manifest:
    path = os.path.join(dataset_dir, e['file_path'])
    if not os.path.exists(path):
        continue
    ext = os.path.splitext(path)[1].lower()
    if ext in ['.json', '.sql', '.txt', '.log']:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            evidence_texts[e['file_id']] = f.read()

for s in samples:
    cid = s['case_id']
    st, steps = outputs[cid]
    uid = email_to_uid[s['email'].lower()]
    emails = user_all_emails[uid]
    phones = user_all_phones[uid]
    
    print(f"\n--- {cid} ({uid}, {s['email']}) -> {st} ---")
    for step in steps:
        res = step['resource_id']
        sys_id = step['system_id']
        ev_id = step.get('evidence_id')
        
        # Where does `res` link to uid or emails or phones in evidence_texts?
        linked_in_ev = []
        for eid, text in evidence_texts.items():
            if res in text:
                linked_in_ev.append(eid)
        
        # Check if uid or email is also near res in the cited evidence
        cited_text = evidence_texts.get(ev_id, "")
        user_in_cited = any(em in cited_text for em in emails) or uid in cited_text
        
        print(f"  {step['phase']:12} | {sys_id:18} | {res:16} | {step['operation']:24} | cited_ev={ev_id} | res_in_evs={linked_in_ev}")
