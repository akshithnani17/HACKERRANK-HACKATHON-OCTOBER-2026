import csv
import json
import os
import glob
import sqlite3
import re
import fitz

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

# Map: user_id -> {system_id: set(resource_ids)}
user_resources = {uid: {} for uid in identities}

def add_user_resource(uid, system_id, resource_id):
    if not uid or uid not in identities or not resource_id:
        return
    user_resources[uid].setdefault(system_id, set()).add(resource_id)

# A. From system_activity LINK_RESOURCE_IDENTITY
with open(os.path.join(dataset_dir, 'system_activity.csv'), encoding='utf-8') as f:
    for r in csv.DictReader(f):
        res = r['resource_id']
        sys_id = r['target_system']
        if r['event_type'] == 'LINK_RESOURCE_IDENTITY':
            m_u = re.search(r'\b(user_\d+)\b', r['details'])
            if m_u:
                add_user_resource(m_u.group(1), sys_id, res)

# B. From SQL files
for sql_path in glob.glob(os.path.join(dataset_dir, 'evidence/databases/*.sql')):
    conn = sqlite3.connect(":memory:")
    with open(sql_path, encoding='utf-8') as f:
        conn.executescript(f.read())
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall()]
    for t in tables:
        cursor.execute(f"PRAGMA table_info({t});")
        cols = [c[1] for c in cursor.fetchall()]
        if 'resource_id' in cols:
            cursor.execute(f"SELECT * FROM {t};")
            for row in cursor.fetchall():
                row_dict = dict(zip(cols, row))
                res = row_dict.get('resource_id')
                if not res: continue
                sys_id = row_dict.get('origin_system')
                if not sys_id:
                    if 'customer_profiles' in t: sys_id = 'account_service'
                    elif 'search' in t: sys_id = 'search_service'
                    elif 'analytics' in t: sys_id = 'analytics_platform'
                    elif 'support' in t: sys_id = 'support_platform'
                    elif 'connector' in t: sys_id = 'integration_service'
                    elif 'backup' in t: sys_id = 'backup_service'
                    elif 'security' in t: sys_id = 'security_service'
                    elif 'export' in t: sys_id = 'export_service'
                
                found_uid = None
                for c in ['user_id', 'customer_reference', 'subject_reference']:
                    val = row_dict.get(c)
                    if val and val in identities:
                        found_uid = val
                        break
                if not found_uid:
                    for c in ['email', 'customer_email', 'owner_email', 'requester_email']:
                        val = row_dict.get(c)
                        if val and val.lower() in email_to_uid:
                            found_uid = email_to_uid[val.lower()]
                            break
                if found_uid:
                    add_user_resource(found_uid, sys_id, res)

# C. From JSON files
for jf in glob.glob(os.path.join(dataset_dir, 'evidence/records/*.json')):
    with open(jf, encoding='utf-8') as f:
        data = json.load(f)
    
    def search_obj(obj, curr_sys=None):
        if isinstance(obj, dict):
            sys_id = curr_sys
            if 'service_exports' in obj:
                for s_key, s_val in obj['service_exports'].items():
                    search_obj(s_val, curr_sys=s_key)
                return
            if 'data_store' in obj:
                sys_id = obj['data_store']
            if 'system' in obj:
                sys_id = obj['system']
            
            res = obj.get('resource_id')
            if res:
                found_uid = None
                for c in ['user_id', 'customer_reference', 'subject_reference']:
                    val = obj.get(c)
                    if val and val in identities:
                        found_uid = val
                        break
                if not found_uid:
                    for c in ['email', 'customer_email', 'owner_email', 'requester_email', 'query']:
                        val = obj.get(c)
                        if isinstance(val, str) and val.lower() in email_to_uid:
                            found_uid = email_to_uid[val.lower()]
                            break
                if found_uid and sys_id:
                    add_user_resource(found_uid, sys_id, res)
            for k, v in obj.items():
                if k not in ['service_exports']:
                    search_obj(v, curr_sys=sys_id)
        elif isinstance(obj, list):
            for item in obj:
                search_obj(item, curr_sys=curr_sys)

    search_obj(data)

# D. From TXT
txt_path = os.path.join(dataset_dir, 'evidence/records/customer_account_handover_20261001.txt')
if os.path.exists(txt_path):
    with open(txt_path, encoding='utf-8') as f:
        for line in f:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 6:
                sys_id = parts[1]
                res = parts[2]
                ref = parts[5]
                found_uid = None
                if ref in identities:
                    found_uid = ref
                elif ref.lower() in email_to_uid:
                    found_uid = email_to_uid[ref.lower()]
                if found_uid:
                    add_user_resource(found_uid, sys_id, res)

# E. From LOG files
for lf in glob.glob(os.path.join(dataset_dir, 'evidence/logs/*.log')):
    with open(lf, encoding='utf-8', errors='ignore') as f:
        for line in f:
            m_res = re.search(r'resource_id[ =":]+([a-zA-Z0-9_]+)', line)
            m_sys = re.search(r'service[ =":]+([a-zA-Z0-9_]+)', line)
            if m_res:
                res = m_res.group(1)
                sys_id = m_sys.group(1) if m_sys else None
                found_uid = None
                m_u = re.search(r'\b(user_\d+)\b', line)
                if m_u and m_u.group(1) in identities:
                    found_uid = m_u.group(1)
                else:
                    for em, uid in email_to_uid.items():
                        if em in line.lower():
                            found_uid = uid
                            break
                if found_uid and sys_id:
                    add_user_resource(found_uid, sys_id, res)

# F. From PDF files
for pf in glob.glob(os.path.join(dataset_dir, 'evidence/documents/*.pdf')):
    doc = fitz.open(pf)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    res_matches = re.findall(r'\b(audit_record_\d+|account_\d+|support_\d+|export_\d+|object_\d+)\b', text)
    u_matches = re.findall(r'\b(user_\d+)\b', text)
    for res in res_matches:
        sys_id = 'security_service' if 'audit_record' in res else 'account_service' if 'account' in res else 'support_platform' if 'support' in res else 'export_service' if 'export' in res else None
        for u in u_matches:
            if u in identities and sys_id:
                add_user_resource(u, sys_id, res)
        for em, uid in email_to_uid.items():
            if em in text.lower() and sys_id:
                add_user_resource(uid, sys_id, res)

# G. What about account_service resources from deletion_worker activities?
# In system_activity.csv, each deletion_worker activity for account_service corresponds to a deletion request!
# Let's map deletion requests to account_service activities!
samples = list(csv.DictReader(open(os.path.join(dataset_dir, 'sample_deletion_requests.csv'), encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open(os.path.join(dataset_dir, 'sample_output.csv'), encoding='utf-8'))}

# Compare user_resources with sample_outputs!
print("Comparing extracted resources with sample_output.csv:")
perfect = 0
for s in samples:
    cid = s['case_id']
    st, steps = outputs[cid]
    uid = email_to_uid[s['email'].lower()]
    expected_by_sys = {}
    for step in steps:
        expected_by_sys.setdefault(step['system_id'], set()).add(step['resource_id'])
    
    extracted_by_sys = user_resources.get(uid, {})
    
    # check differences
    diffs = []
    for sys_id, exp_res in expected_by_sys.items():
        ext_res = extracted_by_sys.get(sys_id, set())
        if not exp_res.issubset(ext_res):
            diffs.append((sys_id, "Missing:", exp_res - ext_res))
    
    if not diffs:
        perfect += 1
    else:
        print(f"Diff for {cid} ({uid}): {diffs}")

print(f"\nPerfect matches: {perfect} / {len(samples)}")
