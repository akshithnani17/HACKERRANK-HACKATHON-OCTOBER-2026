import csv
from datetime import datetime

# Load sample requests
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))

# Group deletion_worker activities
worker_acts = [a for a in activities if a['source_system'] == 'deletion_worker']
print(f"Total deletion worker activities: {len(worker_acts)}")

# Let's inspect the correlation between sample reported_at and worker activities
for s in samples[:10]:
    cid = s['case_id']
    rep_at = datetime.fromisoformat(s['reported_at'].replace('Z', '+00:00'))
    close_acts = []
    for a in worker_acts:
        a_dt = datetime.fromisoformat(a['event_time'].replace('Z', '+00:00'))
        if abs((a_dt - rep_at).total_seconds()) <= 3600 * 4: # within 4 hours
            close_acts.append(a)
    print(f"\n{cid} ({s['email']}, reported_at: {s['reported_at']}): {len(close_acts)} worker acts")
    for a in close_acts:
        print(f"  {a['event_time']} | {a['event_type']} | {a['target_system']} | {a['resource_id']} | {a['reported_result']}")
