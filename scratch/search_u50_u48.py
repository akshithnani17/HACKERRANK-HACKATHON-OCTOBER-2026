import os

for uid in ['user_50', 'user_48']:
    print(f"=== Occurrences of {uid} in dataset/evidence ===")
    for root, dirs, files in os.walk('dataset/evidence'):
        for f in files:
            p = os.path.join(root, f)
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                    for lno, line in enumerate(fp, 1):
                        if uid in line:
                            print(f"{p}:{lno}: {line.strip()[:140]}")
            except:
                pass
