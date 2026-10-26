import csv

ev_map = {r['file_id']: r for r in csv.DictReader(open('dataset/evidence_files.csv', encoding='utf-8'))}
for eid in ['evidence_01', 'evidence_03', 'evidence_05', 'evidence_51', 'evidence_54', 'evidence_56', 'evidence_57', 'evidence_58', 'evidence_59', 'evidence_61', 'evidence_92', 'evidence_93', 'evidence_94']:
    r = ev_map[eid]
    print(f"{eid}: captured_at={r['captured_at']}, origin={r['origin']}, path={r['file_path']}")
