import csv
import json
import os

ev_map = {r['file_id']: r for r in csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8'))}
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

for s in samples:
    cid = s['case_id']
    st, steps = outputs[cid]
    ev_ids = sorted(list(set(step['evidence_id'] for step in steps if step['evidence_id'])))
    print(f"=== {cid} ({st}) req={s['requested_at']} rep={s['reported_at']} audit={s['audit_at']} ===")
    print(f"Cited evidence: {ev_ids}")
    for eid in ev_ids:
        ev = ev_map[eid]
        print(f"  {eid}: captured={ev['captured_at']} origin={ev['origin']} path={ev['file_path']}")
    for step in steps:
        print(f"  step {step['step_no']}: {step['phase']} | {step['system_id']} | {step['resource_id']} | {step['operation']} | {step['state']} | ev={step['evidence_id']}")
    print()
