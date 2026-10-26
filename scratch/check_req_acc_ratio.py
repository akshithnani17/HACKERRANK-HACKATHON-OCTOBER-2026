import csv
from datetime import datetime

requests = list(csv.DictReader(open('dataset/deletion_requests.csv', encoding='utf-8')))
activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))
acc_acts = [a for a in activities if a['source_system'] == 'deletion_worker' and a['target_system'] == 'account_service']

print(f"Total requests: {len(requests)}, total account worker acts: {len(acc_acts)}")
