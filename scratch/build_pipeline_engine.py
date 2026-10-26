import csv
import json
import os
import glob
import re
import sqlite3
from datetime import datetime

dataset_dir = r"c:\Users\Akash\Desktop\hacker rank oct hackathon\dataset"

# 1. Load Identities and Audit Log
identities = {r['user_id']: r for r in csv.DictReader(open(os.path.join(dataset_dir, 'user_identities.csv'), encoding='utf-8'))}
email_to_uid = {r['email'].lower(): r['user_id'] for r in identities.values()}
uid_to_emails = {uid: {identities[uid]['email'].lower()} for uid in identities}
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

# 2. Load Manifest
ev_manifest = {r['file_id']: r for r in csv.DictReader(open(os.path.join(dataset_dir, 'evidence_files.csv'), encoding='utf-8'))}

# 3. Non-deletion classifier keywords
NON_DEL_KEYWORDS = [
    "export my data", "download my personal data", "send me a copy of my data", "export of all my data",
    "opt out of marketing", "unsubscribe", "remove me from your marketing lists", "stop sending promotional",
    "update my phone number", "correct my phone number", "change my email", "update my email",
    "access my personal information", "what data do you store", "copy of my personal data",
    "cannot log in", "reset my password", "help accessing my account"
]

def is_deletion_request(text):
    t = text.lower()
    for kw in NON_DEL_KEYWORDS:
        if kw in t:
            return False
    # Check for affirmative deletion words
    if any(w in t for w in ["delete", "remove", "erasure", "erase", "close my account", "purge", "löschen", "supprimer", "eliminar", "suppression", "eliminación"]):
        return True
    return False

print("Helper definitions initialized.")
