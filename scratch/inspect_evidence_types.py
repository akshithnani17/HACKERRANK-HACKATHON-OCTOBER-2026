import csv
import os

repo_root = r"c:\Users\Akash\Desktop\hacker rank oct hackathon"
dataset_dir = os.path.join(repo_root, "dataset")

with open(os.path.join(dataset_dir, "evidence_files.csv"), encoding="utf-8") as f:
    evidence_files = list(csv.DictReader(f))

print(f"Total evidence files: {len(evidence_files)}")

# Group by extension / category
extensions = {}
for ef in evidence_files:
    ext = os.path.splitext(ef['file_path'])[1].lower()
    extensions.setdefault(ext, []).append(ef)

for ext, files in extensions.items():
    print(f"Extension {ext}: {len(files)} files")
    for f in files[:3]:
        print(f"  {f['file_id']} | {f['captured_at']} | {f['file_path']}")
