# Chapter 11: 에러 처리 및 로깅

## 학습 목표
- 안전한 에러 처리의 중요성 이해
- 민감 정보 노출 방지 방법 학습
- 보안 로깅 모범 사례 적용

## 실습 환경

```powershell
cd ch11-error-handling
docker-compose up -d --build

# 취약한 버전: http://localhost:5001
# 안전한 버전: http://localhost:5002
```

**테스트 계정:** `admin` / `admin123`

## 취약점 비교

| 항목 | 취약한 버전 (5001) | 안전한 버전 (5002) |
|------|-------------------|-------------------|
| 에러 메시지 | 스택 트레이스 전체 노출 | 일반적인 메시지 + error_id |
| 디버그 모드 | `debug=True` | `debug=False` |
| 로그 기록 | 비밀번호, 신용카드 평문 기록 | 민감 정보 자동 마스킹 |
| 사용자 열거 | "Username does not exist" / "Invalid password" 구분 | 동일한 "Invalid credentials" 메시지 |
| 디버그 엔드포인트 | `/debug` 에서 환경변수 전체 노출 | 없음 |
| DB 트랜잭션 | rollback 없음 → 에러 시 데이터 불일치 | rollback으로 데이터 일관성 보장 |

## 공격 실습 (취약한 버전)

### 공격 1: 스택 트레이스 노출

```powershell
curl.exe "http://localhost:5001/user?id=abc"
```

**결과:** 전체 스택 트레이스가 응답에 포함됩니다:
```json
{
  "error": "invalid literal for int() with base 10: 'abc'",
  "type": "ValueError",
  "traceback": "Traceback (most recent call last):\n  File \"/app/vulnerable/app.py\"..."
}
```

공격자는 파일 경로, 코드 구조, Python 버전 등 시스템 정보를 얻을 수 있습니다.

### 공격 2: 데이터베이스 구조 노출

```powershell
curl.exe "http://localhost:5001/user?id=999"
```

**결과:** 존재하지 않는 사용자 조회 시 DB 테이블명과 쿼리가 노출됩니다:
```json
{
  "error": "User not found in database table 'users'",
  "query": "SELECT * FROM users WHERE id = 999",
  "database": "users.db"
}
```

### 공격 3: 시스템 환경 정보 노출

```powershell
curl.exe "http://localhost:5001/debug"
```

**결과:** Python 버전, OS 정보, **환경 변수 전체**(시크릿 키, API 키 등)가 노출됩니다.

### 공격 4: 사용자 열거 공격

```powershell
# 존재하는 사용자
curl.exe -X POST http://localhost:5001/login -d "username=admin&password=wrong"
# 결과: "Invalid password for existing user"

# 존재하지 않는 사용자
curl.exe -X POST http://localhost:5001/login -d "username=nonexist&password=wrong"
# 결과: "Username does not exist in our system"
```

에러 메시지가 다르므로, 공격자가 유효한 사용자명을 추측할 수 있습니다.

### 공격 5: 로그에서 민감 정보 유출

취약한 버전은 비밀번호, 신용카드 번호를 로그 파일에 평문으로 기록합니다:
```
Login attempt: username=admin, password=admin123
User found: {'credit_card': '4111-1111-1111-1111', ...}
```

### 공격 6: 트랜잭션 rollback 없음 → 데이터 불일치

```powershell
# 초기 잔액 확인 (admin: 1000, alice: 1000)
curl.exe http://localhost:5001/balance

# 송금 중 에러 발생 (receiver="error"로 시뮬레이션)
curl.exe -X POST http://localhost:5001/transfer -d "from=admin&to=error&amount=300"
# 결과: 500 에러

# 잔액 다시 확인
curl.exe http://localhost:5001/balance
# 결과: admin: 700, alice: 1000 → 300원이 사라짐!
```

**원인:** 취약한 코드는 1단계(차감) 후 바로 `commit()`하므로, 2단계(입금)에서 에러가 나면 차감만 반영됩니다:

```python
# 취약한 코드
conn.execute("UPDATE accounts SET balance = balance - ? ...", (amount, sender))
conn.commit()  # ← 여기서 이미 커밋! 이후 에러 시 되돌릴 수 없음

conn.execute("UPDATE accounts SET balance = balance + ? ...", (amount, receiver))
conn.commit()  # ← 여기서 에러 발생 시 위의 차감만 남음
```

## 방어 확인 (안전한 버전)

```powershell
# 동일한 잘못된 입력 → 일반적인 에러 메시지만 반환
curl.exe "http://localhost:5002/user?id=abc"
# 결과: {"error": "Invalid input provided"}

# 존재/비존재 사용자 → 동일한 메시지
curl.exe -X POST http://localhost:5002/login -d "username=admin&password=wrong"
curl.exe -X POST http://localhost:5002/login -d "username=nonexist&password=wrong"
# 결과: 둘 다 "Invalid credentials" (사용자 열거 불가)
```

### 안전한 rollback 확인

```powershell
# 초기 잔액 확인 (admin: 1000, alice: 1000)
curl.exe http://localhost:5002/balance

# 송금 중 에러 발생
curl.exe -X POST http://localhost:5002/transfer -d "from=admin&to=error&amount=300"
# 결과: 500 에러

# 잔액 확인 → rollback으로 잔액 보존
curl.exe http://localhost:5002/balance
# 결과: admin: 1000, alice: 1000 → 잔액 변화 없음 (안전!)

# 정상 송금 테스트
curl.exe -X POST http://localhost:5002/transfer -d "from=admin&to=alice&amount=200"
curl.exe http://localhost:5002/balance
# 결과: admin: 800, alice: 1200 (정상)
```

## 방어 기법

### 1. 일반적인 에러 메시지 + error_id

```python
import uuid

error_id = str(uuid.uuid4())[:8]
logger.error(f"Error ID {error_id}: {type(e).__name__}: {str(e)}")

return jsonify({
    "error": "An unexpected error occurred",
    "error_id": error_id  # 사용자가 지원팀에 전달
}), 500
```

### 2. 민감 정보 로그 마스킹

```python
class SensitiveDataFilter(logging.Filter):
    PATTERNS = [
        (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD_MASKED]'),
        (r'\b[\w.+-]+@[\w-]+\.[\w.]+\b', '[EMAIL_MASKED]'),
        (r'password\s*[:=]\s*\S+', 'password=[MASKED]'),
    ]

    def filter(self, record):
        for pattern, replacement in self.PATTERNS:
            record.msg = re.sub(pattern, replacement, record.msg)
        return True
```

### 3. 동일한 에러 응답 (사용자 열거 방지)

```python
# 취약: 사용자 존재 여부를 구분
if exists: return "Invalid password", 401
else:      return "Username not found", 401

# 안전: 항상 동일한 메시지
return jsonify({"error": "Invalid credentials"}), 401
```

### 4. 트랜잭션 rollback (데이터 일관성)

```python
# 취약: 중간 commit → 에러 시 데이터 불일치
conn.execute("UPDATE accounts SET balance = balance - ? ...", (amount, sender))
conn.commit()  # 여기서 커밋 후 아래에서 에러 나면 돈이 사라짐
conn.execute("UPDATE accounts SET balance = balance + ? ...", (amount, receiver))
conn.commit()

# 안전: 모든 작업 완료 후 commit, 에러 시 rollback
conn = get_db()
try:
    conn.execute("UPDATE accounts SET balance = balance - ? ...", (amount, sender))
    conn.execute("UPDATE accounts SET balance = balance + ? ...", (amount, receiver))
    conn.commit()  # 모두 성공한 경우에만 커밋
except Exception:
    conn.rollback()  # 에러 시 모든 변경 취소
    raise
finally:
    conn.close()
```

## 테스트 방법

### 1. pytest 실행 (권장)

```powershell
cd ch11-error-handling
python -m pytest test_app.py -v
```

**예상 출력:**
```
test_app.py::TestVulnerableApp::test_index PASSED                    [ 14%]
test_app.py::TestVulnerableApp::test_error_exposes_trace PASSED      [ 28%]
test_app.py::TestVulnerableApp::test_transfer_no_rollback PASSED     [ 42%]
test_app.py::TestSecureApp::test_index PASSED                        [ 57%]
test_app.py::TestSecureApp::test_error_generic PASSED                [ 71%]
test_app.py::TestSecureApp::test_transfer_rollback PASSED            [ 85%]
test_app.py::TestSecureApp::test_transfer_success PASSED             [100%]

============================== 7 passed in 0.74s ==============================
```

**테스트 항목:**
| 테스트 | 설명 |
|--------|------|
| `test_error_exposes_trace` | 취약: 스택 트레이스 노출 확인 |
| `test_transfer_no_rollback` | 취약: 에러 시 rollback 없음 → 잔액 불일치 확인 |
| `test_error_generic` | 안전: 일반 에러 메시지만 반환 확인 |
| `test_transfer_rollback` | 안전: 에러 시 rollback → 잔액 보존 확인 |
| `test_transfer_success` | 안전: 정상 송금 시 잔액 정확히 변경 확인 |

**개별 테스트 실행:**
```powershell
python -m pytest test_app.py -k "error" -v
python -m pytest test_app.py -k "transfer" -v
```

### 2. 수동 테스트 (브라우저)

#### 취약한 버전 테스트
1. http://localhost:5001/user?id=abc 접속 → 스택 트레이스 노출 확인
2. http://localhost:5001/user?id=999 접속 → DB 구조 정보 노출 확인
3. http://localhost:5001/debug 접속 → 환경 변수 전체 노출 확인
4. 로그인 실패 → 사용자 존재 여부에 따라 다른 메시지 확인
5. http://localhost:5001/balance 확인 → 에러 송금 후 잔액 불일치 확인

#### 안전한 버전 테스트
1. http://localhost:5002/user?id=abc 접속 → 일반 에러 메시지 확인
2. http://localhost:5002/user?id=999 접속 → "Resource not found" 확인
3. 로그인 실패 → 항상 동일한 "Invalid credentials" 메시지 확인
4. http://localhost:5002/balance 확인 → 에러 송금 후 잔액 보존 확인

## 체크리스트
- [ ] 스택 트레이스를 사용자에게 노출하지 않기
- [ ] error_id로 내부 추적 가능하게 구현
- [ ] 민감 정보 로그 자동 마스킹
- [ ] 동일한 에러 메시지 사용 (사용자 열거 방지)
- [ ] `debug=False` 설정 (프로덕션)
- [ ] 디버그 엔드포인트 제거
- [ ] DB 트랜잭션에서 에러 시 rollback 처리
