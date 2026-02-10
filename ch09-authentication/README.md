# Chapter 09: 인증 및 인가 실습

## 학습 목표
- 안전한 비밀번호 저장 (bcrypt, Argon2)
- JWT 보안 모범 사례
- 브루트포스 방지

## 실습 환경 실행

```bash
docker-compose up -d

# 취약한 버전: http://localhost:5001
# 안전한 버전: http://localhost:5002
```

## 취약점 비교

### 비밀번호 해시

| 취약 | 안전 |
|------|------|
| MD5 | bcrypt |
| SHA1 | Argon2 |
| Salt 없음 | 자동 Salt |

### JWT

| 취약 | 안전 |
|------|------|
| algorithms=["HS256", "none"] | algorithms=["HS256"] |
| 하드코딩된 시크릿 | 환경 변수 |
| 긴 만료 시간 | 1시간 이내 |

## bcrypt 사용법

```python
import bcrypt

# 해시 생성
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# 검증
if bcrypt.checkpw(password.encode(), password_hash):
    print("Password correct")
```

## JWT 보안

```python
import jwt

# 토큰 생성
token = jwt.encode(payload, SECRET, algorithm="HS256")

# 검증 (알고리즘 명시!)
payload = jwt.decode(token, SECRET, algorithms=["HS256"])
```

## 체크리스트
- [ ] bcrypt 또는 Argon2 사용
- [ ] 비밀번호 복잡도 정책 적용
- [ ] JWT 알고리즘 명시적 지정
- [ ] 시크릿 키 환경 변수 사용
- [ ] 브루트포스 방지 구현
- [ ] 토큰 만료 시간 설정
