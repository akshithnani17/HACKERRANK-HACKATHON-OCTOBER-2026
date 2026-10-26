import csv
import json
import glob
import os

repo_root = r"c:\Users\Akash\Desktop\hacker rank oct hackathon"
dataset_dir = os.path.join(repo_root, "dataset")

samples = list(csv.DictReader(open(os.path.join(dataset_dir, 'sample_deletion_requests.csv'), encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open(os.path.join(dataset_dir, 'sample_output.csv'), encoding='utf-8'))}

# Build mapping of all occurrences of any resource ID across all files
print("Searching occurrences of each resource in each sample case...")

for s in samples:
    cid = s['case_id']
    st, steps = outputs[cid]
    email = s['email']
    req_at = s['requested_at']
    rep_at = s['reported_at']
    aud_at = s['audit_at']
    
    res_list = [step['resource_id'] for step in steps]
    print(f"\n==========================================")
    print(f"CASE: {cid} | {email} | {st} | req={req_at} | rep={rep_at} | aud={aud_at}")
    for step in steps:
        print(f"  Step {step['step_no']}: {step['phase']} | {step['system_id']} | {step['resource_id']} | {step['operation']} | {step['state']} | ev={step['evidence_id']}")
