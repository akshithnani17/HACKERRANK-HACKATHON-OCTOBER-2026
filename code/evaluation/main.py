"""
Evaluation Harness for Ghost Data Still Exists
HackerRank Orchestrate (October 2026)

This script evaluates predictions against ground truth (e.g. sample_output.csv)
and generates accuracy metrics across cases, steps, fields, and sequences.
"""

import sys
import os
import csv
import json

def evaluate(predictions_path, ground_truth_path):
    print(f"Loading predictions from: {predictions_path}")
    print(f"Loading ground truth from: {ground_truth_path}")

    with open(predictions_path, encoding="utf-8") as f:
        preds = {r["case_id"]: r for r in csv.DictReader(f)}

    with open(ground_truth_path, encoding="utf-8") as f:
        truths = {r["case_id"]: r for r in csv.DictReader(f)}

    total_cases = len(truths)
    status_matches = 0
    exact_steps_matches = 0

    total_truth_steps = 0
    total_pred_steps = 0
    matching_steps = 0

    field_matches = {
        "step_no": 0,
        "phase": 0,
        "system_id": 0,
        "resource_id": 0,
        "operation": 0,
        "state": 0,
        "evidence_id": 0
    }
    total_step_fields = 0

    sequence_matches = 0

    for cid, truth_row in truths.items():
        pred_row = preds.get(cid)
        if not pred_row:
            continue

        truth_status = truth_row["deletion_status"]
        pred_status = pred_row["deletion_status"]

        if truth_status == pred_status:
            status_matches += 1

        try:
            truth_steps = json.loads(truth_row["steps_json"])
            pred_steps = json.loads(pred_row["steps_json"])
        except Exception as e:
            truth_steps = []
            pred_steps = []

        total_truth_steps += len(truth_steps)
        total_pred_steps += len(pred_steps)

        # Check exact array match
        if truth_status == pred_status and truth_steps == pred_steps:
            exact_steps_matches += 1

        # Check sequence accuracy (ignoring step_no numbers if contents match in order)
        truth_ops = [(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"], s["evidence_id"]) for s in truth_steps]
        pred_ops = [(s["phase"], s["system_id"], s["resource_id"], s["operation"], s["state"], s["evidence_id"]) for s in pred_steps]
        if truth_status == pred_status and truth_ops == pred_ops:
            sequence_matches += 1

        # Step and field level comparison
        for i in range(min(len(truth_steps), len(pred_steps))):
            ts = truth_steps[i]
            ps = pred_steps[i]
            if ts == ps:
                matching_steps += 1
            for k in field_matches:
                total_step_fields += 1
                if ts.get(k) == ps.get(k):
                    field_matches[k] += 1

    case_acc = (status_matches / total_cases) * 100 if total_cases else 0
    step_precision = (matching_steps / total_pred_steps) * 100 if total_pred_steps else 0
    step_recall = (matching_steps / total_truth_steps) * 100 if total_truth_steps else 0
    seq_acc = (sequence_matches / total_cases) * 100 if total_cases else 0

    results = {
        "total_cases": total_cases,
        "status_matches": status_matches,
        "case_status_accuracy": case_acc,
        "exact_case_matches": exact_steps_matches,
        "sequence_matches": sequence_matches,
        "sequence_accuracy": seq_acc,
        "total_truth_steps": total_truth_steps,
        "total_pred_steps": total_pred_steps,
        "matching_steps": matching_steps,
        "step_precision": step_precision,
        "step_recall": step_recall,
        "field_accuracies": {k: (v / total_step_fields * len(field_matches) * 100 if total_step_fields else 0) for k, v in field_matches.items()}
    }

    print("\n" + "=" * 60)
    print("EVALUATION RESULTS SUMMARY")
    print("=" * 60)
    print(f"Total Cases Evaluated:       {total_cases}")
    print(f"Case Deletion Status Accuracy: {case_acc:.2f}% ({status_matches}/{total_cases})")
    print(f"Sequence Accuracy:           {seq_acc:.2f}% ({sequence_matches}/{total_cases})")
    print(f"Exact Case & Steps Match:    {exact_steps_matches}/{total_cases} ({(exact_steps_matches/total_cases)*100:.2f}%)")
    print(f"Step Precision:              {step_precision:.2f}% ({matching_steps}/{total_pred_steps})")
    print(f"Step Recall:                 {step_recall:.2f}% ({matching_steps}/{total_truth_steps})")
    print("-" * 60)
    print("Field-level Accuracies:")
    for k, acc in results["field_accuracies"].items():
        print(f"  {k:<15}: {acc:.2f}%")
    print("=" * 60 + "\n")

    return results

if __name__ == "__main__":
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    pred_path = os.path.join(repo_root, "output.csv")
    truth_path = os.path.join(repo_root, "dataset/sample_output.csv")

    if len(sys.argv) > 1:
        pred_path = sys.argv[1]
    if len(sys.argv) > 2:
        truth_path = sys.argv[2]

    evaluate(pred_path, truth_path)
