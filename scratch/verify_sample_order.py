import csv
import json

PHASE_ORDER = {"FINDING": 1, "REMEDIATION": 2, "VERIFICATION": 3}
OP_ORDER = {
    # Findings
    "REPORT_REMAINING_RECORD": 1,
    "REPORT_EXPOSED_PII": 2,
    "REPORT_ACTIVE_DATA_FLOW": 3,
    "REPORT_RESTORE_RISK": 4,
    # Remediation
    "DISABLE_DATA_FLOW": 1,
    "BLOCK_RESTORE": 2,
    "DELETE_RECORD": 3,
    "REDACT_RECORD": 4,
    "ANONYMIZE_RECORD": 5,
    # Verification
    "VERIFY_RECORD_ABSENT": 1,
    "VERIFY_RECORD_PRESENT": 2,
    "VERIFY_RECORD_REDACTED": 3,
    "VERIFY_RECORD_ANONYMIZED": 4,
    "VERIFY_DATA_FLOW_DISABLED": 5,
    "VERIFY_RESTORE_BLOCKED": 6,
}

def step_sort_key(step):
    return (
        PHASE_ORDER[step['phase']],
        OP_ORDER[step['operation']],
        step['system_id'],
        step['resource_id']
    )

samples = list(csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8')))
all_sorted = True
for s in samples:
    steps = json.loads(s['steps_json'])
    sorted_steps = sorted(steps, key=step_sort_key)
    # Check if original steps match sorted steps (ignoring step_no)
    orig_keys = [step_sort_key(st) for st in steps]
    sort_keys = [step_sort_key(st) for st in sorted_steps]
    if orig_keys != sort_keys:
        print(f"Mismatch in order for {s['case_id']}!")
        all_sorted = False

if all_sorted:
    print("ALL 32 sample cases strictly adhere to this exact sort key!")
else:
    print("Some sample cases differed in order.")
