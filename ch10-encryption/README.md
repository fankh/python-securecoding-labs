# Chapter 10: 암호화 실습

## 학습 목표
- 안전한 대칭키 암호화 (AES-GCM vs DES-ECB)
- 키 관리 모범 사례
- 해시 함수 선택 (SHA-256 vs MD5)

## 실습 환경

```bash
cd ch10-encryption
docker-compose up -d

# 취약한 버전: http://localhost:5001
# 안전한 버전: http://localhost:5002
```

## 취약점 비교

| 항목 | 취약한 버전 (5001) | 안전한 버전 (5002) |
|------|-------------------|-------------------|
| 암호화 알고리즘 | DES (56-bit, deprecated) | AES-256 |
| 운용 모드 | ECB (패턴 노출) | GCM (인증된 암호화) |
| IV/Nonce | 고정 IV | 매번 랜덤 Nonce 생성 |
| 키 관리 | 하드코딩 (`"secret12"`) | 환경 변수에서 로드 |
| 해시 함수 | MD5, SHA1 | SHA-256, SHA-3 |

## 공격 실습 (취약한 버전)

### ECB 모드의 패턴 노출 문제

```bash
# 동일한 평문을 2회 암호화
curl.exe -X POST http://localhost:5001/encrypt -d "data=hello"
curl.exe -X POST http://localhost:5001/encrypt -d "data=hello"
```

**결과:** ECB 모드는 동일한 평문 → **항상 동일한 암호문**을 생성합니다.
공격자가 암호문 패턴을 분석하여 원문을 추측할 수 있습니다.

### 취약한 해시 확인

```bash
curl.exe -X POST http://localhost:5001/hash -d "data=password"
```

**결과:** MD5, SHA1 해시가 반환됩니다.
- MD5: `5f4dcc3b5aa765d61d8327deb882cf99`
- SHA1: `5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8`

이 해시값은 온라인 레인보우 테이블에서 즉시 복원 가능합니다.

## 방어 확인 (안전한 버전)

### GCM 모드의 랜덤 Nonce 확인

```bash
# 동일한 평문을 2회 암호화
curl.exe -X POST http://localhost:5002/encrypt -d "data=hello"
curl.exe -X POST http://localhost:5002/encrypt -d "data=hello"
```

**결과:** GCM 모드는 매번 랜덤 Nonce를 사용하므로, 동일 평문 → **매번 다른 암호문**을 생성합니다.

### 암복호화 테스트

```bash
# 1. 암호화
curl.exe -X POST http://localhost:5002/encrypt -d "data=비밀 메시지"
# 결과: {"encrypted": "Base64_암호문", ...}

# 2. 반환된 암호문으로 복호화
curl.exe -X POST http://localhost:5002/decrypt -d "encrypted=<위에서_반환된_Base64값>"
# 결과: {"decrypted": "비밀 메시지"}
```

### 안전한 해시 확인

```bash
curl.exe -X POST http://localhost:5002/hash -d "data=password"
# 결과: SHA-256, SHA-3 해시 반환
```

## 방어 기법

### 1. AES-256-GCM 암호화

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

key = os.urandom(32)       # AES-256 키 (32바이트)
nonce = os.urandom(12)     # 랜덤 Nonce (매번 새로 생성)
aesgcm = AESGCM(key)

# 암호화 (GCM: 암호화 + 무결성 검증)
ciphertext = aesgcm.encrypt(nonce, plaintext, None)

# 복호화
plaintext = aesgcm.decrypt(nonce, ciphertext, None)
```

### 2. 키 관리

```python
# 환경 변수에서 키 로드
key = bytes.fromhex(os.environ["ENCRYPTION_KEY"])

# 비밀번호에서 키 유도 (PBKDF2)
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=600000)
key = kdf.derive(password.encode())
```

## 테스트 방법

### 1. pytest 실행 (권장)

```bash
cd ch10-encryption
python -m pytest test_app.py -v
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
| `test_encrypt` | 취약: DES/ECB 암호화 | 취약 버전만 통과 |
| `test_hash` | 취약: MD5 해시 | 취약 버전만 통과 |
| `test_encrypt_decrypt` | 안전: AES-GCM 암복호화 | 안전 버전만 통과 |
| `test_encrypt_different_nonce` | 안전: 동일 평문 → 다른 암호문 | 안전 버전만 통과 |

**개별 테스트 실행:**
```bash
python -m pytest test_app.py -k "encrypt" -v
python -m pytest test_app.py -k "hash" -v
```

### 2. 수동 테스트 (브라우저)

#### 취약한 버전 테스트
1. http://localhost:5001 접속
2. 동일 평문 2회 암호화 → 동일 암호문 확인 (ECB 취약점)
3. MD5 해시값을 온라인 디코더에서 검색 → 원문 복원

#### 안전한 버전 테스트
1. http://localhost:5002 접속
2. 동일 평문 2회 암호화 → 다른 암호문 확인 (GCM 안전)
3. 암호화 → 복호화 왕복 테스트로 데이터 무결성 확인

## 체크리스트
- [ ] AES-256 사용 (DES, 3DES 금지)
- [ ] GCM 또는 CCM 모드 사용 (ECB 금지)
- [ ] 매번 새로운 Nonce/IV 생성
- [ ] 키를 환경 변수로 관리 (하드코딩 금지)
- [ ] SHA-256 이상 해시 사용 (MD5/SHA1 금지)
