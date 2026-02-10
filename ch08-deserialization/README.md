# Chapter 08: 역직렬화(Deserialization) 취약점 실습

## 학습 목표
- Pickle 역직렬화 취약점의 원리 이해
- RCE(Remote Code Execution) 공격 실습
- 안전한 직렬화 방법 습득

## 실습 환경 실행

```bash
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

## 체크리스트
- [ ] 외부 입력에 pickle.loads() 사용하지 않기
- [ ] JSON, MessagePack 등 안전한 포맷 사용
- [ ] 필요시 서명으로 무결성 검증
- [ ] yaml.safe_load() 사용 (yaml.load() 금지)
