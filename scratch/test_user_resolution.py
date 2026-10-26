import csv

# Load identities
identities = {}
email_to_uid = {}
with open('dataset/user_identities.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        identities[r['user_id']] = r
        email_to_uid[r['email'].lower()] = r['user_id']

# Load audit log
audits_by_uid = {}
old_email_to_uid = {}
with open('dataset/user_audit_log.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        uid = r['user_id']
        audits_by_uid.setdefault(uid, []).append(r)
        if r['field_name'] == 'email':
            old_email_to_uid[r['old_value'].lower()] = uid
            old_email_to_uid[r['new_value'].lower()] = uid

def resolve_user(email):
    em = email.strip().lower()
    if em in email_to_uid:
        return email_to_uid[em]
    if em in old_email_to_uid:
        return old_email_to_uid[em]
    return None

# Test on sample requests
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
unresolved_samples = [s for s in samples if not resolve_user(s['email'])]
print(f"Sample requests: {len(samples)}, unresolved: {len(unresolved_samples)}")

# Test on all deletion_requests
requests = list(csv.DictReader(open('dataset/deletion_requests.csv', encoding='utf-8')))
unresolved_reqs = [r for r in requests if not resolve_user(r['email'])]
print(f"Evaluation requests: {len(requests)}, unresolved: {len(unresolved_reqs)}")
if unresolved_reqs:
    for r in unresolved_reqs[:10]:
        print("  Unresolved:", r['case_id'], r['email'])
