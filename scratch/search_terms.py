import os

def search_text(term):
    print(f"=== Searching for {term} ===")
    for root, dirs, files in os.walk('dataset'):
        for f in files:
            p = os.path.join(root, f)
            if p.endswith('.csv') and 'sample_output' in p:
                continue
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                    for lno, line in enumerate(fp, 1):
                        if term in line:
                            print(f"{p}:{lno}: {line.strip()[:150]}")
            except Exception as e:
                pass

search_text('6645')
search_text('5569')
search_text('4902')
