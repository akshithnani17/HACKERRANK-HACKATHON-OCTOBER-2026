import csv
import json

# Load sample outputs
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

# Load identities & audits
identities = {r['user_id']: r for r in csv.DictReader(open('dataset/user_identities.csv', encoding='utf-8'))}
email_to_uid = {r['email'].lower(): r['user_id'] for r in identities.values()}
with open('dataset/user_audit_log.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['field_name'] == 'email':
            email_to_uid[r['old_value'].lower()] = r['user_id']
            email_to_uid[r['new_value'].lower()] = r['user_id']

# Load system activities
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))

print("Analyzing sample cases vs system_activity:")
for s in samples[:15]:
    cid = s['case_id']
    st, steps = outputs[cid]
    uid = email_to_uid[s['email'].lower()]
    step_res = {step['resource_id']: step for step in steps}
    
    # Check which activities mention these resource IDs or this user
    matching_acts = [a for a in activities if a['resource_id'] in step_res]
    print(f"\n{cid} (User: {uid}, {s['email']}, status: {st}):")
    print(f"  Expected resources: {list(step_res.keys())}")
    print(f"  Matching activities in system_activity.csv: {len(matching_acts)}")
    for a in matching_acts:
        print(f"    act: {a['event_time']} | {a['event_type']} | {a['target_system']} | {a['resource_id']} | {a['reported_result']} | {a['details']}")
