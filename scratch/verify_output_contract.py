import csv
import json
import os

repo_root = r"c:\Users\Akash\Desktop\hacker rank oct hackathon"
output_path = os.path.join(repo_root, "output.csv")

with open(output_path, encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    assert header == ["case_id", "deletion_status", "steps_json"], f"Header mismatch: {header}"
    rows = list(reader)

print(f"Total output rows: {len(rows)}")
assert len(rows) == 518, f"Expected 518 rows, got {len(rows)}"

case_ids = [r[0] for r in rows]
assert case_ids == sorted(case_ids), "Rows are not sorted by case_id!"

status_counts = {}
for idx, r in enumerate(rows, 1):
    cid, status, steps_raw = r
    assert status in ["COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"], f"Invalid status: {status} in row {idx}"
    status_counts[status] = status_counts.get(status, 0) + 1
    
    steps = json.loads(steps_raw)
    assert isinstance(steps, list), f"steps_json is not a list in row {idx}"
    
    if status == "NOT_APPLICABLE":
        assert len(steps) == 0, f"NOT_APPLICABLE must have empty steps_json in row {idx}"
    else:
        # Check consecutive 1-based step_no
        for s_idx, st in enumerate(steps, 1):
            assert st["step_no"] == s_idx, f"Step numbering not consecutive in {cid}: {st['step_no']} vs {s_idx}"
            assert st["phase"] in ["FINDING", "REMEDIATION", "VERIFICATION"], f"Invalid phase in {cid}"
            
        # Check phase ordering: FINDING -> REMEDIATION -> VERIFICATION
        phases = [st["phase"] for st in steps]
        phase_ranks = [{"FINDING": 1, "REMEDIATION": 2, "VERIFICATION": 3}[p] for p in phases]
        assert phase_ranks == sorted(phase_ranks), f"Phases out of order in {cid}: {phases}"

print("\n--- OUTPUT.CSV VALIDATION PASSED 100% ---")
print(f"Status distribution across 518 cases:")
for st, cnt in sorted(status_counts.items()):
    print(f"  {st:<16}: {cnt} ({cnt/518*100:.1f}%)")
