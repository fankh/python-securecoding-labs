"""
보안 스캐닝 테스트용 취약한 코드
bandit으로 스캔하여 취약점을 확인하세요.
"""
import os
import subprocess
import pickle
import hashlib

# B602: subprocess with shell=True
def vulnerable_command(user_input):
    subprocess.call(f"echo {user_input}", shell=True)

# B301: Pickle usage
def vulnerable_pickle(data):
    return pickle.loads(data)

# B303: MD5 usage
def vulnerable_hash(password):
    return hashlib.md5(password.encode()).hexdigest()

# B105: Hardcoded password
PASSWORD = "admin123"

# B608: SQL Injection
def vulnerable_sql(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return query

# B501: requests without certificate verification
def vulnerable_request():
    import requests
    requests.get("https://example.com", verify=False)


if __name__ == "__main__":
    print("이 파일을 bandit으로 스캔하세요:")
    print("  bandit scan_example.py")
