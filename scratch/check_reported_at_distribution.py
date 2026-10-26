import csv
from collections import Counter

requests = list(csv.DictReader(open('dataset/deletion_requests.csv', encoding='utf-8')))
samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
all_reqs = samples + requests

rep_counts = Counter(r['reported_at'] for r in all_reqs)
print(f"Total requests: {len(all_reqs)}, unique reported_at: {len(rep_counts)}")
multi_rep = {k: v for k, v in rep_counts.items() if v > 1}
print(f"Reported_at with multiple requests: {len(multi_rep)}")
for k, v in sorted(multi_rep.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  {k}: {v} requests")
