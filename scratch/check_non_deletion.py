import csv

with open('dataset/deletion_requests.csv', encoding='utf-8') as f:
    requests = list(csv.DictReader(f))

print(f"Total requests in deletion_requests.csv: {len(requests)}")

non_del_keywords = ['access', 'export', 'download', 'correct', 'rectify', 'update my', 'opt-out', 'marketing', 'copy of my data', 'portability']

potential_non_del = []
for r in requests:
    text = r['request_text'].lower()
    # Check if text does not ask for deletion, or asks for access/export only
    if any(k in text for k in ['export my data', 'download my data', 'send me a copy', 'access to my data', 'rectify', 'update my email', 'opt out of marketing', 'unsubscribe']):
        potential_non_del.append((r['case_id'], r['email'], r['request_text']))

print(f"Found {len(potential_non_del)} potential non-deletion requests:")
for cid, email, txt in potential_non_del[:15]:
    print(f"{cid} | {email} | {txt}")
