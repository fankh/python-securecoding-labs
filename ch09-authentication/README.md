# Chapter 09: 인증 및 인가 실습

## 학습 목표
- 안전한 비밀번호 저장 (bcrypt vs MD5)
- JWT 보안 모범 사례
- 브루트포스 방지 (계정 잠금)

## 실습 환경

```bash
cd ch09-authentication
docker-compose up -d

# 취약한 버전: http://localhost:5001
# 안전한 버전: http://localhost:5002
```

**기본 계정:**
| 사용자 | 비밀번호 | 권한 |
|--------|----------|------|
| `admin` | `admin123` | admin |

## 취약점 비교

### 비밀번호 해시

| 항목 | 취약한 버전 | 안전한 버전 |
|------|-----------|-----------|
| 해시 알고리즘 | MD5 (레인보우 테이블 공격 가능) | bcrypt (자동 salt 포함) |
| Salt | 없음 | 자동 생성 |
| 비밀번호 정책 | 없음 | 8자 이상, 대소문자+숫자+특수문자 |
| 저장 형식 | `0192023a7bbd73250516f069df18b500` | `$2b$12$...` (60자) |

### JWT 토큰

| 항목 | 취약한 버전 | 안전한 버전 |
|------|-----------|-----------|
| 알고리즘 | `["HS256", "none"]` 허용 | `["HS256"]`만 허용 |
| 시크릿 키 | 하드코딩 (`"secret123"`) | `os.urandom(32)` |
| 만료 시간 | 24시간 | 1시간 |
| 브루트포스 방지 | 없음 | 5회 실패 시 15분 잠금 |

## 공격 실습 (취약한 버전)

### 공격 1: 회원가입 후 MD5 해시 확인

```bash
# 회원가입
curl.exe -X POST http://localhost:5001/register \
  -d "username=testuser&password=pass123"

# 로그인하여 JWT 토큰 획득
curl.exe -X POST http://localhost:5001/login \
  -d "username=testuser&password=pass123"
```

취약한 버전은 MD5 해시를 사용하므로, 동일 비밀번호는 항상 동일한 해시를 생성합니다.
온라인 MD5 디코더로 `482c811da5d5b4bc6d497ffa98491e38` 검색 → `password123` 복원 가능

### 공격 2: admin 계정 로그인

```bash
# admin / admin123으로 로그인
curl.exe -X POST http://localhost:5001/login \
  -d "username=admin&password=admin123"
# 결과: JWT 토큰 반환

# 반환된 토큰으로 admin 페이지 접근
curl.exe -H "Authorization: Bearer <반환된_토큰>" \
  http://localhost:5001/admin
# 결과: "Welcome to admin panel"
```

### MD5 vs bcrypt 해시 비교

```
MD5 (취약):    0192023a7bbd73250516f069df18b500
               → 레인보우 테이블로 즉시 복원 가능

bcrypt (안전): $2b$12$LJ3m4ys3Rl81K7Oe4Hp8dOcBR...
               → Salt 포함, 복원 불가능
```

## 방어 확인 (안전한 버전)

### 비밀번호 정책 확인

```bash
# 약한 비밀번호 → 거부됨
curl.exe -X POST http://localhost:5002/register \
  -d "username=testuser&password=123"
# 결과: "비밀번호는 8자 이상이어야 합니다"

# 강한 비밀번호 → 성공
curl.exe -X POST http://localhost:5002/register \
  -d "username=testuser&password=Test1234!"
# 결과: "User registered successfully"
```

### 브루트포스 방지 확인

```bash
# 5회 연속 잘못된 비밀번호 입력
curl.exe -X POST http://localhost:5002/login -d "username=admin&password=wrong1"
curl.exe -X POST http://localhost:5002/login -d "username=admin&password=wrong2"
curl.exe -X POST http://localhost:5002/login -d "username=admin&password=wrong3"
curl.exe -X POST http://localhost:5002/login -d "username=admin&password=wrong4"
curl.exe -X POST http://localhost:5002/login -d "username=admin&password=wrong5"

# 6번째 시도 → 계정 잠금
curl.exe -X POST http://localhost:5002/login -d "username=admin&password=admin123"
# 결과: "계정이 잠겼습니다. ...까지 대기하세요" (15분 잠금)
```

## 방어 기법

### 1. bcrypt 해시

```python
import bcrypt

# 해시 생성 (자동 salt 포함)
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# 검증
if bcrypt.checkpw(password.encode(), password_hash):
    print("비밀번호 일치")
```

### 2. JWT 알고리즘 명시적 지정

```python
import jwt

# 토큰 생성
token = jwt.encode(payload, SECRET, algorithm="HS256")

# 검증 — algorithms를 명시적으로 지정!
payload = jwt.decode(token, SECRET, algorithms=["HS256"])
# "none" 알고리즘이 포함되면 토큰 위조 가능
```

### 3. 비밀번호 정책

```python
def validate_password(password):
    if len(password) < 8: return False, "8자 이상"
    if not re.search(r"[A-Z]", password): return False, "대문자 필요"
    if not re.search(r"[a-z]", password): return False, "소문자 필요"
    if not re.search(r"\d", password): return False, "숫자 필요"
    if not re.search(r"[!@#$%^&*]", password): return False, "특수문자 필요"
    return True, ""
```

## 테스트 방법

### 1. pytest 실행 (권장)

```bash
cd ch09-authentication
python -m pytest test_app.py -v
```

**예상 출력:**
```
test_app.py::TestVulnerableApp::test_index PASSED                    [ 16%]
test_app.py::TestVulnerableApp::test_register PASSED                 [ 33%]
test_app.py::TestVulnerableApp::test_login PASSED                    [ 50%]
test_app.py::TestSecureApp::test_index PASSED                        [ 66%]
test_app.py::TestSecureApp::test_register PASSED                     [ 83%]
test_app.py::TestSecureApp::test_login PASSED                        [100%]

============================== 6 passed in 0.55s ==============================
```

**개별 테스트 실행:**
```bash
python -m pytest test_app.py::TestVulnerableApp -v
python -m pytest test_app.py::TestSecureApp -v
python -m pytest test_app.py -k "register" -v
```

### 2. 수동 테스트 (브라우저)

#### 취약한 버전 테스트
1. http://localhost:5001 접속
2. 회원가입 후 로그인 → JWT 토큰 확인
3. [jwt.io](https://jwt.io)에서 토큰 디코딩 → 페이로드 확인

#### 안전한 버전 테스트
1. http://localhost:5002 접속
2. 약한 비밀번호로 회원가입 시도 → 정책 위반 에러 확인
3. 강한 비밀번호로 등록 후 로그인 → 1시간 만료 토큰 확인
4. 5회 잘못된 로그인 → 계정 잠금 확인

## 체크리스트
- [ ] bcrypt 또는 Argon2 사용 (MD5/SHA1 금지)
- [ ] 비밀번호 복잡도 정책 적용
- [ ] JWT 알고리즘 명시적 지정 (`"none"` 제외)
- [ ] 시크릿 키를 환경 변수로 관리
- [ ] 브루트포스 방지 (계정 잠금)
- [ ] 토큰 만료 시간 설정 (1시간 이내)
