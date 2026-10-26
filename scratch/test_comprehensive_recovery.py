import csv
import json
import os
import glob
import re
import sqlite3
import fitz
from datetime import datetime

dataset_dir = r"c:\Users\Akash\Desktop\hacker rank oct hackathon\dataset"

# 1. Identities
identities = {r['user_id']: r for r in csv.DictReader(open(os.path.join(dataset_dir, 'user_identities.csv'), encoding='utf-8'))}
email_to_uid = {r['email'].lower(): r['user_id'] for r in identities.values()}
uid_to_emails = {uid: {identities[uid]['email'].lower()} for uid in identities}
uid_to_names = {uid: {identities[uid]['name'].lower()} for uid in identities if identities[uid].get('name')}
uid_to_phones = {uid: {identities[uid]['phone']} for uid in identities if identities[uid].get('phone')}

with open(os.path.join(dataset_dir, 'user_audit_log.csv'), encoding='utf-8') as f:
    for r in csv.DictReader(f):
        uid = r['user_id']
        if r['field_name'] == 'email':
            email_to_uid[r['old_value'].lower()] = uid
            email_to_uid[r['new_value'].lower()] = uid
            uid_to_emails.setdefault(uid, set()).add(r['old_value'].lower())
            uid_to_emails.setdefault(uid, set()).add(r['new_value'].lower())
        elif r['field_name'] == 'phone':
            uid_to_phones.setdefault(uid, set()).add(r['old_value'])
            uid_to_phones.setdefault(uid, set()).add(r['new_value'])

# 2. Manifest
ev_manifest = list(csv.DictReader(open(os.path.join(dataset_dir, 'evidence_files.csv'), encoding='utf-8')))
ev_manifest.sort(key=lambda x: x['captured_at'])

# Load samples & golden outputs
samples = list(csv.DictReader(open(os.path.join(dataset_dir, 'sample_deletion_requests.csv'), encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open(os.path.join(dataset_dir, 'sample_output.csv'), encoding='utf-8'))}

# Pre-parse audit records
user_audit_record = {}
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
                    except: pass

for jf in glob.glob(os.path.join(dataset_dir, 'evidence/records/*.json')):
    try:
        with open(jf, encoding='utf-8') as f:
            data = json.load(f)
        def search_audit(obj):
            if isinstance(obj, dict):
                res = obj.get('resource_id')
                if res and res.startswith('audit_record_'):
                    sub = obj.get('subject_reference')
                    if sub and sub in identities:
                        user_audit_record[sub] = res
                for v in obj.values(): search_audit(v)
            elif isinstance(obj, list):
                for item in obj: search_audit(item)
        search_audit(data)
    except: pass

txt_path = os.path.join(dataset_dir, 'evidence/records/customer_account_handover_20261001.txt')
if os.path.exists(txt_path):
    with open(txt_path, encoding='utf-8') as f:
        for line in f:
            if 'audit_record_' in line:
                m_res = re.search(r'\b(audit_record_\d+)\b', line)
                m_u = re.search(r'\b(user_\d+)\b', line)
                if m_res and m_u and m_u.group(1) in identities:
                    user_audit_record[m_u.group(1)] = m_res.group(1)

for lf in glob.glob(os.path.join(dataset_dir, 'evidence/logs/*.log')):
    trace_to_user = {}
    with open(lf, encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    for line in lines:
        m_tr = re.search(r'trace_id[:=]"?([a-zA-Z0-9_\-]+)"?', line)
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
        m_tr = re.search(r'trace_id[:=]"?([a-zA-Z0-9_\-]+)"?', line)
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

# Let's inspect each sample case
exact_res_count = 0
for s in samples:
    cid = s['case_id']
    st, steps = outputs[cid]
    uid = email_to_uid[s['email'].lower()]
    user_emails = uid_to_emails[uid]
    exp_resources = set(step['resource_id'] for step in steps)
    
    # Collect resources from evidence
    found_resources = set()
    if uid in user_audit_record:
        found_resources.add(user_audit_record[uid])
        
    audit_dt = datetime.fromisoformat(s['audit_at'].replace('Z', '+00:00'))
    
    # 1. Search JSON snapshot / export files <= audit_dt
    for ev in ev_manifest:
        if ev['captured_at'] > s['audit_at']: continue
        p = os.path.join(dataset_dir, ev['file_path'])
        if not os.path.exists(p): continue
        if p.endswith('.json'):
            try:
                data = json.load(open(p, encoding='utf-8'))
                # check service_exports
                if 'service_exports' in data:
                    se = data['service_exports']
                    for q in se.get('search_service', {}).get('index_queries', []):
                        if q.get('query') and q.get('query').lower() in user_emails:
                            found_resources.add(q.get('resource_id'))
                    for ap in se.get('analytics_platform', {}).get('profiles', []):
                        if ap.get('customer_reference') == uid or (ap.get('email') and ap.get('email').lower() in user_emails):
                            found_resources.add(ap.get('resource_id'))
                    for t in se.get('support_platform', {}).get('tickets', []):
                        if t.get('customer_reference') == uid or (t.get('requester_email') and t.get('requester_email').lower() in user_emails):
                            found_resources.add(t.get('resource_id'))
                    for c in se.get('integration_service', {}).get('connectors', []):
                        if c.get('customer_reference') == uid or (c.get('customer_email') and c.get('customer_email').lower() in user_emails):
                            found_resources.add(c.get('resource_id'))
                    for b in se.get('backup_service', {}).get('restore_entries', []):
                        if b.get('customer_reference') == uid or (b.get('customer_email') and b.get('customer_email').lower() in user_emails):
                            found_resources.add(b.get('resource_id'))
                    for e in se.get('export_service', {}).get('exports', []):
                        if e.get('customer_reference') == uid or (e.get('owner_email') and e.get('owner_email').lower() in user_emails):
                            found_resources.add(e.get('resource_id'))
                    for lk in se.get('account_service', {}).get('profile_lookups', []):
                        if lk.get('customer_reference') == uid or (lk.get('email') and lk.get('email').lower() in user_emails):
                            found_resources.add(lk.get('resource_id'))
                # check snapshots
                if 'snapshots' in data:
                    for snap in data['snapshots']:
                        for rec in snap.get('records', []):
                            if rec.get('subject_reference') == uid or rec.get('customer_reference') == uid or rec.get('user_id') == uid:
                                found_resources.add(rec.get('resource_id'))
            except: pass
        elif p.endswith('.txt'):
            try:
                for line in open(p, encoding='utf-8'):
                    if uid in line or any(em in line.lower() for em in user_emails):
                        m = re.search(r'\b([a-zA-Z0-9_]+_\d+)\b', line)
                        if m:
                            found_resources.add(m.group(1))
            except: pass
        elif p.endswith('.log'):
            try:
                lines = open(p, encoding='utf-8', errors='ignore').readlines()
                trace_to_u = {}
                for l in lines:
                    m_tr = re.search(r'trace_id[:=]"?([a-zA-Z0-9_\-]+)"?', l)
                    if m_tr:
                        tr = m_tr.group(1)
                        if uid in l or any(em in l.lower() for em in user_emails):
                            trace_to_u[tr] = uid
                for l in lines:
                    m_tr = re.search(r'trace_id[:=]"?([a-zA-Z0-9_\-]+)"?', l)
                    m_res = re.search(r'resource_id[ =":]+([a-zA-Z0-9_]+)', l)
                    if m_tr and m_res:
                        if m_tr.group(1) in trace_to_u:
                            found_resources.add(m_res.group(1))
            except: pass
            
    diff = exp_resources - found_resources
    if not diff:
        exact_res_count += 1
    else:
        print(f"{cid} ({uid}) missing: {diff}")

print(f"\nExact resource recovery: {exact_res_count} / {len(samples)}")
