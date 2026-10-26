import csv
import json
import os
import glob
import sqlite3
import re

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
source_of_audit = {}

# A. SQL files: check record_json column
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
        if 'record_json' in cols:
            cursor.execute(f"SELECT record_json FROM {t};")
            for (rj,) in cursor.fetchall():
                if rj and 'audit_record_' in rj:
                    try:
                        data = json.loads(rj)
                        res = data.get('resource_id')
                        sub = data.get('subject_reference')
                        if res and sub and sub in identities:
                            user_audit_record[sub] = res
                            source_of_audit[sub] = f"SQL {os.path.basename(sf)}:{t}"
                    except:
                        pass
        elif 'resource_id' in cols and any(c in cols for c in ['subject_reference', 'user_id', 'customer_reference']):
            cursor.execute(f"SELECT * FROM {t};")
            for row in cursor.fetchall():
                row_dict = dict(zip(cols, row))
                res = row_dict.get('resource_id')
                if res and res.startswith('audit_record_'):
                    sub = row_dict.get('subject_reference') or row_dict.get('user_id') or row_dict.get('customer_reference')
                    if sub and sub in identities:
                        user_audit_record[sub] = res
                        source_of_audit[sub] = f"SQL {os.path.basename(sf)}:{t}"

# B. JSON files
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
                    source_of_audit[sub] = f"JSON {os.path.basename(jf)}"
            for v in obj.values():
                search_audit(v)
        elif isinstance(obj, list):
            for item in obj:
                search_audit(item)
    search_audit(data)

# C. TXT files
txt_path = os.path.join(dataset_dir, 'evidence/records/customer_account_handover_20261001.txt')
if os.path.exists(txt_path):
    with open(txt_path, encoding='utf-8') as f:
        for line in f:
            if 'audit_record_' in line:
                m_res = re.search(r'\b(audit_record_\d+)\b', line)
                m_u = re.search(r'\b(user_\d+)\b', line)
                if m_res and m_u and m_u.group(1) in identities:
                    user_audit_record[m_u.group(1)] = m_res.group(1)
                    source_of_audit[m_u.group(1)] = "TXT handover"

# D. LOG files
for lf in glob.glob(os.path.join(dataset_dir, 'evidence/logs/*.log')):
    trace_to_user = {}
    with open(lf, encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    for line in lines:
        m_tr = re.search(r'trace_id[:=]([a-zA-Z0-9_\-]+)', line)
        if m_tr:
            tr = m_tr.group(1)
            m_u = re.search(r'\b(user_\d+)\b', line)
            if m_u and m_u.group(1) in identities:
                trace_to_user[tr] = m_u.group(1)
            else:
                for em, uid in email_to_uid.items():
                    if em in line.lower():
                        trace_to_user[tr] = uid
                        break
    for line in lines:
        m_tr = re.search(r'trace_id[:=]([a-zA-Z0-9_\-]+)', line)
        m_res = re.search(r'\b(audit_record_\d+)\b', line)
        if m_res:
            res = m_res.group(1)
            found_u = None
            if m_tr and m_tr.group(1) in trace_to_user:
                found_u = trace_to_user[m_tr.group(1)]
            else:
                m_u = re.search(r'\b(user_\d+)\b', line)
                if m_u and m_u.group(1) in identities:
                    found_u = m_u.group(1)
            if found_u:
                user_audit_record[found_u] = res
                source_of_audit[found_u] = f"LOG {os.path.basename(lf)}"

samples = list(csv.DictReader(open(os.path.join(dataset_dir, 'sample_deletion_requests.csv'), encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open(os.path.join(dataset_dir, 'sample_output.csv'), encoding='utf-8'))}

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
        print(f"{cid} ({uid}): exp={exp_audit}, found={user_audit_record.get(uid)}, src={source_of_audit.get(uid)}")
