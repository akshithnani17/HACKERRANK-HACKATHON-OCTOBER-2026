import os
import sys
import csv
import json
import sqlite3
import re
from datetime import datetime
import pypdf

class EvidenceSearcher:
    def __init__(self, dataset_dir):
        self.dataset_dir = dataset_dir
        with open(os.path.join(dataset_dir, "evidence_files.csv"), encoding="utf-8") as f:
            self.manifest = list(csv.DictReader(f))
        for m in self.manifest:
            m["dt"] = datetime.fromisoformat(m["captured_at"].replace("Z", "+00:00"))
        self.manifest.sort(key=lambda x: x["dt"])

    def search_for_user(self, audit_at, uid, emails):
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
                
            # 1. SQL
            if p.endswith(".sql"):
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
                            if uref == uid or (em and em.lower() in emails):
                                if ("account_service", rid) not in resources_seen:
                                    if st == "ACTIVE":
                                        findings.append(("account_service", rid, "REPORT_REMAINING_RECORD", "PRESENT", fid))
                                    else:
                                        verifs.append(("account_service", rid, "VERIFY_RECORD_ABSENT", "ABSENT", fid))
                                    resources_seen.add(("account_service", rid))

                    if "source_resource_id" in cols and "email" in cols: # search primary
                        cur.execute(f"SELECT resource_id, email FROM {t};")
                        for rid, em in cur.fetchall():
                            if em and em.lower() in emails:
                                if ("search_service", rid) not in resources_seen:
                                    findings.append(("search_service", rid, "REPORT_REMAINING_RECORD", "PRESENT", fid))
                                    resources_seen.add(("search_service", rid))

                    if "backup_restore_entries" in t or ("archive_key" in cols and "restore_allowed" in cols):
                        cur.execute(f"SELECT resource_id, customer_reference, customer_email, restore_allowed FROM {t};")
                        for rid, cref, cem, ra in cur.fetchall():
                            if cref == uid or (cem and cem.lower() in emails):
                                if ("backup_service", rid) not in resources_seen:
                                    if ra == 1 or str(ra).lower() in ["true", "1"]:
                                        findings.append(("backup_service", rid, "REPORT_RESTORE_RISK", "ACTIVE", fid))
                                    else:
                                        verifs.append(("backup_service", rid, "VERIFY_RESTORE_BLOCKED", "BLOCKED", fid))
                                    resources_seen.add(("backup_service", rid))

            # 2. PDF
            elif p.endswith(".pdf"):
                try:
                    reader = pypdf.PdfReader(p)
                    text = "".join(page.extract_text() for page in reader.pages)
                    if uid in text or any(em in text.lower() for em in emails):
                        m_sup = re.search(r"\b(support_\d+)\b", text)
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
                    # Check export jobs
                    if "export_jobs" in data:
                        for ej in data["export_jobs"]:
                            if ej.get("customer_reference") == uid or (ej.get("owner_email") and ej.get("owner_email").lower() in emails):
                                rid = ej.get("resource_id")
                                if ("export_service", rid) not in resources_seen:
                                    findings.append(("export_service", rid, "REPORT_REMAINING_RECORD", "PRESENT", fid))
                                    resources_seen.add(("export_service", rid))
                except: pass

            # 4. LOG / TXT
            elif p.endswith((".log", ".txt")):
                with open(p, encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if uid in line or any(em in line.lower() for em in emails):
                            m_sup = re.search(r"\b(support_\d+)\b", line)
                            if m_sup:
                                rid = m_sup.group(1)
                                if ("support_platform", rid) not in resources_seen:
                                    findings.append(("support_platform", rid, "REPORT_REMAINING_RECORD", "PRESENT", fid))
                                    resources_seen.add(("support_platform", rid))

        return findings, verifs

s = EvidenceSearcher("dataset")
# Check case_07
print("Case 07 search:", s.search_for_user("2026-09-12T08:00:00Z", "user_07", {"priya.raman@gmail.com"}))
# Check case_08
print("Case 08 search:", s.search_for_user("2026-09-15T09:00:00Z", "user_08", {"felix.vogel@gmx.de"}))
# Check case_09
print("Case 09 search:", s.search_for_user("2026-09-17T14:15:00Z", "user_09", {"chloe.durand@orange.fr"}))
# Check case_10
print("Case 10 search:", s.search_for_user("2026-09-18T10:00:00Z", "user_10", {"gabriel.silva@uol.com.br"}))
