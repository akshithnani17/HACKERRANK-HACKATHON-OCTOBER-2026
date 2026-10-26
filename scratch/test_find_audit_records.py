import csv
import json
import os
import glob
import sqlite3
import re
import fitz

repo_root = r"c:\Users\Akash\Desktop\hacker rank oct hackathon"
dataset_dir = os.path.join(repo_root, "dataset")

identities = {r['user_id']: r for r in csv.DictReader(open(os.path.join(dataset_dir, 'user_identities.csv'), encoding='utf-8'))}
email_to_uid = {r['email'].lower(): r['user_id'] for r in identities.values()}
with open(os.path.join(dataset_dir, 'user_audit_log.csv'), encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['field_name'] == 'email':
            email_to_uid[r['old_value'].lower()] = r['user_id']
            email_to_uid[r['new_value'].lower()] = r['user_id']

user_audit_record = {}

# 1. Check JSON files
for jf in glob.glob(os.path.join(dataset_dir, 'evidence/records/*.json')):
    with open(jf, encoding='utf-8') as f:
        data = json.load(f)
    def search_audit(obj):
        if isinstance(obj, dict):
            res = obj.get('resource_id')
            if res and res.startswith('audit_record_'):
                sub = obj.get('subject_reference')
                if sub and sub in identities:
                    user_audit_record[sub] = res
                else:
                    for em, uid in email_to_uid.items():
                        if em in str(obj).lower():
                            user_audit_record[uid] = res
            for v in obj.values():
                search_audit(v)
        elif isinstance(obj, list):
            for item in obj:
                search_audit(item)
    search_audit(data)

# 2. Check SQL files
for sf in glob.glob(os.path.join(dataset_dir, 'evidence/databases/*.sql')):
    conn = sqlite3.connect(":memory:")
    with open(sf, encoding='utf-8') as f:
        conn.executescript(f.read())
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall()]
    for t in tables:
        cursor.execute(f"PRAGMA table_info({t});")
        cols = [c[1] for c in cursor.fetchall()]
        if 'resource_id' in cols and any(c in cols for c in ['subject_reference', 'user_id', 'customer_reference']):
            cursor.execute(f"SELECT * FROM {t};")
            for row in cursor.fetchall():
                row_dict = dict(zip(cols, row))
                res = row_dict.get('resource_id')
                if res and res.startswith('audit_record_'):
                    sub = row_dict.get('subject_reference') or row_dict.get('user_id') or row_dict.get('customer_reference')
                    if sub and sub in identities:
                        user_audit_record[sub] = res

# 3. Check TXT handover
txt_path = os.path.join(dataset_dir, 'evidence/records/customer_account_handover_20261001.txt')
if os.path.exists(txt_path):
    with open(txt_path, encoding='utf-8') as f:
        for line in f:
            if 'audit_record_' in line:
                m_res = re.search(r'\b(audit_record_\d+)\b', line)
                m_u = re.search(r'\b(user_\d+)\b', line)
                if m_res and m_u and m_u.group(1) in identities:
                    user_audit_record[m_u.group(1)] = m_res.group(1)

# 4. Check LOG files
for lf in glob.glob(os.path.join(dataset_dir, 'evidence/logs/*.log')):
    with open(lf, encoding='utf-8', errors='ignore') as f:
        for line in f:
            if 'audit_record_' in line:
                m_res = re.search(r'\b(audit_record_\d+)\b', line)
                m_u = re.search(r'\b(user_\d+)\b', line)
                if m_res and m_u and m_u.group(1) in identities:
                    user_audit_record[m_u.group(1)] = m_res.group(1)
                elif m_res:
                    for em, uid in email_to_uid.items():
                        if em in line.lower():
                            user_audit_record[uid] = m_res.group(1)
                            break

# 5. Check PDF files
for pf in glob.glob(os.path.join(dataset_dir, 'evidence/documents/*.pdf')):
    doc = fitz.open(pf)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    if 'audit_record_' in text:
        # e.g. Event reference audit_record_003 ... subject reference user_03
        pairs = re.findall(r'audit_record_\d+', text)
        u_pairs = re.findall(r'user_\d+', text)
        for r_id in pairs:
            for u_id in u_pairs:
                if u_id in identities:
                    user_audit_record[u_id] = r_id

# 6. Check system_activity for LINK_RESOURCE_IDENTITY with audit_record_
with open(os.path.join(dataset_dir, 'system_activity.csv'), encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['resource_id'].startswith('audit_record_'):
            m_u = re.search(r'\b(user_\d+)\b', r['details'])
            if m_u and m_u.group(1) in identities:
                user_audit_record[m_u.group(1)] = r['resource_id']

print(f"Total users with discovered audit_records: {len(user_audit_record)} / {len(identities)}")

# Check against sample outputs
samples = list(csv.DictReader(open(os.path.join(dataset_dir, 'sample_deletion_requests.csv'), encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open(os.path.join(dataset_dir, 'sample_output.csv'), encoding='utf-8'))}

missing = 0
correct = 0
for s in samples:
    cid = s['case_id']
    st, steps = outputs[cid]
    uid = email_to_uid[s['email'].lower()]
    exp_audit = None
    for step in steps:
        if step['resource_id'].startswith('audit_record_'):
            exp_audit = step['resource_id']
            break
    if exp_audit:
        found_audit = user_audit_record.get(uid)
        if found_audit == exp_audit:
            correct += 1
        else:
            missing += 1
            print(f"{cid} ({uid}): expected={exp_audit}, found={found_audit}")

print(f"Sample audit records checked: correct={correct}, mismatches={missing}")
