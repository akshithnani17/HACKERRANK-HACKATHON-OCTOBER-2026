import subprocess
import csv
import json
import os

repo_root = r"c:\Users\Akash\Desktop\hacker rank oct hackathon"
sample_in = os.path.join(repo_root, "dataset/sample_deletion_requests.csv")
sample_out = os.path.join(repo_root, "scratch/test_sample_output.csv")
golden_out = os.path.join(repo_root, "dataset/sample_output.csv")

# Run main.py on sample_deletion_requests.csv
res = subprocess.run(["python", "code/main.py", sample_in, sample_out], capture_output=True, text=True, cwd=repo_root)
print("Main.py STDOUT:", res.stdout)
if res.stderr:
    print("Main.py STDERR:", res.stderr)

# Compare test_sample_output.csv with golden_out
predicted = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open(sample_out, encoding='utf-8'))}
actual = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open(golden_out, encoding='utf-8'))}

status_correct = 0
exact_steps_match = 0

for cid, (act_st, act_steps) in actual.items():
    pred_st, pred_steps = predicted[cid]
    if pred_st == act_st:
        status_correct += 1
    if pred_st == act_st and pred_steps == act_steps:
        exact_steps_match += 1
    else:
        print(f"\n--- Mismatch in {cid} ---")
        print(f"Status: actual={act_st}, pred={pred_st}")
        print(f"Actual steps count: {len(act_steps)}, Pred steps count: {len(pred_steps)}")
        if pred_st != act_st:
            print("  Status differed!")
        # check steps diff
        act_res = [(s['phase'], s['system_id'], s['resource_id'], s['operation']) for s in act_steps]
        pred_res = [(s['phase'], s['system_id'], s['resource_id'], s['operation']) for s in pred_steps]
        if act_res != pred_res:
            print(f"  Actual: {act_res}")
            print(f"  Pred:   {pred_res}")

print(f"\nEvaluation on 32 samples:")
print(f"Status accuracy: {status_correct} / {len(actual)} ({status_correct/len(actual)*100:.1f}%)")
print(f"Exact steps match: {exact_steps_match} / {len(actual)} ({exact_steps_match/len(actual)*100:.1f}%)")
