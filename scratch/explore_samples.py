import csv
import json
import os

repo_root = r"c:\Users\Akash\Desktop\hacker rank oct hackathon"
dataset_dir = os.path.join(repo_root, "dataset")

# Load sample requests
samples = []
with open(os.path.join(dataset_dir, "sample_deletion_requests.csv"), "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        samples.append(r)

# Load sample outputs
sample_outputs = {}
with open(os.path.join(dataset_dir, "sample_output.csv"), "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        sample_outputs[r["case_id"]] = {
            "deletion_status": r["deletion_status"],
            "steps": json.loads(r["steps_json"])
        }

print(f"Loaded {len(samples)} sample requests and {len(sample_outputs)} sample outputs.")

# Summary of sample outputs
status_counts = {}
for cid, out in sample_outputs.items():
    st = out["deletion_status"]
    status_counts[st] = status_counts.get(st, 0) + 1
print("Sample status counts:", status_counts)

# For each sample, print case_id, email, status, and steps summary
for s in samples:
    cid = s["case_id"]
    out = sample_outputs.get(cid)
    if not out:
        continue
    st = out["deletion_status"]
    steps = out["steps"]
    phases = [step.get("phase") for step in steps]
    ops = [f"{step.get('system_id')}:{step.get('operation')}:{step.get('resource_id')}" for step in steps]
    evs = set(step.get("evidence_id") for step in steps if step.get("evidence_id"))
    print(f"\n{cid} | {s['email']} | {st} | {len(steps)} steps | evs={evs}")
    for step in steps:
        print(f"  [{step['step_no']}] {step['phase']} | {step['system_id']} | {step['resource_id']} | {step['operation']} | {step['state']} | ev={step['evidence_id']}")
