# Chapter 11: 에러 처리 및 로깅

## 학습 목표
- 안전한 에러 처리의 중요성 이해
- 민감 정보 노출 방지 방법 학습
- 보안 로깅 모범 사례 적용

## 취약점 설명

### 1. 상세 에러 메시지 노출
공격자에게 시스템 구조 정보 제공

### 2. 스택 트레이스 노출
디버그 정보가 사용자에게 표시됨

### 3. 민감 정보 로깅
비밀번호, 신용카드 번호 등이 로그에 기록

### 4. 사용자 열거 공격
로그인 실패 메시지로 사용자 존재 여부 확인 가능

## 실습 방법

```bash
docker-compose up --build
```

- 취약한 버전: http://localhost:5001
- 안전한 버전: http://localhost:5002

## 테스트 시나리오

### 취약한 버전 테스트
1. `/user?id=abc` - 스택 트레이스 노출 확인
2. `/user?id=999` - 데이터베이스 정보 노출 확인
3. `/debug` - 시스템 환경 정보 노출 확인
4. 로그인 실패 후 메시지 차이 확인
5. `app.log` 파일에서 민감 정보 확인

### 안전한 버전 테스트
1. 동일한 요청 시 일반적인 에러 메시지 확인
2. 에러 ID를 통한 추적 가능성 확인
3. `secure_app.log`에서 마스킹된 로그 확인

## 보안 조치

1. **일반적인 에러 메시지 사용**
   - 내부 정보를 노출하지 않는 메시지
   - 에러 ID로 추적 가능하게 구현

2. **민감 정보 마스킹**
   - 로그 필터를 통한 자동 마스킹
   - 신용카드, 이메일, 비밀번호 패턴 탐지

3. **구조화된 로깅**
   - 요청 ID 할당
   - 적절한 로그 레벨 사용

4. **동일한 에러 응답**
   - 로그인 실패 시 동일한 메시지
   - 사용자 열거 공격 방지

## 테스트 방법

### 1. pytest 실행 (권장)
```bash
cd ch11-error-handling
pytest test_app.py -v
```

**예상 출력:**
```
test_app.py::TestVulnerableApp::test_index PASSED                    [ 14%]
test_app.py::TestVulnerableApp::test_error_exposes_trace PASSED      [ 28%]
test_app.py::TestVulnerableApp::test_sensitive_log PASSED            [ 42%]
test_app.py::TestSecureApp::test_index PASSED                        [ 57%]
test_app.py::TestSecureApp::test_error_generic PASSED                [ 71%]
test_app.py::TestSecureApp::test_error_id_present PASSED             [ 85%]
test_app.py::TestSecureApp::test_sensitive_masked PASSED             [100%]

============================== 7 passed in 0.46s ==============================
```

**테스트 항목:**
| 테스트 | 설명 | 결과 |
|--------|------|------|
| `test_index` | 메인 페이지 접근 테스트 | 두 버전 모두 통과 |
| `test_error_exposes_trace` | 취약: 스택 트레이스 노출 | 취약 버전만 통과 |
| `test_sensitive_log` | 취약: 민감 정보 로그 기록 | 취약 버전만 통과 |
| `test_error_generic` | 안전: 일반 에러 메시지 | 안전 버전만 통과 |
| `test_error_id_present` | 안전: error_id로 추적 가능 | 안전 버전만 통과 |
| `test_sensitive_masked` | 안전: 민감 정보 마스킹 확인 | 안전 버전만 통과 |

**개별 테스트 실행:**
```bash
# 취약한 버전만 테스트
pytest test_app.py::TestVulnerableApp -v

# 안전한 버전만 테스트
pytest test_app.py::TestSecureApp -v

# 에러 처리 관련 테스트만 실행
pytest test_app.py -k "error" -v

# 로깅 관련 테스트만 실행
pytest test_app.py -k "log or masked" -v
```

### 2. Docker 테스트
```bash
cd ch11-error-handling
docker-compose up -d

# 취약한 버전 - 스택 트레이스 노출
curl "http://localhost:5001/user?id=abc"
# 결과: traceback 정보 포함

# 안전한 버전 - 일반 에러 메시지
curl "http://localhost:5002/user?id=abc"
# 결과: error_id만 포함, 상세 정보 없음

docker-compose down
```

### 3. 수동 테스트
1. http://localhost:5001/user?id=abc 접속
2. 스택 트레이스 노출 확인 (취약점)
3. http://localhost:5002/user?id=abc 접속
4. 일반적인 에러 메시지 + error_id 확인 (방어)
5. 로그 파일에서 마스킹 확인
