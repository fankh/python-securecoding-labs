# Chapter 06: CSRF (Cross-Site Request Forgery) 실습

## 학습 목표
- CSRF 공격의 원리와 위험성 이해
- CSRF 토큰을 이용한 방어 구현
- SameSite 쿠키 설정 방법 습득

## CSRF란?

CSRF(Cross-Site Request Forgery)는 사용자가 로그인된 상태에서, 공격자가 만든 악성 웹페이지를 방문하면
사용자의 의도와 무관하게 요청이 전송되는 공격입니다.

**핵심 원리:** 브라우저는 쿠키를 자동으로 포함하여 요청을 전송하므로,
로그인 상태의 사용자가 공격 페이지를 방문하면 인증된 요청이 자동 실행됩니다.

## 실습 환경

```bash
cd ch06-csrf
docker-compose up -d

# 취약한 버전: http://localhost:5001
# 안전한 버전: http://localhost:5002
```

**테스트 계정:**
| 사용자 | 초기 잔액 |
|--------|----------|
| `alice` | 1,000원 |
| `bob` | 1,000원 |

> 로그인 시 Username만 입력하면 됩니다 (비밀번호 없음)

## 취약점 비교

| 항목 | 취약한 버전 (5001) | 안전한 버전 (5002) |
|------|-------------------|-------------------|
| CSRF 토큰 | 없음 | Flask-WTF 자동 검증 |
| 송금 HTTP 메서드 | GET + POST 모두 허용 | POST만 허용 |
| SameSite 쿠키 | 미설정 | SameSite=Strict |
| secret_key | 하드코딩 (`"secret"`) | `os.urandom(32)` |

## 공격 실습 (취약한 버전)

### 단계 1: 피해자(alice) 로그인

1. 브라우저에서 http://localhost:5001 접속
2. Username에 `alice` 입력 후 Login 클릭
3. 잔액 1,000원 확인

### 단계 2: 공격 페이지 준비

아래 내용을 `attacker.html` 파일로 저장합니다:

```html
<!-- attacker.html -->
<html>
<body>
<h1>축하합니다! 경품에 당첨되었습니다!</h1>
<p>아래 버튼을 클릭하여 경품을 수령하세요.</p>

<!-- 숨겨진 자동 송금 폼 -->
<form action="http://localhost:5001/transfer" method="POST">
    <input type="hidden" name="to" value="attacker">
    <input type="hidden" name="amount" value="500">
</form>
<script>document.forms[0].submit();</script>
</body>
</html>
```

### 단계 3: 공격 실행

1. alice가 로그인된 **동일한 브라우저**에서 `attacker.html` 파일을 엽니다
2. 페이지가 열리는 즉시 숨겨진 폼이 자동 제출됩니다
3. http://localhost:5001 로 돌아가서 잔액을 확인합니다
4. **alice의 잔액이 1,000원 → 500원으로 감소** (공격 성공)

### 공격이 성공하는 이유

```
[alice의 브라우저]
    ↓ 로그인 → 세션 쿠키 저장됨
    ↓
[공격자 페이지 방문]
    ↓ 숨겨진 폼 자동 제출
    ↓ 브라우저가 세션 쿠키를 자동 포함!
    ↓
[서버: localhost:5001/transfer]
    ↓ 유효한 세션 쿠키 확인 → alice의 요청으로 인식
    ↓ CSRF 토큰 검증 없음 → 송금 실행
    ↓
[결과: alice → attacker에게 500원 송금]
```

### GET 요청을 이용한 공격 (이미지 태그)

취약한 버전은 GET 요청도 허용하므로, 이미지 태그만으로도 공격 가능합니다:

```html
<!-- 피해자가 이 이미지가 포함된 페이지를 방문하면 자동 송금됨 -->
<img src="http://localhost:5001/transfer?to=attacker&amount=500" width="0" height="0">
```

## 방어 확인 (안전한 버전)

### 안전한 버전에서 동일한 공격 시도

1. 브라우저에서 http://localhost:5002 접속
2. `alice`로 로그인
3. 위의 `attacker.html`에서 포트를 5002로 변경한 뒤 실행
4. **400 Bad Request 에러 발생** — CSRF 토큰이 없으므로 요청 거부

### curl로 CSRF 방어 확인

```bash
# CSRF 토큰 없이 송금 요청 → 400 에러 (방어 성공)
curl.exe -X POST http://localhost:5002/transfer \
  -d "to=attacker&amount=100"
```

## 방어 기법

### 1. Flask-WTF CSRF 보호

```python
from flask_wtf import CSRFProtect

app = Flask(__name__)
csrf = CSRFProtect(app)
```

### 2. 템플릿에 CSRF 토큰 추가

```html
<form action="/transfer" method="POST">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <input name="to" placeholder="받는 사람">
    <input name="amount" type="number" placeholder="금액">
    <button type="submit">송금</button>
</form>
```

### 3. POST 요청만 허용

```python
# 취약: GET + POST 모두 허용
@app.route("/transfer", methods=["GET", "POST"])

# 안전: POST만 허용
@app.route("/transfer", methods=["POST"])
```

### 4. SameSite 쿠키 설정

```python
@app.after_request
def set_cookie_options(response):
    existing_cookie = response.headers.get('Set-Cookie', '')
    if existing_cookie:
        response.headers['Set-Cookie'] = existing_cookie + '; SameSite=Strict'
    return response
```

## 테스트 방법

### 1. pytest 실행

```bash
cd ch06-csrf
python -m pytest test_app.py -v
```

**예상 출력:**
```
test_app.py::TestVulnerableApp::test_index PASSED                    [ 50%]
test_app.py::TestSecureApp::test_index PASSED                        [100%]

============================== 2 passed in 0.35s ==============================
```

**참고:**
- CSRF 공격은 브라우저 세션(쿠키 자동 전송)을 이용하므로, pytest로는 완전한 테스트가 불가능합니다
- 실제 공격 테스트는 위의 **공격 실습** 섹션을 참고하세요

**개별 테스트 실행:**
```bash
# 취약한 버전만 테스트
python -m pytest test_app.py::TestVulnerableApp -v

# 안전한 버전만 테스트
python -m pytest test_app.py::TestSecureApp -v
```

### 2. Bandit 정적 분석

```bash
cd ch06-csrf

# 자동 스캔 (취약한 코드 vs 안전한 코드 비교)
bash test_bandit.sh

# 또는 수동 실행
python -m bandit -r vulnerable/ -ll
python -m bandit -r secure/ -ll
```

**예상 결과:**
| 코드 | Bandit 결과 |
|------|------------|
| `vulnerable/app.py` | 🔴 B105: 하드코딩된 secret_key<br>🔴 B201: debug=True 활성화 |
| `secure/app.py` | ⚠️ B105: secret_key (환경변수 권장)<br>✅ debug=False |

### 3. 수동 테스트 (브라우저)

#### 취약한 버전 테스트
1. http://localhost:5001 접속 → `alice`로 로그인
2. 잔액 1,000원 확인
3. `attacker.html`을 동일 브라우저에서 열기
4. 자동 송금 후 잔액 500원으로 감소 확인 (취약점 확인)

#### 안전한 버전 테스트
1. http://localhost:5002 접속 → `alice`로 로그인
2. 잔액 1,000원 확인
3. `attacker.html`(포트 5002로 변경)을 동일 브라우저에서 열기
4. 400 에러 발생 확인 (방어 성공)
5. 브라우저 개발자 도구(F12) → 네트워크 탭에서 CSRF 토큰이 폼에 포함되어 있는지 확인

## 보안 스캐닝

### Bandit 취약점 검출
```bash
# 전체 스캔
python -m bandit -r . -ll

# 특정 파일 스캔
python -m bandit vulnerable/app.py

# JSON 출력
python -m bandit -r vulnerable/ -f json -o bandit-report.json
```

**검출되는 취약점:**
- **B105 (LOW)**: Hardcoded password string (secret_key)
- **B201 (HIGH)**: Flask app with debug=True

## 체크리스트
- [ ] 모든 상태 변경 요청에 CSRF 토큰 적용
- [ ] POST 요청만 허용 (GET으로 상태 변경 금지)
- [ ] SameSite=Strict 쿠키 설정
- [ ] secret_key를 환경변수로 관리
- [ ] debug=False 설정 (프로덕션)
- [ ] Bandit 정적 분석 통과
