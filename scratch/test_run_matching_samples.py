import csv
import json
import os
from datetime import datetime

repo_root = r"c:\Users\Akash\Desktop\hacker rank oct hackathon"
dataset_dir = os.path.join(repo_root, "dataset")

samples = list(csv.DictReader(open(os.path.join(dataset_dir, 'sample_deletion_requests.csv'), encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open(os.path.join(dataset_dir, 'sample_output.csv'), encoding='utf-8'))}

activities = list(csv.DictReader(open(os.path.join(dataset_dir, 'system_activity.csv'), encoding='utf-8')))
worker_acts = [a for a in activities if a['source_system'] == 'deletion_worker']

runs = []
curr_run = []
for a in worker_acts:
    if a['target_system'] == 'account_service':
        if curr_run:
            runs.append(curr_run)
        curr_run = [a]
    else:
        if curr_run:
            curr_run.append(a)
if curr_run:
    runs.append(curr_run)

# Match each sample request to a run!
# A run's timestamp is within ~1-2 hours of request reported_at
matched_perfectly = 0
for s in samples:
    cid = s['case_id']
    st, steps = outputs[cid]
    exp_resources = set(step['resource_id'] for step in steps if not step['resource_id'].startswith('audit_record_'))
    rep_dt = datetime.fromisoformat(s['reported_at'].replace('Z', '+00:00'))
    
    # candidate runs within 2 hours of reported_at
    best_run = None
    min_diff = float('inf')
    max_overlap = -1
    
    for r in runs:
        r_dt = datetime.fromisoformat(r[0]['event_time'].replace('Z', '+00:00'))
        diff = abs((r_dt - rep_dt).total_seconds())
        if diff <= 7200: # within 2 hours
            run_res = set(x['resource_id'] for x in r)
            overlap = len(exp_resources.intersection(run_res))
            if overlap > max_overlap or (overlap == max_overlap and diff < min_diff):
                max_overlap = overlap
                min_diff = diff
                best_run = r
                
    run_resources = set(x['resource_id'] for x in best_run) if best_run else set()
    diff_res = exp_resources - run_resources
    if not diff_res:
        matched_perfectly += 1
    else:
        print(f"{cid} diff: exp={exp_resources}, run={run_resources}")

print(f"\nRuns matched perfectly to sample resources: {matched_perfectly} / {len(samples)}")
