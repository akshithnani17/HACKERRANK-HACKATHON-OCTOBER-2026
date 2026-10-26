import csv
import json
import os

repo_root = r"c:\Users\Akash\Desktop\hacker rank oct hackathon"
dataset_dir = os.path.join(repo_root, "dataset")

outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open(os.path.join(dataset_dir, 'sample_output.csv'), encoding='utf-8'))}

# For every sample case, check each unique resource_id and find which evidence files or system_activity contain it
for cid, (st, steps) in list(outputs.items()):
    unique_res = set(s['resource_id'] for s in steps)
    print(f"\n=== {cid} ({st}) Resources: {unique_res} ===")
    for res in sorted(unique_res):
        sources = []
        for root, dirs, files in os.walk(os.path.join(dataset_dir, 'evidence')):
            for f in files:
                p = os.path.join(root, f)
                try:
                    content = open(p, encoding='utf-8', errors='ignore').read()
                    if res in content:
                        sources.append(f)
                except: pass
        # also check system_activity
        act_matches = []
        for a in csv.DictReader(open(os.path.join(dataset_dir, 'system_activity.csv'), encoding='utf-8')):
            if a['resource_id'] == res or res in a['details']:
                act_matches.append(f"{a['event_time']} {a['source_system']} {a['target_system']} {a['reported_result']}")
        print(f"  {res}:")
        print(f"     in evidence: {sources}")
        if act_matches:
            print(f"     in activity: {act_matches[:2]}")
