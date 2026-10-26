import csv
import re

# Find which users have those accounts
# Where are account_IDs mapped to users?
# In system_activity.csv, user_identities, or evidence?
with open('dataset/system_activity.csv', encoding='utf-8') as f:
    acts = list(csv.DictReader(f))

classified_accounts = [
    'account_2461', 'account_2176', 'account_9321', 'account_6486',
    'account_7452', 'account_5605', 'account_7821', 'account_5835',
    'account_1733', 'account_228'
]

print("Searching for mentions of classified accounts:")
for acc in classified_accounts:
    mentions = [a for a in acts if acc in a['resource_id'] or acc in a['details']]
    print(f"{acc}: {len(mentions)} mentions")
    for m in mentions:
        print(f"  {m['event_time']} | {m['event_type']} | {m['source_system']} -> {m['target_system']} | {m['details']}")
