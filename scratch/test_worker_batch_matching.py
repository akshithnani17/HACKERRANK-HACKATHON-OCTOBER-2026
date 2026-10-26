import csv
import json
from datetime import datetime

# Load sample requests
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

# Load system activities
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))
worker_acts = [a for a in activities if a['source_system'] == 'deletion_worker']

print("Matching sample cases to deletion_worker activity batches:")

for s in samples:
    cid = s['case_id']
    st, steps = outputs[cid]
    rep_dt = datetime.fromisoformat(s['reported_at'].replace('Z', '+00:00'))
    
    # Check all worker activities within a window around reported_at
    # Let's find activities that match the expected resources
    expected_res = set(step['resource_id'] for step in steps)
    
    matched_acts = [a for a in worker_acts if a['resource_id'] in expected_res]
    
    print(f"\n{cid} ({s['email']}, reported={s['reported_at']}):")
    print(f"  Expected resources: {expected_res}")
    for a in matched_acts:
        a_dt = datetime.fromisoformat(a['event_time'].replace('Z', '+00:00'))
        diff_min = (a_dt - rep_dt).total_seconds() / 60.0
        print(f"    diff={diff_min:6.1f}m | {a['event_time']} | {a['target_system']} | {a['resource_id']} | {a['reported_result']}")
