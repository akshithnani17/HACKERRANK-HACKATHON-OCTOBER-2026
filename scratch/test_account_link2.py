import csv
from datetime import datetime

with open("dataset/sample_deletion_requests.csv", encoding="utf-8") as f:
    sample_reqs = list(csv.DictReader(f))

with open("dataset/system_activity.csv", encoding="utf-8") as f:
    worker_acts = [r for r in csv.DictReader(f) if r["source_system"] == "deletion_worker" and r["target_system"] == "account_service"]

for r in sample_reqs[:15]:
    cid = r["case_id"]
    rep_at = datetime.fromisoformat(r["reported_at"].replace("Z", "+00:00"))
    
    # Find closest account deletion worker activity to reported_at
    candidates = []
    for wa in worker_acts:
        w_time = datetime.fromisoformat(wa["event_time"].replace("Z", "+00:00"))
        diff = abs((rep_at - w_time).total_seconds())
        if diff < 1800: # within 30 minutes
            candidates.append((diff, wa["resource_id"], wa["activity_id"]))
            
    candidates.sort()
    best = candidates[0] if candidates else None
    print(f"{cid:<10} reported_at={r['reported_at']} -> {best}")
