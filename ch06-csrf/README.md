# Chapter 06: CSRF 실습

## 학습 목표
- CSRF 공격 원리 이해
- CSRF 토큰 구현
- SameSite 쿠키 설정

## 실습 환경

```bash
cd ch06-csrf
docker-compose up -d
# 취약한 버전: http://localhost:5001
# 안전한 버전: http://localhost:5002
```

## 공격 실습

### 1. 피해자 로그인
http://localhost:5001에서 alice로 로그인

### 2. 공격 페이지 생성
```html
<!-- attacker.html -->
<html>
<body>
<form action="http://localhost:5001/transfer" method="POST">
    <input type="hidden" name="to" value="attacker">
    <input type="hidden" name="amount" value="500">
</form>
<script>document.forms[0].submit();</script>
</body>
</html>
```

### 3. 피해자가 공격 페이지 방문 시 자동 송금

## 방어 기법

### Flask-WTF CSRF 보호
```python
from flask_wtf import CSRFProtect
csrf = CSRFProtect(app)
```

### 템플릿에 토큰 추가
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

## 테스트 방법

### 1. Bandit 정적 분석 (권장)
```bash
cd ch06-csrf

# 자동 스캔 (취약한 코드 vs 안전한 코드 비교)
./test_bandit.sh

# 또는 수동 실행
bandit -r vulnerable/ -ll
bandit -r secure/ -ll
```

**예상 결과:**
| 코드 | Bandit 결과 |
|------|------------|
| `vulnerable/app.py` | 🔴 B105: 하드코딩된 secret_key<br>🔴 B201: debug=True 활성화 |
| `secure/app.py` | ⚠️ B105: secret_key (환경변수 권장)<br>✅ debug=False |

### 2. pytest 실행
```bash
cd ch06-csrf
pytest test_app.py -v
```

**예상 출력:**
```
test_app.py::TestVulnerableApp::test_index PASSED                    [ 50%]
test_app.py::TestSecureApp::test_index PASSED                        [100%]

============================== 2 passed in 0.35s ==============================
```

**테스트 항목:**
| 테스트 | 설명 | 결과 |
|--------|------|------|
| `test_index` | 메인 페이지 (/) 접근 테스트 | 두 버전 모두 통과 |

**참고:**
- pytest는 기본 기능만 테스트 (CSRF 공격 테스트는 수동/Docker 테스트 참고)
- CSRF 토큰 검증은 브라우저 세션이 필요하여 수동 테스트 권장

**개별 테스트 실행:**
```bash
# 취약한 버전만 테스트
pytest test_app.py::TestVulnerableApp -v

# 안전한 버전만 테스트
pytest test_app.py::TestSecureApp -v
```

### 3. Docker 테스트
```bash
cd ch06-csrf
docker-compose up -d

# 취약한 버전 - CSRF 공격 시뮬레이션
# 1. 브라우저에서 http://localhost:5001 접속 후 alice로 로그인
# 2. 새 탭에서 아래 HTML 파일 열기

# 안전한 버전 - CSRF 토큰 필요
curl -X POST http://localhost:5002/transfer \
  -d "to=attacker&amount=100"
# 결과: CSRF 토큰 누락으로 실패

docker-compose down
```

### 4. 수동 테스트
1. http://localhost:5001 접속, alice로 로그인
2. 개발자 도구에서 CSRF 토큰 없이 송금 요청
3. 송금 성공 확인 (취약점)
4. http://localhost:5002에서 동일 테스트
5. CSRF 토큰 없으면 거부 확인 (방어 성공)

## 보안 스캐닝

### Bandit 취약점 검출
```bash
# 전체 스캔
bandit -r . -ll

# 특정 파일 스캔
bandit vulnerable/app.py

# JSON 출력
bandit -r vulnerable/ -f json -o bandit-report.json
```

**검출되는 취약점:**
- **B105 (LOW)**: Hardcoded password string (secret_key)
- **B201 (HIGH)**: Flask app with debug=True

**권장 사항:**
```python
# 환경변수 사용
import os
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# debug=False (프로덕션)
app.run(debug=False)
```

## 체크리스트
- [ ] CSRF 토큰 구현
- [ ] POST 요청만 허용
- [ ] SameSite=Strict 쿠키
- [ ] secret_key 환경변수 사용
- [ ] debug=False 설정
- [ ] Bandit 정적 분석 통과
