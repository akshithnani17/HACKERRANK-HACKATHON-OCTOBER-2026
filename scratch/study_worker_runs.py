import csv
import json
from datetime import datetime

# Load sample requests
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

# Load system activities
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))

# Check all deletion_worker activities around requested_at and reported_at
for s in samples[:15]:
    cid = s['case_id']
    st, steps = outputs[cid]
    expected_acc = None
    for step in steps:
        if step['system_id'] == 'account_service':
            expected_acc = step['resource_id']
            break
    
    req_dt = datetime.fromisoformat(s['requested_at'].replace('Z', '+00:00'))
    rep_dt = datetime.fromisoformat(s['reported_at'].replace('Z', '+00:00'))
    
    # find all worker activities between req_dt and rep_dt + 1 hour
    acts = []
    for a in activities:
        if a['source_system'] == 'deletion_worker':
            a_dt = datetime.fromisoformat(a['event_time'].replace('Z', '+00:00'))
            if req_dt <= a_dt <= rep_dt + datetime.resolution * 3600: # up to 1 hour after rep_dt
                acts.append(a)
    
    print(f"\n{cid} (req={s['requested_at']}, rep={s['reported_at']}): expected_acc={expected_acc}")
    print(f"  Activities in window [req, rep+1h]: {len(acts)}")
    for a in acts[:10]:
        print(f"    {a['event_time']} | {a['target_system']} | {a['resource_id']} | {a['reported_result']}")
