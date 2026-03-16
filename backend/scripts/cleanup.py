import os

files_to_delete = [
    'test_automated_flow_final.py',
    'check_resources.py',
    'prisma_fields.json',
    'introspect_prisma.py',
    'test_results.txt',
    'test_results_utf8.txt',
    'final_verification_results.txt',
    'final_verification_results_utf8.txt',
    'prisma_dump.txt',
    'test_results_detailed.txt',
    'test_results_detailed_utf8.txt',
    'test_results_v2.txt',
    'test_results_v2_utf8.txt',
    'test_results_v3.txt'
]

for f in files_to_delete:
    path = os.path.join('scripts', f)
    if os.path.exists(path):
        try:
            os.remove(path)
            print(f"Deleted {path}")
        except Exception as e:
            print(f"Failed to delete {path}: {e}")
