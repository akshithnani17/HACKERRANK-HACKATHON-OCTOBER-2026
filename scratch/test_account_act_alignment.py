import csv
from datetime import datetime

# Load requests
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
requests = list(csv.DictReader(open('dataset/deletion_requests.csv', encoding='utf-8')))

# Load system activities
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))

# Find all activities where target_system == 'account_service' and source_system == 'deletion_worker'
acc_acts = [a for a in activities if a['source_system'] == 'deletion_worker' and a['target_system'] == 'account_service']
print(f"Total account deletion worker activities: {len(acc_acts)}")

# Let's see if we can match each request's reported_at to an account_service deletion activity
def find_acc_act(rep_at_str):
    rep_dt = datetime.fromisoformat(rep_at_str.replace('Z', '+00:00'))
    best_act = None
    min_diff = float('inf')
    for a in acc_acts:
        a_dt = datetime.fromisoformat(a['event_time'].replace('Z', '+00:00'))
        diff = abs((a_dt - rep_dt).total_seconds())
        if diff < min_diff:
            min_diff = diff
            best_act = a
    return best_act, min_diff

# Check for sample cases
sample_matches = []
for s in samples:
    act, diff = find_acc_act(s['reported_at'])
    sample_matches.append((s['case_id'], s['reported_at'], act['resource_id'] if act else None, diff))

print("Sample cases closest account activity:")
for cid, rep_at, res, diff in sample_matches[:10]:
    print(f"  {cid} ({rep_at}): res={res}, diff={diff:.1f}s")

# Check for evaluation requests (excluding the 10 non-deletion requests)
non_del_cids = {f"case_{i}" for i in range(533, 543)}
eval_matches = []
large_diffs = []
for r in requests:
    if r['case_id'] in non_del_cids:
        continue
    act, diff = find_acc_act(r['reported_at'])
    if diff > 7200: # more than 2 hours
        large_diffs.append((r['case_id'], r['reported_at'], act['resource_id'] if act else None, diff))

print(f"Evaluation requests total: {len(requests) - len(non_del_cids)}, large diffs (>2h): {len(large_diffs)}")
if large_diffs:
    for cid, rep, res, diff in large_diffs[:10]:
        print(f"  Large diff: {cid} rep={rep} res={res} diff={diff:.1f}s")
