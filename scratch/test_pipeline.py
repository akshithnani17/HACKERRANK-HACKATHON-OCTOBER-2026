import csv
import json
import os
import glob
import re
import sqlite3
from datetime import datetime

dataset_dir = r"c:\Users\Akash\Desktop\hacker rank oct hackathon\dataset"

# 1. Identity Resolver
identities = {r['user_id']: r for r in csv.DictReader(open(os.path.join(dataset_dir, 'user_identities.csv'), encoding='utf-8'))}
email_to_uid = {r['email'].lower(): r['user_id'] for r in identities.values()}
uid_to_all_emails = {uid: {identities[uid]['email'].lower()} for uid in identities}
uid_to_all_phones = {uid: {identities[uid]['phone']} for uid in identities if identities[uid].get('phone')}

with open(os.path.join(dataset_dir, 'user_audit_log.csv'), encoding='utf-8') as f:
    for r in csv.DictReader(f):
        uid = r['user_id']
        if r['field_name'] == 'email':
            email_to_uid[r['old_value'].lower()] = uid
            email_to_uid[r['new_value'].lower()] = uid
            uid_to_all_emails.setdefault(uid, set()).add(r['old_value'].lower())
            uid_to_all_emails.setdefault(uid, set()).add(r['new_value'].lower())
        elif r['field_name'] == 'phone':
            uid_to_all_phones.setdefault(uid, set()).add(r['old_value'])
            uid_to_all_phones.setdefault(uid, set()).add(r['new_value'])

# 2. Evidence Files Index
evidence_files = list(csv.DictReader(open(os.path.join(dataset_dir, 'evidence_files.csv'), encoding='utf-8')))
ev_map = {r['file_id']: r for r in evidence_files}

print("Loaded identities and evidence files successfully.")
