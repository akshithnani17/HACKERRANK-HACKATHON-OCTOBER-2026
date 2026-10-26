import csv

activities = list(csv.DictReader(open('dataset/system_activity.csv', encoding='utf-8')))

def show_around(res):
    print(f"=== Operations around {res} ===")
    idx = -1
    for i, a in enumerate(activities):
        if a['resource_id'] == res:
            idx = i
            break
    if idx != -1:
        for j in range(max(0, idx - 5), min(len(activities), idx + 6)):
            a = activities[j]
            print(f"  {a['activity_id']} | {a['event_time']} | {a['event_type']} | {a['target_system']} | {a['resource_id']} | {a['reported_result']}")

show_around('support_4715')
show_around('support_4707')
show_around('support_2351')
show_around('support_5281')
show_around('support_6477')
show_around('tombstone_440')
show_around('tombstone_9178')
