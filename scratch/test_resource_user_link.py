import csv
import json
import os
import glob
import sqlite3
import re

repo_root = r"c:\Users\Akash\Desktop\hacker rank oct hackathon"
dataset_dir = os.path.join(repo_root, "dataset")

# Load users
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

# Let's map every resource to a user_id by looking across all evidence files and activities!
resource_to_user = {}

# 1. From all SQL files
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
                    resource_to_user.setdefault(res, set()).add(found_uid)

print(f"Mapped {len(resource_to_user)} resources from SQL files.")

# 2. From all JSON files
for jf in glob.glob(os.path.join(dataset_dir, 'evidence/records/*.json')):
    with open(jf, encoding='utf-8') as f:
        data = json.load(f)
    
    def search_obj(obj):
        if isinstance(obj, dict):
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
                if found_uid:
                    resource_to_user.setdefault(res, set()).add(found_uid)
            for v in obj.values():
                search_obj(v)
        elif isinstance(obj, list):
            for item in obj:
                search_obj(item)

    search_obj(data)

print(f"Mapped {len(resource_to_user)} resources after JSON files.")

# 3. From text & log files
for lf in glob.glob(os.path.join(dataset_dir, 'evidence/logs/*.log')) + glob.glob(os.path.join(dataset_dir, 'evidence/records/*.txt')):
    with open(lf, encoding='utf-8', errors='ignore') as f:
        for line in f:
            # find resource_id=... or resource_id "..."
            m_res = re.search(r'resource_id[ =":]+([a-zA-Z0-9_]+)', line)
            if m_res:
                res = m_res.group(1)
                found_uid = None
                # search for user_XX
                m_u = re.search(r'\b(user_\d+)\b', line)
                if m_u and m_u.group(1) in identities:
                    found_uid = m_u.group(1)
                else:
                    for em, uid in email_to_uid.items():
                        if em in line.lower():
                            found_uid = uid
                            break
                if found_uid:
                    resource_to_user.setdefault(res, set()).add(found_uid)

print(f"Total mapped resources: {len(resource_to_user)}")

# Now test: For the 32 sample cases, how many expected resources are in resource_to_user?
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
        uids = resource_to_user.get(res, set())
        if uid not in uids:
            missing += 1
            print(f"MISSING link: {cid} ({uid}) -> {res} (found uids={uids})")

print(f"Sample step resources: {total}, missing links: {missing}")
