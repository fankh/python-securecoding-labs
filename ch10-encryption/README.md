# Chapter 10: 암호화 실습

## 학습 목표
- 안전한 대칭키 암호화 (AES-GCM)
- 키 관리 모범 사례
- 해시 함수 선택

## 실습 환경 실행

```bash
docker-compose up -d

# 취약한 버전: http://localhost:5001
# 안전한 버전: http://localhost:5002
```

## 암호화 알고리즘 비교

| 취약 | 안전 |
|------|------|
| DES | AES-256 |
| ECB 모드 | GCM 모드 |
| 고정 IV | 랜덤 Nonce |
| MD5/SHA1 | SHA-256/SHA-3 |

## AES-GCM 사용법

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

# 키 생성 (32바이트 = AES-256)
key = os.urandom(32)

# 암호화
nonce = os.urandom(12)
aesgcm = AESGCM(key)
ciphertext = aesgcm.encrypt(nonce, plaintext, None)

# 복호화
plaintext = aesgcm.decrypt(nonce, ciphertext, None)
```

## 키 관리

```python
# 환경 변수에서 로드
key = bytes.fromhex(os.environ["ENCRYPTION_KEY"])

# 비밀번호에서 유도 (PBKDF2)
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=600000)
key = kdf.derive(password.encode())
```

## 체크리스트
- [ ] AES-256 사용
- [ ] GCM 또는 CCM 모드 사용
- [ ] 매번 새로운 Nonce/IV 생성
- [ ] 키를 환경 변수로 관리
- [ ] SHA-256 이상 해시 사용
