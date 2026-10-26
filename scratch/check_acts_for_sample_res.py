import csv
import json
import os

repo_root = r"c:\Users\Akash\Desktop\hacker rank oct hackathon"
dataset_dir = os.path.join(repo_root, "dataset")

samples = list(csv.DictReader(open(os.path.join(dataset_dir, 'sample_deletion_requests.csv'), encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open(os.path.join(dataset_dir, 'sample_output.csv'), encoding='utf-8'))}
activities = list(csv.DictReader(open(os.path.join(dataset_dir, 'system_activity.csv'), encoding='utf-8')))

# Group activities by resource_id
act_by_res = {}
for a in activities:
    act_by_res.setdefault(a['resource_id'], []).append(a)

print("Checking resources in sample_output vs system_activity:")
for s in samples:
    cid = s['case_id']
    st, steps = outputs[cid]
    step_res = set(step['resource_id'] for step in steps)
    
    # resources from steps that have activities:
    res_with_acts = {r: [a['event_type'] + ':' + a['reported_result'] for a in act_by_res.get(r, [])] for r in step_res}
    res_no_acts = [r for r in step_res if r not in act_by_res]
    
    print(f"\n{cid} ({s['email']}, {st}):")
    print(f"  Step resources with activities: {res_with_acts}")
    if res_no_acts:
        print(f"  Step resources WITHOUT activities: {res_no_acts}")
