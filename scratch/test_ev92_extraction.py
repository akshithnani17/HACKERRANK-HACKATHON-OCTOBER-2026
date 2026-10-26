import csv
import json
import os

dataset_dir = r"c:\Users\Akash\Desktop\hacker rank oct hackathon\dataset"
outputs = {r['case_id']: (r['deletion_status'], json.loads(r['steps_json'])) for r in csv.DictReader(open(os.path.join(dataset_dir, 'sample_output.csv'), encoding='utf-8'))}
samples = {r['case_id']: r for r in csv.DictReader(open(os.path.join(dataset_dir, 'sample_deletion_requests.csv'), encoding='utf-8'))}

identities = {r['user_id']: r for r in csv.DictReader(open(os.path.join(dataset_dir, 'user_identities.csv'), encoding='utf-8'))}
email_to_uid = {r['email'].lower(): r['user_id'] for r in identities.values()}

with open(os.path.join(dataset_dir, 'evidence/records/service_resource_export_20260915_114455.json'), encoding='utf-8') as f:
    ev92 = json.load(f)

for cid in [f"case_{i}" for i in range(21, 31)]:
    req = samples[cid]
    uid = email_to_uid[req['email'].lower()]
    st, steps = outputs[cid]
    print(f"\n--- {cid} ({uid}) Expected: {st} ---")
    
    acc_profiles = ev92['service_exports']['account_service']['profile_lookups']
    for p in acc_profiles:
        if p.get('customer_reference') == uid or (p.get('email') and p.get('email').lower() == req['email'].lower()):
            print("  account_service:", p)
            
    # 2. security_service
    sec_records = ev92['service_exports']['security_service']['audit_records']
    for r in sec_records:
        if r.get('subject_reference') == uid:
            print("  security_service:", r)
            
    # 3. search_service
    search_queries = ev92['service_exports']['search_service']['index_queries']
    for q in search_queries:
        if q.get('query') == req['email'].lower():
            print("  search_service:", q)
            
    # 4. support_platform
    support_tickets = ev92['service_exports']['support_platform']['tickets']
    for t in support_tickets:
        if t.get('customer_reference') == uid or (t.get('requester_email') and t.get('requester_email').lower() == req['email'].lower()):
            print("  support_platform:", t)
            
    # 5. analytics_platform
    analytics_profiles = ev92['service_exports']['analytics_platform']['profiles']
    for a in analytics_profiles:
        if a.get('customer_reference') == uid or (a.get('email') and a.get('email').lower() == req['email'].lower()):
            print("  analytics_platform:", a)
            
    # 6. integration_service
    connectors = ev92['service_exports']['integration_service']['connectors']
    for c in connectors:
        if c.get('customer_reference') == uid or (c.get('customer_email') and c.get('customer_email').lower() == req['email'].lower()):
            print("  integration_service:", c)
            
    # 7. backup_service
    restores = ev92['service_exports']['backup_service']['restore_entries']
    for b in restores:
        if b.get('customer_reference') == uid or (b.get('customer_email') and b.get('customer_email').lower() == req['email'].lower()):
            print("  backup_service:", b)
            
    # 8. export_service
    exports = ev92['service_exports']['export_service']['exports']
    for e in exports:
        if e.get('customer_reference') == uid or (e.get('owner_email') and e.get('owner_email').lower() == req['email'].lower()):
            print("  export_service:", e)
