import os
import sys
import csv
import json
import sqlite3
import re
from datetime import datetime

# Import classes from code/main.py
import importlib.util
spec = importlib.util.spec_from_file_location("main", "code/main.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class EnhancedDeletionAuditEngine(m.DeletionAuditEngine):
    def audit_case(self, case_id, email, requested_at, reported_status, reported_at, audit_at, request_text):
        if not self.is_deletion_request(case_id, request_text):
            return "NOT_APPLICABLE", "[]"

        uid = self.resolver.resolve_user_id(email)
        user_emails = self.resolver.get_emails(uid) if uid else {email.lower()}

        file_id, file_path = self.find_evidence_file(audit_at, uid, user_emails)
        abs_ev_path = os.path.join(self.dataset_dir, file_path)

        findings = []
        verifications = []
        resources_checked = set()

        # Handle SQL evidence
        if abs_ev_path.endswith(".sql") and os.path.exists(abs_ev_path):
            conn = sqlite3.connect(":memory:")
            with open(abs_ev_path, encoding="utf-8") as f:
                conn.executescript(f.read())
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [r[0] for r in cur.fetchall()]

            for t in tables:
                cur.execute(f"PRAGMA table_info({t});")
                cols = {c[1]: c[0] for c in cur.fetchall()}

                # Account profiles
                if ("user_id" in cols or "customer_reference" in cols) and "account_status" in cols:
                    uid_col = "user_id" if "user_id" in cols else "customer_reference"
                    cur.execute(f"SELECT resource_id, {uid_col}, email, account_status FROM {t};")
                    for rid, u_ref, em, status in cur.fetchall():
                        if u_ref == uid or (em and em.lower() in user_emails):
                            if ( "account_service", rid ) in resources_checked:
                                continue
                            if status == "ACTIVE":
                                findings.append(("account_service", rid, "REPORT_REMAINING_RECORD", "PRESENT"))
                            else:
                                verifications.append(("account_service", rid, "VERIFY_RECORD_ABSENT", "ABSENT"))
                            resources_checked.add(("account_service", rid))

                # Search primary
                if "source_resource_id" in cols and "email" in cols:
                    cur.execute(f"SELECT resource_id, email, source_resource_id FROM {t};")
                    for rid, em, srid in cur.fetchall():
                        if em and em.lower() in user_emails:
                            if ("search_service", rid) not in resources_checked:
                                findings.append(("search_service", rid, "REPORT_REMAINING_RECORD", "PRESENT"))
                                resources_checked.add(("search_service", rid))

                # Inventory Search documents
                if "customer_reference" in cols and "display_name" in cols and "index_name" in cols:
                    cur.execute(f"SELECT resource_id, customer_reference, email FROM {t};")
                    for rid, cref, em in cur.fetchall():
                        if cref == uid or (em and em.lower() in user_emails):
                            if ("search_service", rid) not in resources_checked:
                                findings.append(("search_service", rid, "REPORT_REMAINING_RECORD", "PRESENT"))
                                resources_checked.add(("search_service", rid))

                # Inventory Analytics profiles
                if "audience_cohort" in cols and "customer_reference" in cols:
                    cur.execute(f"SELECT resource_id, customer_reference, email, phone, email_hash FROM {t};")
                    for rid, cref, em, ph, eh in cur.fetchall():
                        if cref == uid or (em and em.lower() in user_emails):
                            if ("analytics_platform", rid) not in resources_checked:
                                if any([em, ph, eh]):
                                    findings.append(("analytics_platform", rid, "REPORT_EXPOSED_PII", "PRESENT"))
                                else:
                                    verifications.append(("analytics_platform", rid, "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED"))
                                resources_checked.add(("analytics_platform", rid))

                # Inventory Support records
                if "requester_email" in cols and "message_excerpt" in cols:
                    cur.execute(f"SELECT resource_id, customer_reference, requester_name, requester_email, requester_phone FROM {t};")
                    for rid, cref, rname, rem, rph in cur.fetchall():
                        if cref == uid or (rem and rem.lower() in user_emails):
                            if ("support_platform", rid) not in resources_checked:
                                if any([rname, rem, rph]):
                                    findings.append(("support_platform", rid, "REPORT_EXPOSED_PII", "PRESENT"))
                                else:
                                    verifications.append(("support_platform", rid, "VERIFY_RECORD_REDACTED", "REDACTED"))
                                resources_checked.add(("support_platform", rid))

                # Inventory Exports
                if "object_key" in cols and "customer_reference" in cols:
                    cur.execute(f"SELECT resource_id, customer_reference, owner_email FROM {t};")
                    for rid, cref, oem in cur.fetchall():
                        if cref == uid or (oem and oem.lower() in user_emails):
                            if ("export_service", rid) not in resources_checked:
                                findings.append(("export_service", rid, "REPORT_REMAINING_RECORD", "PRESENT"))
                                resources_checked.add(("export_service", rid))

                # Inventory Connectors
                if "connector_name" in cols and "enabled" in cols:
                    cur.execute(f"SELECT resource_id, customer_reference, customer_email, enabled FROM {t};")
                    for rid, cref, cem, en in cur.fetchall():
                        if cref == uid or (cem and cem.lower() in user_emails):
                            if ("integration_service", rid) not in resources_checked:
                                if en == 1 or str(en).lower() in ["true", "1"]:
                                    findings.append(("integration_service", rid, "REPORT_ACTIVE_DATA_FLOW", "ACTIVE"))
                                else:
                                    verifications.append(("integration_service", rid, "VERIFY_DATA_FLOW_DISABLED", "DISABLED"))
                                resources_checked.add(("integration_service", rid))

                # Inventory Backup
                if "archive_key" in cols and "restore_allowed" in cols:
                    cur.execute(f"SELECT resource_id, customer_reference, customer_email, restore_allowed FROM {t};")
                    for rid, cref, cem, ra in cur.fetchall():
                        if cref == uid or (cem and cem.lower() in user_emails):
                            if ("backup_service", rid) not in resources_checked:
                                if ra == 1 or str(ra).lower() in ["true", "1"]:
                                    findings.append(("backup_service", rid, "REPORT_RESTORE_RISK", "ACTIVE"))
                                else:
                                    verifications.append(("backup_service", rid, "VERIFY_RESTORE_BLOCKED", "BLOCKED"))
                                resources_checked.add(("backup_service", rid))

                # Record JSON tables
                if "record_json" in cols:
                    cur.execute(f"SELECT resource_id, origin_system, collection_name, record_json FROM {t};")
                    for rid, orig, coll, rj in cur.fetchall():
                        if rj and (uid in rj or any(em in rj.lower() for em in user_emails)):
                            try:
                                d = json.loads(rj)
                                if coll == "customer_profiles":
                                    if d.get("account_status") == "ACTIVE":
                                        findings.append(("account_service", rid, "REPORT_REMAINING_RECORD", "PRESENT"))
                                    else:
                                        verifications.append(("account_service", rid, "VERIFY_RECORD_ABSENT", "ABSENT"))
                                    resources_checked.add(("account_service", rid))
                                elif coll == "customer_search_documents":
                                    findings.append(("search_service", rid, "REPORT_REMAINING_RECORD", "PRESENT"))
                                    resources_checked.add(("search_service", rid))
                                elif coll == "customer_analytics_profiles":
                                    if any(d.get(k) for k in ["email", "phone", "email_hash"]):
                                        findings.append(("analytics_platform", rid, "REPORT_EXPOSED_PII", "PRESENT"))
                                    else:
                                        verifications.append(("analytics_platform", rid, "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED"))
                                    resources_checked.add(("analytics_platform", rid))
                            except: pass

        # Include standard JSON/log audit as well
        super_status, super_steps_raw = super().audit_case(case_id, email, requested_at, reported_status, reported_at, audit_at, request_text)
        if super_status == "NOT_APPLICABLE":
            return "NOT_APPLICABLE", "[]"

        super_steps = json.loads(super_steps_raw)
        for s in super_steps:
            if s["phase"] == "FINDING":
                if (s["system_id"], s["resource_id"]) not in resources_checked:
                    findings.append((s["system_id"], s["resource_id"], s["operation"], s["state"]))
                    resources_checked.add((s["system_id"], s["resource_id"]))
            elif s["phase"] == "VERIFICATION":
                if (s["system_id"], s["resource_id"]) not in resources_checked:
                    verifications.append((s["system_id"], s["resource_id"], s["operation"], s["state"]))
                    resources_checked.add((s["system_id"], s["resource_id"]))

        # Build output plan
        is_complete = len(findings) == 0
        status = "COMPLETE" if is_complete else "INCOMPLETE"

        steps = []
        step_no = 1

        if is_complete:
            # Sort verifications: system_id, resource_id
            verifications.sort(key=lambda x: (x[0], x[1]))
            for sys_id, res_id, op, st in verifications:
                steps.append({
                    "step_no": step_no,
                    "phase": "VERIFICATION",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": op,
                    "state": st,
                    "evidence_id": file_id
                })
                step_no += 1
        else:
            # Order findings per OP_ORDER
            def finding_sort_key(item):
                sys_id, res_id, op, st = item
                return (m.OP_ORDER.get(op, 99), sys_id, res_id)
            findings.sort(key=finding_sort_key)

            for sys_id, res_id, op, st in findings:
                steps.append({
                    "step_no": step_no,
                    "phase": "FINDING",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": op,
                    "state": st,
                    "evidence_id": file_id
                })
                step_no += 1

            # Remediation
            # Dependency order: DISABLE_DATA_FLOW, BLOCK_RESTORE, DELETE_RECORD, REDACT_RECORD, ANONYMIZE_RECORD
            remediations = []
            future_verifs = []
            for sys_id, res_id, op, st in findings:
                if op == "REPORT_ACTIVE_DATA_FLOW":
                    remediations.append((sys_id, res_id, "DISABLE_DATA_FLOW", "DISABLED"))
                    future_verifs.append((sys_id, res_id, "VERIFY_DATA_FLOW_DISABLED", "DISABLED"))
                elif op == "REPORT_RESTORE_RISK":
                    remediations.append((sys_id, res_id, "BLOCK_RESTORE", "BLOCKED"))
                    future_verifs.append((sys_id, res_id, "VERIFY_RESTORE_BLOCKED", "BLOCKED"))
                elif op == "REPORT_REMAINING_RECORD":
                    remediations.append((sys_id, res_id, "DELETE_RECORD", "ABSENT"))
                    future_verifs.append((sys_id, res_id, "VERIFY_RECORD_ABSENT", "ABSENT"))
                elif op == "REPORT_EXPOSED_PII":
                    if sys_id == "analytics_platform":
                        remediations.append((sys_id, res_id, "ANONYMIZE_RECORD", "ANONYMIZED"))
                        future_verifs.append((sys_id, res_id, "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED"))
                    else:
                        remediations.append((sys_id, res_id, "REDACT_RECORD", "REDACTED"))
                        future_verifs.append((sys_id, res_id, "VERIFY_RECORD_REDACTED", "REDACTED"))

            def rem_sort_key(item):
                sys_id, res_id, op, st = item
                return (m.OP_ORDER.get(op, 99), sys_id, res_id)
            remediations.sort(key=rem_sort_key)

            for sys_id, res_id, op, st in remediations:
                steps.append({
                    "step_no": step_no,
                    "phase": "REMEDIATION",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": op,
                    "state": st,
                    "evidence_id": ""
                })
                step_no += 1

            # Future verifications
            def ver_sort_key(item):
                sys_id, res_id, op, st = item
                return (m.OP_ORDER.get(op, 99), sys_id, res_id)
            future_verifs.sort(key=ver_sort_key)

            for sys_id, res_id, op, st in future_verifs:
                steps.append({
                    "step_no": step_no,
                    "phase": "VERIFICATION",
                    "system_id": sys_id,
                    "resource_id": res_id,
                    "operation": op,
                    "state": st,
                    "evidence_id": ""
                })
                step_no += 1

        return status, json.dumps(steps)

if __name__ == "__main__":
    engine = EnhancedDeletionAuditEngine("dataset")
    with open("dataset/sample_deletion_requests.csv", encoding="utf-8") as f:
        requests = list(csv.DictReader(f))

    results = []
    for r in requests:
        cid = r["case_id"]
        status, steps_json = engine.audit_case(
            cid, r["email"], r["requested_at"], r["reported_status"],
            r["reported_at"], r["audit_at"], r["request_text"]
        )
        results.append({"case_id": cid, "deletion_status": status, "steps_json": steps_json})

    with open("scratch/enhanced_sample_preds.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["case_id", "deletion_status", "steps_json"])
        w.writeheader()
        w.writerows(results)

    # Evaluate
    import subprocess
    subprocess.run(["python", "code/evaluation/main.py", "scratch/enhanced_sample_preds.csv", "dataset/sample_output.csv"], check=True)
