import csv
from datetime import datetime

with open("dataset/sample_deletion_requests.csv", encoding="utf-8") as f:
    sample_reqs = list(csv.DictReader(f))

with open("dataset/system_activity.csv", encoding="utf-8") as f:
    worker_acts = [r for r in csv.DictReader(f) if r["source_system"] == "deletion_worker" and r["target_system"] == "account_service"]

for r in sample_reqs[:10]:
    cid = r["case_id"]
    rep_at = datetime.fromisoformat(r["reported_at"].replace("Z", "+00:00"))
    req_at = datetime.fromisoformat(r["requested_at"].replace("Z", "+00:00"))
    
    # Find matching account activity within 30 minutes before reported_at
    candidates = []
    for wa in worker_acts:
        w_time = datetime.fromisoformat(wa["event_time"].replace("Z", "+00:00"))
        if req_at <= w_time <= rep_at:
            diff = (rep_at - w_time).total_seconds()
            candidates.append((diff, wa["resource_id"], wa["activity_id"]))
            
    candidates.sort()
    best = candidates[0] if candidates else None
    print(f"{cid:<10} reported_at={r['reported_at']} -> account={best}")
