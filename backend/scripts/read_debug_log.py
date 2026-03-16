import os

def read_log():
    log_path = 'scripts/debug_output_v3.txt'
    if not os.path.exists(log_path):
        print("Log not found")
        return
    
    with open(log_path, 'rb') as f:
        content = f.read().decode('utf-16le')
    
    print("LOG CONTENT:")
    print("-" * 50)
    print(content)
    print("-" * 50)

if __name__ == "__main__":
    read_log()
