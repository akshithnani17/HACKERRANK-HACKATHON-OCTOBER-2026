import csv
from datetime import datetime

activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))
worker_acts = [a for a in activities if a['source_system'] == 'deletion_worker']

# Check cases 26, 27, 28, 29, 30
cases_data = {
    'case_26': {'acc': 'account_5684', 'aux': {'backup_3120', 'data_flow_6244', 'support_4715'}},
    'case_27': {'acc': 'account_3866', 'aux': {'data_flow_2295', 'backup_5970', 'support_4707'}},
    'case_28': {'acc': 'account_5482', 'aux': {'support_2351', 'backup_838', 'data_flow_2337'}},
    'case_29': {'acc': 'account_7012', 'aux': {'analytics_5208', 'data_flow_3827', 'search_1993', 'support_5281'}},
    'case_30': {'acc': 'account_4163', 'aux': {'search_9359', 'support_6477', 'data_flow_8524', 'analytics_3697'}},
}

for cname, d in cases_data.items():
    acc_act = [a for a in worker_acts if a['resource_id'] == d['acc']][0]
    acc_time = acc_act['event_time']
    print(f"\n{cname}: acc={d['acc']} at {acc_time}")
    for a in worker_acts:
        if a['resource_id'] in d['aux']:
            print(f"   aux {a['resource_id']} at {a['event_time']} ({a['target_system']})")
