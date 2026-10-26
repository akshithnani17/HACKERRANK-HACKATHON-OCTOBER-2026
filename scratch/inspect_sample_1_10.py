import csv
import json
import os
import glob
import re

dataset_dir = r"c:\Users\Akash\Desktop\hacker rank oct hackathon\dataset"
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open(os.path.join(dataset_dir, 'sample_output.csv'), encoding='utf-8'))}
samples = {r['case_id']: r for r in csv.DictReader(open(os.path.join(dataset_dir, 'sample_deletion_requests.csv'), encoding='utf-8'))}

# For cases 1 to 10, print the findings and check what is inside their cited evidence files
for cid in [f"case_{i:02d}" for i in range(1, 11)]:
    req = samples[cid]
    st, steps = outputs[cid]
    print(f"\n=== {cid}: {st} (audit={req['audit_at']}) ===")
    for s in steps:
        print(f"  {s['phase']} | {s['system_id']} | {s['resource_id']} | {s['operation']} | ev={s['evidence_id']}")
