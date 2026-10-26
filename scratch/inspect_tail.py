import csv

with open('dataset/deletion_requests.csv', encoding='utf-8') as f:
    requests = list(csv.DictReader(f))

# Look at cases around the end:
for r in requests:
    cid_num = int(r['case_id'].split('_')[1])
    if cid_num >= 530:
        print(f"{r['case_id']} | {r['reported_status']} | {r['email']} | {r['request_text'][:80]}")
