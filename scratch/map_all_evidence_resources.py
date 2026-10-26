import csv
import json
import os
import glob
import sqlite3
import re
import fitz

repo_root = r"c:\Users\Akash\Desktop\hacker rank oct hackathon"
dataset_dir = os.path.join(repo_root, "dataset")

# Load identities & audits
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

# Map resource -> set of uids, and resource -> system_id, and resource -> data_category
res_to_user = {}
res_to_system = {}

# 1. From LINK_RESOURCE_IDENTITY in system_activity
with open(os.path.join(dataset_dir, 'system_activity.csv'), encoding='utf-8') as f:
    for r in csv.DictReader(f):
        res = r['resource_id']
        if r['event_type'] == 'LINK_RESOURCE_IDENTITY':
            # e.g. "Data catalog linked account_5762 (account_5762) to haruka.s1838@zoho.com and user_11."
            m_u = re.search(r'\b(user_\d+)\b', r['details'])
            if m_u:
                res_to_user.setdefault(res, set()).add(m_u.group(1))
            res_to_system[res] = r['target_system']

# 2. From all SQL files
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
                # system
                if 'customer_profiles' in t: res_to_system[res] = 'account_service'
                elif 'search' in t: res_to_system[res] = 'search_service'
                elif 'analytics' in t: res_to_system[res] = 'analytics_platform'
                elif 'support' in t: res_to_system[res] = 'support_platform'
                elif 'connector' in t: res_to_system[res] = 'integration_service'
                elif 'backup' in t: res_to_system[res] = 'backup_service'
                elif 'security' in t: res_to_system[res] = 'security_service'
                
                # origin_system column
                if 'origin_system' in row_dict and row_dict['origin_system']:
                    res_to_system[res] = row_dict['origin_system']
                
                # find uid
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
                    res_to_user.setdefault(res, set()).add(found_uid)

# 3. From all JSON files
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
                if sys_id:
                    res_to_system[res] = sys_id
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
                if found_uid:
                    res_to_user.setdefault(res, set()).add(found_uid)
            for k, v in obj.items():
                if k not in ['service_exports']:
                    search_obj(v, curr_sys=sys_id)
        elif isinstance(obj, list):
            for item in obj:
                search_obj(item, curr_sys=curr_sys)

    search_obj(data)

# 4. From TXT (customer_account_handover_20261001.txt)
txt_path = os.path.join(dataset_dir, 'evidence/records/customer_account_handover_20261001.txt')
if os.path.exists(txt_path):
    with open(txt_path, encoding='utf-8') as f:
        for line in f:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 6:
                # - 2026-10-01T12:00:00Z | security_service | audit_record_9394 | SECURITY_AUDIT_LOG | FOUND | user_32
                sys_id = parts[1]
                res = parts[2]
                ref = parts[5]
                res_to_system[res] = sys_id
                if ref in identities:
                    res_to_user.setdefault(res, set()).add(ref)
                elif ref.lower() in email_to_uid:
                    res_to_user.setdefault(res, set()).add(email_to_uid[ref.lower()])

# 5. From LOG files
for lf in glob.glob(os.path.join(dataset_dir, 'evidence/logs/*.log')):
    with open(lf, encoding='utf-8', errors='ignore') as f:
        for line in f:
            m_res = re.search(r'resource_id[ =":]+([a-zA-Z0-9_]+)', line)
            m_sys = re.search(r'service[ =":]+([a-zA-Z0-9_]+)', line)
            if m_res:
                res = m_res.group(1)
                if m_sys:
                    res_to_system[res] = m_sys.group(1)
                found_uid = None
                m_u = re.search(r'\b(user_\d+)\b', line)
                if m_u and m_u.group(1) in identities:
                    found_uid = m_u.group(1)
                else:
                    for em, uid in email_to_uid.items():
                        if em in line.lower():
                            found_uid = uid
                            break
                if found_uid:
                    res_to_user.setdefault(res, set()).add(found_uid)

# 6. From PDF files
for pf in glob.glob(os.path.join(dataset_dir, 'evidence/documents/*.pdf')):
    doc = fitz.open(pf)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    # Find all resource IDs in text
    res_matches = re.findall(r'\b(audit_record_\d+|account_\d+|support_\d+|export_\d+|object_\d+)\b', text)
    u_matches = re.findall(r'\b(user_\d+)\b', text)
    for res in res_matches:
        for u in u_matches:
            if u in identities:
                res_to_user.setdefault(res, set()).add(u)
        for em, uid in email_to_uid.items():
            if em in text.lower():
                res_to_user.setdefault(res, set()).add(uid)

print(f"Total mapped resources: {len(res_to_user)}")

# Check against sample outputs!
samples = list(csv.DictReader(open(os.path.join(dataset_dir, 'sample_deletion_requests.csv'), encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open(os.path.join(dataset_dir, 'sample_output.csv'), encoding='utf-8'))}

missing = 0
total = 0
for s in samples:
    cid = s['case_id']
    st, steps = outputs[cid]
    uid = email_to_uid[s['email'].lower()]
    for step in steps:
        total += 1
        res = step['resource_id']
        uids = res_to_user.get(res, set())
        if uid not in uids:
            missing += 1
            print(f"MISSING: {cid} ({uid}) -> {res} (found uids={uids})")

print(f"Sample step resources: {total}, missing: {missing}")
