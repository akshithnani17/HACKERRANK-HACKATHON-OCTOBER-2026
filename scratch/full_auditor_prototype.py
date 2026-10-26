import csv
import json
import os
import glob
import re
import sqlite3
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

# 2. System Activities
activities = list(csv.DictReader(open(os.path.join(dataset_dir, 'system_activity.csv'), encoding='utf-8')))
worker_acts = [a for a in activities if a['source_system'] == 'deletion_worker']

# 3. Evidence Files
ev_manifest = list(csv.DictReader(open(os.path.join(dataset_dir, 'evidence_files.csv'), encoding='utf-8')))
ev_manifest.sort(key=lambda x: x['captured_at'])

# 4. Sorting Constants
PHASE_ORDER = {"FINDING": 1, "REMEDIATION": 2, "VERIFICATION": 3}
OP_ORDER = {
    # Findings
    "REPORT_REMAINING_RECORD": 1,
    "REPORT_EXPOSED_PII": 2,
    "REPORT_ACTIVE_DATA_FLOW": 3,
    "REPORT_RESTORE_RISK": 4,
    # Remediation
    "DISABLE_DATA_FLOW": 1,
    "BLOCK_RESTORE": 2,
    "DELETE_RECORD": 3,
    "REDACT_RECORD": 4,
    "ANONYMIZE_RECORD": 5,
    # Verification
    "VERIFY_RECORD_ABSENT": 1,
    "VERIFY_RECORD_PRESENT": 2,
    "VERIFY_RECORD_REDACTED": 3,
    "VERIFY_RECORD_ANONYMIZED": 4,
    "VERIFY_DATA_FLOW_DISABLED": 5,
    "VERIFY_RESTORE_BLOCKED": 6,
}

def sort_and_number_steps(steps):
    def sort_key(s):
        return (
            PHASE_ORDER[s['phase']],
            OP_ORDER[s['operation']],
            s['system_id'],
            s['resource_id']
        )
    sorted_steps = sorted(steps, key=sort_key)
    for idx, s in enumerate(sorted_steps, 1):
        s['step_no'] = idx
    return sorted_steps

print("Framework components ready.")
