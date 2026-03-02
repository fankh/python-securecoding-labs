# Chapter 01: 보안 개요 및 환경 설정

## 학습 목표
- Python 시큐어코딩의 필요성 이해
- 실습 환경 구성
- 보안 도구 설치

## 환경 설정

### 1. Docker 설치
```bash
# Windows/Mac: Docker Desktop 설치
# Linux: docker.io 패키지 설치
```

### 2. Python 환경
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 보안 도구 설치
```bash
pip install bandit safety semgrep
```

## 보안 스캐닝 실습

### Bandit (정적 분석)
```bash
# 현재 디렉토리 스캔
python -m bandit -r .

# 특정 파일 스캔
python -m bandit vulnerable_app.py
```

### Safety (의존성 취약점)
```bash
# requirements.txt 검사
safety check -r requirements.txt
```

### pip-audit
```bash
pip install pip-audit
pip-audit
```

## 취약한 코드 예시

### SQL Injection
```python
# 취약
query = f"SELECT * FROM users WHERE id = {user_id}"

# 안전
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

### Command Injection
```python
# 취약
os.system(f"ping {host}")

# 안전
subprocess.run(["ping", host], shell=False)
```

## 체크리스트
- [ ] Docker Desktop 설치
- [ ] Python 3.11+ 설치
- [ ] VS Code + Python 확장 설치
- [ ] Bandit, Safety 설치
