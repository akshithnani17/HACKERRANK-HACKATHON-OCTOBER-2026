import csv
from datetime import datetime

with open('dataset/deletion_requests.csv', encoding='utf-8') as f:
    requests = list(csv.DictReader(f))

# Match requests whose requested_at or reported_at is close to the event times
times = [
    '2026-08-28T11:07:25Z', '2026-08-29T10:47:38Z', '2026-08-30T10:58:51Z', '2026-09-03T11:09:05Z',
    '2026-09-04T10:49:18Z', '2026-09-05T11:00:31Z', '2026-09-09T11:11:44Z', '2026-09-10T10:51:57Z',
    '2026-09-11T11:02:11Z', '2026-09-13T10:56:12Z'
]

for t in times:
    dt = datetime.fromisoformat(t.replace('Z', '+00:00'))
    print(f"\n--- Around {t} ---")
    for r in requests:
        # compare requested_at and reported_at
        r_dt = datetime.fromisoformat(r['reported_at'].replace('Z', '+00:00'))
        diff = abs((r_dt - dt).total_seconds())
        if diff < 3600 * 24: # within 1 day
            print(f"  {r['case_id']} | reported_at: {r['reported_at']} (diff={diff}s) | email: {r['email']} | text: {r['request_text']}")
