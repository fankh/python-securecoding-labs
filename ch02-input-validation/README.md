# Chapter 02: 입력값 검증 실습

## 학습 목표
- 화이트리스트 vs 블랙리스트
- Pydantic 스키마 검증
- ReDoS 방지

## 실습 환경

```bash
cd ch02-input-validation
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
python -m pytest test_app.py -v
```

**예상 출력:**
```
test_app.py::TestVulnerableApp::test_index_returns_200 PASSED        [  9%]
test_app.py::TestVulnerableApp::test_register_valid_input PASSED     [ 18%]
test_app.py::TestVulnerableApp::test_blacklist_bypass_uppercase PASSED [ 27%]
test_app.py::TestVulnerableApp::test_no_type_validation PASSED       [ 36%]
test_app.py::TestVulnerableApp::test_search_endpoint PASSED          [ 45%]
test_app.py::TestSecureApp::test_index_returns_200 PASSED            [ 54%]
test_app.py::TestSecureApp::test_register_valid_input PASSED         [ 63%]
test_app.py::TestSecureApp::test_rejects_invalid_username PASSED     [ 72%]
test_app.py::TestSecureApp::test_rejects_invalid_email PASSED        [ 81%]
test_app.py::TestSecureApp::test_rejects_invalid_age PASSED          [ 90%]
test_app.py::TestSecureApp::test_safe_regex_search PASSED            [100%]

============================= 11 passed in 0.52s ==============================
```

**테스트 항목:**
| 테스트 | 설명 | 결과 |
|--------|------|------|
| `test_blacklist_bypass_uppercase` | 취약: `<SCRIPT>` 대소문자 우회 허용 | 취약 버전만 통과 |
| `test_no_type_validation` | 취약: 잘못된 타입 (age='문자열') 허용 | 취약 버전만 통과 |
| `test_rejects_invalid_username` | 안전: `<script>` 태그 차단 (Pydantic) | 안전 버전만 통과 |
| `test_rejects_invalid_email` | 안전: 잘못된 이메일 형식 거부 | 안전 버전만 통과 |
| `test_rejects_invalid_age` | 안전: 범위 외 나이(200) 거부 | 안전 버전만 통과 |

**개별 테스트 실행:**
```bash
# 취약한 버전만 테스트
python -m pytest test_app.py::TestVulnerableApp -v

# 안전한 버전만 테스트
python -m pytest test_app.py::TestSecureApp -v

# 특정 테스트만 실행
python -m pytest test_app.py::TestVulnerableApp::test_blacklist_bypass_uppercase -v -s
```

### 2. Docker 테스트
```bash
cd ch02-input-validation
docker-compose up -d

# 취약한 버전 테스트
curl.exe -X POST http://localhost:5001/register -d "username=<SCRIPT>alert(1)</SCRIPT>&email=test@test.com&age=25&website=http://test.com"

# 안전한 버전 테스트
curl.exe -X POST http://localhost:5002/register -d "username=<script>alert(1)</script>&email=test@test.com&age=25&website=http://test.com"

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
