import csv
from datetime import datetime

activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))
worker_acts = [a for a in activities if a['source_system'] == 'deletion_worker']

# Group activities into runs based on account_service submissions and following actions
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

print(f"Total deletion runs identified: {len(runs)}")
for r in runs[:10]:
    acc = r[0]['resource_id']
    time_str = r[0]['event_time']
    other_sys = [(x['target_system'], x['resource_id'], x['reported_result']) for x in r[1:]]
    print(f"Run {acc} at {time_str}: {len(r)} operations -> {other_sys}")
