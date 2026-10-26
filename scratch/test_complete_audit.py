import os
import sys
import csv
import json
import sqlite3
import re
from datetime import datetime
import pypdf

class UnifiedAuditEngine:
    def __init__(self, dataset_dir):
        self.dataset_dir = dataset_dir
        self.load_identities()
        self.load_manifest()

    def load_identities(self):
        self.email_to_uid = {}
        self.uid_to_emails = {}
        self.uid_to_names = {}
        self.identities = {}

        with open(os.path.join(self.dataset_dir, "user_identities.csv"), encoding="utf-8") as f:
            for r in csv.DictReader(f):
                uid = r["user_id"]
                em = r["email"].lower()
                self.identities[uid] = r
                self.email_to_uid[em] = uid
                self.uid_to_emails.setdefault(uid, set()).add(em)
                if r.get("name"):
                    self.uid_to_names.setdefault(uid, set()).add(r["name"].lower())

        with open(os.path.join(self.dataset_dir, "user_audit_log.csv"), encoding="utf-8") as f:
            for r in csv.DictReader(f):
                uid = r["user_id"]
                fn = r["field_name"]
                if fn == "email":
                    oem = r["old_value"].lower()
                    nem = r["new_value"].lower()
                    self.email_to_uid[oem] = uid
                    self.email_to_uid[nem] = uid
                    self.uid_to_emails.setdefault(uid, set()).add(oem)
                    self.uid_to_emails.setdefault(uid, set()).add(nem)

    def load_manifest(self):
        with open(os.path.join(self.dataset_dir, "evidence_files.csv"), encoding="utf-8") as f:
            self.manifest = list(csv.DictReader(f))
        for m in self.manifest:
            m["dt"] = datetime.fromisoformat(m["captured_at"].replace("Z", "+00:00"))
        self.manifest.sort(key=lambda x: x["dt"])

    def is_deletion_request(self, text):
        t = text.lower()
        non_del = [
            "export my data", "download my personal data", "send me a copy of my data",
            "export of all my data", "opt out of marketing", "unsubscribe",
            "remove me from your marketing lists", "stop sending promotional",
            "update my phone number", "correct my phone number", "change my email",
            "update my email", "access my personal information", "what data do you store",
            "copy of my personal data", "cannot log in", "can't access my profile",
            "reset my password", "help accessing my account", "leave the account active",
            "do not close the account", "keep the account as it is", "without removing any of my records",
            "leave my profile and purchase history in place", "want to continue using the service",
            "don't delete or change anything", "not asking for deletion", "misspelled on the account"
        ]
        for nd in non_del:
            if nd in t:
                return False
        return True

    def audit_case(self, case_id, email, requested_at, reported_status, reported_at, audit_at, request_text):
        if not self.is_deletion_request(request_text):
            return "NOT_APPLICABLE", "[]"

        uid = self.email_to_uid.get(email.lower())
        user_emails = self.uid_to_emails.get(uid, {email.lower()}) if uid else {email.lower()}
        user_names = self.uid_to_names.get(uid, set()) if uid else set()

        audit_dt = datetime.fromisoformat(audit_at.replace("Z", "+00:00"))
        valid_evs = [e for e in self.manifest if e["dt"] <= audit_dt]

        findings = []
        verifs = []
        resources_seen = set()

        for ev in valid_evs:
            fid = ev["file_id"]
            p = os.path.join(self.dataset_dir, ev["file_path"])
            if not os.path.exists(p):
                continue

            # 1. Pipe-delimited text
            if p.endswith(".txt"):
                with open(p, encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if any(em in line.lower() for em in user_emails) or (uid and uid in line):
                            parts = [pt.strip() for pt in line.split("|")]
                            if len(parts) >= 6:
                                # timestamp | system_id | resource_id | record_type | status | email
                                sys_id = parts[1]
                                res_id = parts[2]
                                status = parts[4].upper()
                                if (sys_id, res_id) in resources_seen:
                                    continue
                                if status in ["FOUND", "ACTIVE", "IDENTIFIABLE"]:
                                    if status == "ACTIVE":
                                        findings.append((sys_id, res_id, "REPORT_ACTIVE_DATA_FLOW", "ACTIVE", fid))
                                    elif status == "IDENTIFIABLE":
                                        findings.append((sys_id, res_id, "REPORT_EXPOSED_PII", "PRESENT", fid))
                                    else:
                                        findings.append((sys_id, res_id, "REPORT_REMAINING_RECORD", "PRESENT", fid))
                                    resources_seen.add((sys_id, res_id))
                                elif status in ["NOT_FOUND", "DISABLED", "ANONYMIZED", "REDACTED"]:
                                    if status == "DISABLED":
                                        verifs.append((sys_id, res_id, "VERIFY_DATA_FLOW_DISABLED", "DISABLED", fid))
                                    elif status == "ANONYMIZED":
                                        verifs.append((sys_id, res_id, "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED", fid))
                                    elif status == "REDACTED":
                                        verifs.append((sys_id, res_id, "VERIFY_RECORD_REDACTED", "REDACTED", fid))
                                    else:
                                        verifs.append((sys_id, res_id, "VERIFY_RECORD_ABSENT", "ABSENT", fid))
                                    resources_seen.add((sys_id, res_id))

            # 2. PDF
            elif p.endswith(".pdf"):
                try:
                    reader = pypdf.PdfReader(p)
                    t = "".join(page.extract_text() for page in reader.pages)
                    if any(em in t.lower() for em in user_emails) or any(nm in t.lower() for nm in user_names):
                        m_sup = re.search(r"\b(support_\d+)\b", t)
                        if m_sup:
                            rid = m_sup.group(1)
                            if ("support_platform", rid) not in resources_seen:
                                findings.append(("support_platform", rid, "REPORT_REMAINING_RECORD", "PRESENT", fid))
                                resources_seen.add(("support_platform", rid))
                except: pass

            # 3. JSON
            elif p.endswith(".json"):
                try:
                    with open(p, encoding="utf-8") as f:
                        data = json.load(f)

                    # Export jobs
                    records = data.get("records") or data.get("export_jobs") or []
                    for rec in records:
                        if rec.get("customer_reference") == uid or (rec.get("owner_email") and rec.get("owner_email").lower() in user_emails):
                            rid = rec.get("resource_id")
                            if ("export_service", rid) not in resources_seen:
                                findings.append(("export_service", rid, "REPORT_REMAINING_RECORD", "PRESENT", fid))
                                resources_seen.add(("export_service", rid))

                    # Service exports
                    if "service_exports" in data:
                        sexp = data["service_exports"]
                        if "account_service" in sexp:
                            for lk in sexp["account_service"].get("profile_lookups", []):
                                prof = lk.get("profile") or {}
                                if lk.get("customer_reference") == uid or prof.get("customer_reference") == uid or (lk.get("email") and lk.get("email").lower() in user_emails) or (prof.get("email") and prof.get("email").lower() in user_emails):
                                    rid = lk.get("resource_id")
                                    if ("account_service", rid) not in resources_seen:
                                        if lk.get("status_code") == 200 or lk.get("http_status") == 200 or lk.get("rows", 0) > 0:
                                            findings.append(("account_service", rid, "REPORT_REMAINING_RECORD", "PRESENT", fid))
                                        else:
                                            verifs.append(("account_service", rid, "VERIFY_RECORD_ABSENT", "ABSENT", fid))
                                        resources_seen.add(("account_service", rid))

                        if "search_service" in sexp:
                            for q in sexp["search_service"].get("index_queries", []):
                                if q.get("query") and q.get("query").lower() in user_emails:
                                    rid = q.get("resource_id")
                                    if ("search_service", rid) not in resources_seen:
                                        hits = q.get("hits", {})
                                        if hits.get("total", 0) > 0:
                                            findings.append(("search_service", rid, "REPORT_REMAINING_RECORD", "PRESENT", fid))
                                        else:
                                            verifs.append(("search_service", rid, "VERIFY_RECORD_ABSENT", "ABSENT", fid))
                                        resources_seen.add(("search_service", rid))

                        if "support_platform" in sexp:
                            for t in sexp["support_platform"].get("tickets", []):
                                if t.get("customer_reference") == uid or (t.get("requester_email") and t.get("requester_email").lower() in user_emails):
                                    rid = t.get("resource_id")
                                    if ("support_platform", rid) not in resources_seen:
                                        if any(t.get(k) for k in ["requester_name", "requester_email", "requester_phone"]):
                                            findings.append(("support_platform", rid, "REPORT_EXPOSED_PII", "PRESENT", fid))
                                        else:
                                            verifs.append(("support_platform", rid, "VERIFY_RECORD_REDACTED", "REDACTED", fid))
                                        resources_seen.add(("support_platform", rid))

                        if "analytics_platform" in sexp:
                            for ap in sexp["analytics_platform"].get("profiles", []):
                                if ap.get("customer_reference") == uid or (ap.get("email") and ap.get("email").lower() in user_emails):
                                    rid = ap.get("resource_id")
                                    if ("analytics_platform", rid) not in resources_seen:
                                        if any(ap.get(k) for k in ["email", "phone", "email_hash"]):
                                            findings.append(("analytics_platform", rid, "REPORT_EXPOSED_PII", "PRESENT", fid))
                                        else:
                                            verifs.append(("analytics_platform", rid, "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED", fid))
                                        resources_seen.add(("analytics_platform", rid))

                        if "integration_service" in sexp:
                            for c in sexp["integration_service"].get("connectors", []):
                                if c.get("customer_reference") == uid or (c.get("customer_email") and c.get("customer_email").lower() in user_emails):
                                    rid = c.get("resource_id")
                                    if ("integration_service", rid) not in resources_seen:
                                        if c.get("enabled") is True or str(c.get("enabled")).lower() == "true":
                                            findings.append(("integration_service", rid, "REPORT_ACTIVE_DATA_FLOW", "ACTIVE", fid))
                                        else:
                                            verifs.append(("integration_service", rid, "VERIFY_DATA_FLOW_DISABLED", "DISABLED", fid))
                                        resources_seen.add(("integration_service", rid))

                        if "backup_service" in sexp:
                            for b in sexp["backup_service"].get("restore_entries", []):
                                if b.get("customer_reference") == uid or (b.get("customer_email") and b.get("customer_email").lower() in user_emails):
                                    rid = b.get("resource_id")
                                    if ("backup_service", rid) not in resources_seen:
                                        if b.get("restore_allowed") is True or str(b.get("restore_allowed")).lower() == "true":
                                            findings.append(("backup_service", rid, "REPORT_RESTORE_RISK", "ACTIVE", fid))
                                        else:
                                            verifs.append(("backup_service", rid, "VERIFY_RESTORE_BLOCKED", "BLOCKED", fid))
                                        resources_seen.add(("backup_service", rid))

                        if "export_service" in sexp:
                            for e in sexp["export_service"].get("exports", []):
                                if e.get("customer_reference") == uid or (e.get("owner_email") and e.get("owner_email").lower() in user_emails):
                                    rid = e.get("resource_id")
                                    if ("export_service", rid) not in resources_seen:
                                        findings.append(("export_service", rid, "REPORT_REMAINING_RECORD", "PRESENT", fid))
                                        resources_seen.add(("export_service", rid))

                    # Snapshots
                    if "snapshots" in data:
                        for snap in data["snapshots"]:
                            ds = snap.get("data_store")
                            for rec in snap.get("records", []):
                                if rec.get("subject_reference") == uid or rec.get("customer_reference") == uid:
                                    rid = rec.get("resource_id")
                                    if (ds, rid) not in resources_seen:
                                        if ds == "identity_service":
                                            if any(rec.get(k) for k in ["name", "email", "phone", "email_hash"]):
                                                findings.append((ds, rid, "REPORT_EXPOSED_PII", "PRESENT", fid))
                                            else:
                                                verifs.append((ds, rid, "VERIFY_RECORD_REDACTED", "REDACTED", fid))
                                        elif ds == "account_service":
                                            if rec.get("account_status") == "ACTIVE":
                                                findings.append((ds, rid, "REPORT_REMAINING_RECORD", "PRESENT", fid))
                                            else:
                                                verifs.append((ds, rid, "VERIFY_RECORD_ABSENT", "ABSENT", fid))
                                        resources_seen.add((ds, rid))
                except: pass

            # 4. SQL
            elif p.endswith(".sql"):
                conn = sqlite3.connect(":memory:")
                with open(p, encoding="utf-8") as f:
                    conn.executescript(f.read())
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [r[0] for r in cur.fetchall()]

                for t in tables:
                    cur.execute(f"PRAGMA table_info({t});")
                    cols = {c[1]: c[0] for c in cur.fetchall()}

                    if ("user_id" in cols or "customer_reference" in cols) and "account_status" in cols:
                        ucol = "user_id" if "user_id" in cols else "customer_reference"
                        cur.execute(f"SELECT resource_id, {ucol}, email, account_status FROM {t};")
                        for rid, uref, em, st in cur.fetchall():
                            if uref == uid or (em and em.lower() in user_emails):
                                if ("account_service", rid) not in resources_seen:
                                    if st == "ACTIVE":
                                        findings.append(("account_service", rid, "REPORT_REMAINING_RECORD", "PRESENT", fid))
                                    else:
                                        verifs.append(("account_service", rid, "VERIFY_RECORD_ABSENT", "ABSENT", fid))
                                    resources_seen.add(("account_service", rid))

                    if "source_resource_id" in cols and "email" in cols:
                        cur.execute(f"SELECT resource_id, email FROM {t};")
                        for rid, em in cur.fetchall():
                            if em and em.lower() in user_emails:
                                if ("search_service", rid) not in resources_seen:
                                    findings.append(("search_service", rid, "REPORT_REMAINING_RECORD", "PRESENT", fid))
                                    resources_seen.add(("search_service", rid))

                    if "backup_restore_entries" in t or ("archive_key" in cols and "restore_allowed" in cols):
                        cur.execute(f"SELECT resource_id, customer_reference, customer_email, restore_allowed FROM {t};")
                        for rid, cref, cem, ra in cur.fetchall():
                            if cref == uid or (cem and cem.lower() in user_emails):
                                if ("backup_service", rid) not in resources_seen:
                                    if ra == 1 or str(ra).lower() in ["true", "1"]:
                                        findings.append(("backup_service", rid, "REPORT_RESTORE_RISK", "ACTIVE", fid))
                                    else:
                                        verifs.append(("backup_service", rid, "VERIFY_RESTORE_BLOCKED", "BLOCKED", fid))
                                    resources_seen.add(("backup_service", rid))

            # 5. Log files
            elif p.endswith(".log"):
                trace_to_user = {}
                with open(p, encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                for line in lines:
                    m_tr = re.search(r'trace_id[:=]"?([a-zA-Z0-9_\-]+)"?', line)
                    if m_tr:
                        tr = m_tr.group(1)
                        if any(em in line.lower() for em in user_emails) or (uid and uid in line):
                            trace_to_user[tr] = uid
                for line in lines:
                    m_tr = re.search(r'trace_id[:=]"?([a-zA-Z0-9_\-]+)"?', line)
                    if m_tr and m_tr.group(1) in trace_to_user:
                        m_res = re.search(r'\b(support_\d+|search_\d+|analytics_\d+|data_flow_\d+|backup_\d+)\b', line)
                        m_sys = re.search(r'service[ =":]+([a-zA-Z0-9_]+)', line)
                        if m_res:
                            rid = m_res.group(1)
                            sid = m_sys.group(1) if m_sys else "support_platform"
                            if sid == "support_replica": sid = "support_platform"
                            if (sid, rid) not in resources_seen:
                                if "marker_found=false" in line or "rows=1" in line or "total_hits=1" in line or "hit" in line:
                                    findings.append((sid, rid, "REPORT_REMAINING_RECORD", "PRESENT", fid))
                                else:
                                    verifs.append((sid, rid, "VERIFY_RECORD_ABSENT", "ABSENT", fid))
                                resources_seen.add((sid, rid))

        is_complete = len(findings) == 0
        status = "COMPLETE" if is_complete else "INCOMPLETE"

        # Build steps
        steps = []
        step_no = 1
        
        op_order = {
            "REPORT_REMAINING_RECORD": 1, "REPORT_EXPOSED_PII": 2, "REPORT_ACTIVE_DATA_FLOW": 3, "REPORT_RESTORE_RISK": 4,
            "DISABLE_DATA_FLOW": 1, "BLOCK_RESTORE": 2, "DELETE_RECORD": 3, "REDACT_RECORD": 4, "ANONYMIZE_RECORD": 5,
            "VERIFY_RECORD_ABSENT": 1, "VERIFY_RECORD_PRESENT": 2, "VERIFY_RECORD_REDACTED": 3, "VERIFY_RECORD_ANONYMIZED": 4,
            "VERIFY_DATA_FLOW_DISABLED": 5, "VERIFY_RESTORE_BLOCKED": 6
        }

        if is_complete:
            verifs.sort(key=lambda x: (x[0], x[1]))
            for sid, rid, op, st, fid in verifs:
                steps.append({
                    "step_no": step_no,
                    "phase": "VERIFICATION",
                    "system_id": sid,
                    "resource_id": rid,
                    "operation": op,
                    "state": st,
                    "evidence_id": fid
                })
                step_no += 1
        else:
            findings.sort(key=lambda x: (op_order.get(x[2], 99), x[0], x[1]))
            for sid, rid, op, st, fid in findings:
                steps.append({
                    "step_no": step_no,
                    "phase": "FINDING",
                    "system_id": sid,
                    "resource_id": rid,
                    "operation": op,
                    "state": st,
                    "evidence_id": fid
                })
                step_no += 1

            remediations = []
            future_verifs = []
            for sid, rid, op, st, fid in findings:
                if op == "REPORT_ACTIVE_DATA_FLOW":
                    remediations.append((sid, rid, "DISABLE_DATA_FLOW", "DISABLED"))
                    future_verifs.append((sid, rid, "VERIFY_DATA_FLOW_DISABLED", "DISABLED"))
                elif op == "REPORT_RESTORE_RISK":
                    remediations.append((sid, rid, "BLOCK_RESTORE", "BLOCKED"))
                    future_verifs.append((sid, rid, "VERIFY_RESTORE_BLOCKED", "BLOCKED"))
                elif op == "REPORT_REMAINING_RECORD":
                    remediations.append((sid, rid, "DELETE_RECORD", "ABSENT"))
                    future_verifs.append((sid, rid, "VERIFY_RECORD_ABSENT", "ABSENT"))
                elif op == "REPORT_EXPOSED_PII":
                    if sid == "analytics_platform":
                        remediations.append((sid, rid, "ANONYMIZE_RECORD", "ANONYMIZED"))
                        future_verifs.append((sid, rid, "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED"))
                    else:
                        remediations.append((sid, rid, "REDACT_RECORD", "REDACTED"))
                        future_verifs.append((sid, rid, "VERIFY_RECORD_REDACTED", "REDACTED"))

            remediations.sort(key=lambda x: (op_order.get(x[2], 99), x[0], x[1]))
            for sid, rid, op, st in remediations:
                steps.append({
                    "step_no": step_no,
                    "phase": "REMEDIATION",
                    "system_id": sid,
                    "resource_id": rid,
                    "operation": op,
                    "state": st,
                    "evidence_id": ""
                })
                step_no += 1

            future_verifs.sort(key=lambda x: (op_order.get(x[2], 99), x[0], x[1]))
            for sid, rid, op, st in future_verifs:
                steps.append({
                    "step_no": step_no,
                    "phase": "VERIFICATION",
                    "system_id": sid,
                    "resource_id": rid,
                    "operation": op,
                    "state": st,
                    "evidence_id": ""
                })
                step_no += 1

        return status, json.dumps(steps)

if __name__ == "__main__":
    engine = UnifiedAuditEngine("dataset")
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

    with open("scratch/unified_sample_preds.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["case_id", "deletion_status", "steps_json"])
        w.writeheader()
        w.writerows(results)

    import subprocess
    subprocess.run(["python", "code/evaluation/main.py", "scratch/unified_sample_preds.csv", "dataset/sample_output.csv"], check=True)
