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

## 테스트 방법

### 1. pytest 실행 (권장)
```bash
cd ch10-encryption
pytest test_app.py -v
```

**예상 출력:**
```
test_app.py::TestVulnerableApp::test_index PASSED                    [ 14%]
test_app.py::TestVulnerableApp::test_encrypt PASSED                  [ 28%]
test_app.py::TestVulnerableApp::test_hash PASSED                     [ 42%]
test_app.py::TestSecureApp::test_index PASSED                        [ 57%]
test_app.py::TestSecureApp::test_encrypt_decrypt PASSED              [ 71%]
test_app.py::TestSecureApp::test_hash_sha256 PASSED                  [ 85%]
test_app.py::TestSecureApp::test_encrypt_different_nonce PASSED      [100%]

============================== 7 passed in 0.48s ==============================
```

**테스트 항목:**
| 테스트 | 설명 | 결과 |
|--------|------|------|
| `test_index` | 메인 페이지 접근 테스트 | 두 버전 모두 통과 |
| `test_encrypt` | 취약: DES/ECB 암호화 테스트 | 취약 버전만 통과 |
| `test_hash` | 취약: MD5 해시 테스트 | 취약 버전만 통과 |
| `test_encrypt_decrypt` | 안전: AES-GCM 암복호화 테스트 | 안전 버전만 통과 |
| `test_hash_sha256` | 안전: SHA-256 해시 테스트 | 안전 버전만 통과 |
| `test_encrypt_different_nonce` | 안전: 동일 평문 → 다른 암호문 확인 | 안전 버전만 통과 |

**개별 테스트 실행:**
```bash
# 취약한 버전만 테스트
pytest test_app.py::TestVulnerableApp -v

# 안전한 버전만 테스트
pytest test_app.py::TestSecureApp -v

# 암호화 관련 테스트만 실행
pytest test_app.py -k "encrypt" -v

# 해시 관련 테스트만 실행
pytest test_app.py -k "hash" -v
```

### 2. Docker 테스트
```bash
cd ch10-encryption
docker-compose up -d

# 취약한 버전 - DES/ECB 모드
curl -X POST http://localhost:5001/encrypt -d "plaintext=hello"
curl -X POST http://localhost:5001/hash -d "text=password"

# 안전한 버전 - AES-GCM 모드
curl -X POST http://localhost:5002/encrypt -d "plaintext=hello"
# 반환된 ciphertext로 복호화 테스트
curl -X POST http://localhost:5002/decrypt -d "ciphertext=<반환값>"

docker-compose down
```

### 3. 수동 테스트
1. http://localhost:5001 접속
2. 동일 평문 2회 암호화 → 동일 암호문 (ECB 취약점)
3. http://localhost:5002에서 동일 테스트
4. 동일 평문 2회 암호화 → 다른 암호문 (GCM 안전)
5. 해시 형식 비교 (MD5 vs SHA-256)

## 체크리스트
- [ ] AES-256 사용
- [ ] GCM 또는 CCM 모드 사용
- [ ] 매번 새로운 Nonce/IV 생성
- [ ] 키를 환경 변수로 관리
- [ ] SHA-256 이상 해시 사용
