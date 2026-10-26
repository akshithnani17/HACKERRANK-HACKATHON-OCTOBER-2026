import csv
from datetime import datetime

activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))

worker_acts = [a for a in activities if a['source_system'] == 'deletion_worker']
print(f"Total deletion worker activities: {len(worker_acts)}")

# Check time difference between request reported_at and worker activities
for s in samples[10:20]:
    cid = s['case_id']
    rep_dt = datetime.fromisoformat(s['reported_at'].replace('Z', '+00:00'))
    nearby = []
    for a in worker_acts:
        a_dt = datetime.fromisoformat(a['event_time'].replace('Z', '+00:00'))
        diff_min = (a_dt - rep_dt).total_seconds() / 60.0
        if -120 <= diff_min <= 120:
            nearby.append((diff_min, a['target_system'], a['resource_id'], a['reported_result']))
    print(f"\n{cid} (rep={s['reported_at']}): {len(nearby)} worker activities within [-2h, +2h]")
    for diff_min, sys, res, res_code in nearby[:8]:
        print(f"   {diff_min:+.1f}m: {sys} {res} ({res_code})")
