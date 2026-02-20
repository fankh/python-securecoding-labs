# Chapter 02: 입력값 검증 실습

## 학습 목표
- 화이트리스트 vs 블랙리스트
- Pydantic 스키마 검증
- ReDoS 방지

## 실습 환경

```bash
docker-compose up -d

# 취약한 버전: http://localhost:5001
# 안전한 버전: http://localhost:5002
```

## 취약점 테스트

### 블랙리스트 우회
```
Username: <SCRIPT>alert(1)</SCRIPT>
Username: <img/src=x onerror=alert(1)>
```

### ReDoS 공격
```
Email: aaaaaaaaaaaaaaaaaaaaaaaaaaaa!
```

## 방어 기법

### Pydantic 스키마
```python
from pydantic import BaseModel, EmailStr

class User(BaseModel):
    username: str
    email: EmailStr
    age: int
```

### 화이트리스트 정규식
```python
if not re.match(r'^[a-zA-Z0-9_]+$', username):
    raise ValueError('Invalid username')
```

## 테스트 방법

### 1. pytest 실행 (권장)
```bash
cd ch02-input-validation
pytest test_app.py -v
```

**테스트 항목:**
| 테스트 | 설명 | 실행 명령 |
|--------|------|----------|
| `test_blacklist_bypass_uppercase` | 취약: 대소문자 우회 허용 | `pytest test_app.py::TestVulnerableApp::test_blacklist_bypass_uppercase -v` |
| `test_no_type_validation` | 취약: 타입 검증 없음 | `pytest test_app.py::TestVulnerableApp::test_no_type_validation -v` |
| `test_rejects_invalid_username` | 안전: XSS 차단 | `pytest test_app.py::TestSecureApp::test_rejects_invalid_username -v` |
| `test_rejects_invalid_email` | 안전: 이메일 검증 | `pytest test_app.py::TestSecureApp::test_rejects_invalid_email -v` |
| `test_rejects_invalid_age` | 안전: 범위 검증 | `pytest test_app.py::TestSecureApp::test_rejects_invalid_age -v` |

**추가 pytest 옵션:**
```bash
# 특정 클래스의 모든 테스트 실행
pytest test_app.py::TestVulnerableApp -v
pytest test_app.py::TestSecureApp -v

# 키워드로 필터링
pytest test_app.py -k "vulnerable" -v    # 취약한 버전만
pytest test_app.py -k "secure" -v        # 안전한 버전만
pytest test_app.py -k "invalid" -v       # 검증 테스트만

# 상세 출력 옵션
pytest test_app.py -v --tb=short         # 짧은 traceback
pytest test_app.py -v --tb=long          # 긴 traceback
pytest test_app.py -vv                   # 매우 상세한 출력

# 실패 시 즉시 중단
pytest test_app.py -x                    # 첫 실패 시 중단
pytest test_app.py --maxfail=2           # 2번 실패 시 중단
```

### 2. Docker 테스트
```bash
docker-compose up -d

# 취약한 버전 테스트
curl -X POST http://localhost:5001/register \
  -d "username=<SCRIPT>alert(1)</SCRIPT>&email=test@test.com&age=25&website=http://test.com"

# 안전한 버전 테스트
curl -X POST http://localhost:5002/register \
  -d "username=<script>alert(1)</script>&email=test@test.com&age=25&website=http://test.com"

docker-compose down
```

### 3. 수동 테스트
1. http://localhost:5001 접속 (취약한 버전)
2. Username에 `<SCRIPT>alert(1)</SCRIPT>` 입력
3. 등록 성공 확인 (취약점)
4. http://localhost:5002에서 동일 테스트
5. 에러 응답 확인 (방어 성공)

## 체크리스트
- [ ] 화이트리스트 기반 검증
- [ ] 길이 제한
- [ ] 타입 검증
- [ ] ReDoS 안전한 정규식
