import csv
from datetime import datetime

with open('dataset/system_activity.csv', encoding='utf-8') as f:
    activities = list(csv.DictReader(f))

print(f"Total activities in system_activity.csv: {len(activities)}")

# Check unique event_types
event_types = set(a['event_type'] for a in activities)
print("Event types:", event_types)

# Check unique source_systems and target_systems
sources = set(a['source_system'] for a in activities)
targets = set(a['target_system'] for a in activities)
print("Sources:", sources)
print("Targets:", targets)

# How many deletion_worker activities?
worker_acts = [a for a in activities if a['source_system'] == 'deletion_worker']
print(f"deletion_worker activities: {len(worker_acts)}")

# Let's inspect worker activities across time
first_time = activities[0]['event_time']
last_time = activities[-1]['event_time']
print(f"Timeline: {first_time} to {last_time}")
