import csv
import json

samples = list(csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8')))
for s in samples:
    steps = json.loads(s['steps_json'])
    acc = None
    audit = None
    for st in steps:
        if st['resource_id'].startswith('account_'):
            acc = st['resource_id']
        elif st['resource_id'].startswith('audit_record_'):
            audit = st['resource_id']
    if acc or audit:
        print(f"{s['case_id']}: account={acc}, audit={audit}")
