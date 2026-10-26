import csv
import json

samples = list(csv.DictReader(open('dataset/sample_deletion_requests.csv', encoding='utf-8')))
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open('dataset/sample_output.csv', encoding='utf-8'))}

print(f"{'Case':<8} {'Status':<12} {'Steps':<6} {'Findings':<10} {'Remediations':<12} {'Verifications'}")
print("-" * 70)
for s in samples:
    cid = s['case_id']
    st, steps = outputs[cid]
    findings = [st['operation'] for st in steps if st['phase'] == 'FINDING']
    rems = [st['operation'] for st in steps if st['phase'] == 'REMEDIATION']
    vers = [st['operation'] for st in steps if st['phase'] == 'VERIFICATION']
    print(f"{cid:<8} {st:<12} {len(steps):<6} {len(findings):<10} {len(rems):<12} {len(vers)}")
    if findings:
        for f in steps:
            if f['phase'] == 'FINDING':
                print(f"   FINDING: {f['system_id']} {f['resource_id']} {f['operation']} ev={f['evidence_id']}")
    else:
        for v in steps:
            print(f"   VERIF: {v['system_id']} {v['resource_id']} {v['operation']} ev={v['evidence_id']}")
