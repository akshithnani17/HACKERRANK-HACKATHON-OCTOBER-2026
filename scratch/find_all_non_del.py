import csv
import re

with open('dataset/deletion_requests.csv', encoding='utf-8') as f:
    requests = list(csv.DictReader(f))

# Check every request text
non_del = []
for r in requests:
    txt = r['request_text']
    # Check if text does NOT contain words like delete, erase, remove, close, suppression, exclusao, etc.
    # or explicitly says "do not delete", "don't delete", "keep", "not a request to erase", etc.
    is_non_del = False
    lower_txt = txt.lower()
    
    # Check indicators of non-deletion
    if any(phrase in lower_txt for phrase in [
        "don't delete", "do not delete", "do not close", "leave my profile", 
        "not a request to erase", "continue using the service", "replace it with the new",
        "misspelled", "portable format", "stop the promotional emails", "marketing lists only"
    ]):
        is_non_del = True
    
    if is_non_del:
        non_del.append((r['case_id'], r['reported_status'], r['email'], txt))

print(f"Detected {len(non_del)} non-deletion requests:")
for cid, st, email, txt in non_del:
    print(f"  {cid}: {txt}")
