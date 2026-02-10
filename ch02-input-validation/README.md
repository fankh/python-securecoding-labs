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

## 체크리스트
- [ ] 화이트리스트 기반 검증
- [ ] 길이 제한
- [ ] 타입 검증
- [ ] ReDoS 안전한 정규식
