# Chapter 09: 인증 및 인가 실습

## 학습 목표
- 안전한 비밀번호 저장 (bcrypt, Argon2)
- JWT 보안 모범 사례
- 브루트포스 방지

## 실습 환경 실행

```bash
cd ch09-authentication
docker-compose up -d

# 취약한 버전: http://localhost:5001
# 안전한 버전: http://localhost:5002
```

## 취약점 비교

### 비밀번호 해시

| 취약 | 안전 |
|------|------|
| MD5 | bcrypt |
| SHA1 | Argon2 |
| Salt 없음 | 자동 Salt |

### JWT

| 취약 | 안전 |
|------|------|
| algorithms=["HS256", "none"] | algorithms=["HS256"] |
| 하드코딩된 시크릿 | 환경 변수 |
| 긴 만료 시간 | 1시간 이내 |

## bcrypt 사용법

```python
import bcrypt

# 해시 생성
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# 검증
if bcrypt.checkpw(password.encode(), password_hash):
    print("Password correct")
```

## JWT 보안

```python
import jwt

# 토큰 생성
token = jwt.encode(payload, SECRET, algorithm="HS256")

# 검증 (알고리즘 명시!)
payload = jwt.decode(token, SECRET, algorithms=["HS256"])
```

## 테스트 방법

### 1. pytest 실행 (권장)
```bash
cd ch09-authentication
pytest test_app.py -v
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

**테스트 항목:**
| 테스트 | 설명 | 결과 |
|--------|------|------|
| `test_index` | 메인 페이지 접근 테스트 | 두 버전 모두 통과 |
| `test_register` | 사용자 등록 기능 테스트 | 두 버전 모두 통과 |
| `test_login` | 로그인 기능 테스트 | 두 버전 모두 통과 |

**참고:**
- pytest는 기본 기능만 테스트
- 해시 알고리즘 차이(MD5 vs bcrypt)는 수동/Docker 테스트에서 확인
- JWT 토큰 검증은 브라우저 세션이 필요하여 수동 테스트 권장

**개별 테스트 실행:**
```bash
# 취약한 버전만 테스트
pytest test_app.py::TestVulnerableApp -v

# 안전한 버전만 테스트
pytest test_app.py::TestSecureApp -v

# 특정 기능만 테스트
pytest test_app.py -k "register" -v
pytest test_app.py -k "login" -v
```

### 2. Docker 테스트
```bash
cd ch09-authentication
docker-compose up -d

# 취약한 버전 - MD5 해시 확인
curl -X POST http://localhost:5001/register \
  -d "username=testuser&password=pass123"

# 안전한 버전 - bcrypt 해시 확인
curl -X POST http://localhost:5002/register \
  -d "username=testuser&password=pass123"

# DB에서 해시 형식 비교
docker-compose exec vulnerable cat users.db | strings | grep -E '\$2[ab]\$|[a-f0-9]{32}'

docker-compose down
```

### 3. 수동 테스트
1. http://localhost:5001 접속
2. 사용자 등록 후 DB 확인 (MD5 해시)
3. http://localhost:5002에서 동일 테스트
4. bcrypt 해시 형식 확인 (`$2b$...`)
5. JWT 토큰 구조 비교

## 체크리스트
- [ ] bcrypt 또는 Argon2 사용
- [ ] 비밀번호 복잡도 정책 적용
- [ ] JWT 알고리즘 명시적 지정
- [ ] 시크릿 키 환경 변수 사용
- [ ] 브루트포스 방지 구현
- [ ] 토큰 만료 시간 설정
