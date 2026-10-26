import csv
import json

samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

for s in samples[:10]:
    cid = s['case_id']
    st, steps = outputs[cid]
    print(f"=== {cid} ({s['email']}) -> {st} ===")
    print("  request_text:", s['request_text'])
    print("  reported_status:", s['reported_status'], "audit_at:", s['audit_at'])
    for step in steps:
        print("   ", step)
