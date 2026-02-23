# Chapter 08: 역직렬화(Deserialization) 취약점 실습

## 학습 목표
- Pickle 역직렬화 취약점의 원리 이해
- RCE(Remote Code Execution) 공격 실습
- 안전한 직렬화 방법 습득

## 실습 환경 실행

```bash
cd ch08-deserialization
docker-compose up -d

# 취약한 버전: http://localhost:5001
# 안전한 버전: http://localhost:5002
```

## 공격 실습

### 1. 악성 페이로드 생성
```bash
python vulnerable/exploit.py
```

### 2. 페이로드 전송
1. http://localhost:5001 접속
2. "Load Session" 폼에 생성된 Base64 페이로드 입력
3. Submit 후 Docker 로그 확인

```bash
docker-compose logs vulnerable
```

## Pickle 취약점 원리

### __reduce__ 메서드
```python
class Malicious:
    def __reduce__(self):
        return (os.system, ("whoami",))
```

pickle.loads() 호출 시 __reduce__가 반환한 함수가 실행됨.

## 방어 기법

### 1. pickle 사용 금지
신뢰할 수 없는 데이터에는 절대 pickle.loads() 사용 금지

### 2. JSON 사용
```python
import json
data = json.loads(user_input)  # 안전: 코드 실행 불가
```

### 3. itsdangerous로 서명
```python
from itsdangerous import URLSafeSerializer
serializer = URLSafeSerializer(SECRET_KEY)
token = serializer.dumps(data)
data = serializer.loads(token)  # 변조 시 예외 발생
```

## 테스트 방법

### 1. pytest 실행 (권장)
```bash
cd ch08-deserialization
pytest test_app.py -v
```

**예상 출력:**
```
test_app.py::TestVulnerableApp::test_index PASSED                    [ 25%]
test_app.py::TestVulnerableApp::test_save_session PASSED             [ 50%]
test_app.py::TestSecureApp::test_index PASSED                        [ 75%]
test_app.py::TestSecureApp::test_save_session PASSED                 [100%]

============================== 4 passed in 0.38s ==============================
```

**테스트 항목:**
| 테스트 | 설명 | 결과 |
|--------|------|------|
| `test_index` | 메인 페이지 접근 테스트 | 두 버전 모두 통과 |
| `test_save_session` | 세션 저장 기능 테스트 | 두 버전 모두 통과 |

**참고:**
- pytest는 기본 기능만 테스트 (실제 Pickle RCE 공격은 수동/Docker 테스트 참고)
- Pickle 역직렬화 공격은 악성 페이로드가 필요하여 수동 테스트 권장

**개별 테스트 실행:**
```bash
# 취약한 버전만 테스트
pytest test_app.py::TestVulnerableApp -v

# 안전한 버전만 테스트
pytest test_app.py::TestSecureApp -v
```

### 2. Docker 테스트
```bash
cd ch08-deserialization
docker-compose up -d

# 취약한 버전 - Pickle 직렬화 사용
curl -X POST http://localhost:5001/save_session -d "username=test"

# 안전한 버전 - itsdangerous 서명 사용
curl -X POST http://localhost:5002/save_session -d "username=test"

# 로그에서 차이 확인
docker-compose logs

docker-compose down
```

### 3. 수동 테스트
1. http://localhost:5001 접속
2. 세션 저장 후 쿠키 값 확인 (Base64 Pickle)
3. exploit.py로 악성 페이로드 생성
4. http://localhost:5002에서 동일 테스트
5. 변조된 데이터 거부 확인 (서명 검증)

## 체크리스트
- [ ] 외부 입력에 pickle.loads() 사용하지 않기
- [ ] JSON, MessagePack 등 안전한 포맷 사용
- [ ] 필요시 서명으로 무결성 검증
- [ ] yaml.safe_load() 사용 (yaml.load() 금지)
