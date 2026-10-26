import csv
import json
import os

repo_root = r"c:\Users\Akash\Desktop\hacker rank oct hackathon"
dataset_dir = os.path.join(repo_root, "dataset")

samples = list(csv.DictReader(open(os.path.join(dataset_dir, 'sample_deletion_requests.csv'), encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open(os.path.join(dataset_dir, 'sample_output.csv'), encoding='utf-8'))}

activities = list(csv.DictReader(open(os.path.join(dataset_dir, 'system_activity.csv'), encoding='utf-8')))
act_resources = set(a['resource_id'] for a in activities)

print("Checking resource sources for sample cases:")
for s in samples:
    cid = s['case_id']
    st, steps = outputs[cid]
    step_resources = [step['resource_id'] for step in steps]
    in_act = [r for r in step_resources if r in act_resources]
    not_in_act = [r for r in step_resources if r not in act_resources]
    if not_in_act:
        print(f"{cid} ({st}): total {len(step_resources)} res, in acts: {len(in_act)}, NOT in acts: {not_in_act}")
