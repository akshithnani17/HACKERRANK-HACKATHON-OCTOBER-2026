import csv
import json
from datetime import datetime

samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))
worker_acts = [a for a in activities if a['source_system'] == 'deletion_worker']

for s in samples[20:28]:
    cid = s['case_id']
    st, steps = outputs[cid]
    exp_res = set(st['resource_id'] for st in steps)
    req_dt = datetime.fromisoformat(s['requested_at'].replace('Z', '+00:00'))
    rep_dt = datetime.fromisoformat(s['reported_at'].replace('Z', '+00:00'))
    
    # Check all worker acts between requested_at and reported_at + 2h
    case_acts = []
    for a in worker_acts:
        a_dt = datetime.fromisoformat(a['event_time'].replace('Z', '+00:00'))
        if req_dt <= a_dt <= rep_dt + datetime.resolution * 7200:
            case_acts.append((a['event_time'], a['target_system'], a['resource_id'], a['reported_result']))
            
    print(f"\n{cid} (req={s['requested_at']}, rep={s['reported_at']})")
    print(f"  Expected resources: {exp_res}")
    print(f"  Worker acts in [req, rep+2h]: {len(case_acts)}")
    for act in case_acts:
        if act[2] in exp_res:
            print(f"     MATCH: {act}")
        else:
            print(f"     other: {act}")
