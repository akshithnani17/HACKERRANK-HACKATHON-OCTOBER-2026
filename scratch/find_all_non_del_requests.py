import csv

requests = list(csv.DictReader(open('dataset/deletion_requests.csv', encoding='utf-8')))

NON_DEL_KEYWORDS = [
    "export my data", "download my personal data", "send me a copy of my data", "export of all my data",
    "opt out of marketing", "unsubscribe", "remove me from your marketing lists", "stop sending promotional",
    "update my phone number", "correct my phone number", "change my email", "update my email",
    "access my personal information", "what data do you store", "copy of my personal data",
    "cannot log in", "reset my password", "help accessing my account"
]

non_del = []
for r in requests:
    t = r['request_text'].lower()
    is_non = False
    for kw in NON_DEL_KEYWORDS:
        if kw in t:
            is_non = True
            break
    if is_non:
        non_del.append((r['case_id'], r['request_text']))

print(f"Total non-deletion requests found: {len(non_del)}")
for cid, txt in non_del:
    print(f"{cid}: {txt[:100]}")
