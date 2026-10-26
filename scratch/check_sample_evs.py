import csv
import json

with open("dataset/sample_output.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        cid = r["case_id"]
        status = r["deletion_status"]
        steps = json.loads(r["steps_json"])
        evs = [s["evidence_id"] for s in steps if s.get("evidence_id")]
        res = [s["resource_id"] for s in steps]
        print(f"{cid:<10} {status:<15} evs={evs[:2]} res={res[:3]}")
