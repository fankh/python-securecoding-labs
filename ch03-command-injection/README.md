# Chapter 03: Command Injection 실습

## 학습 목표
- OS Command Injection 취약점 이해
- 다양한 인젝션 기법 실습
- subprocess 안전한 사용법 습득

## 실습 환경 실행

```bash
docker-compose up -d

# 취약한 버전: http://localhost:5001
# 안전한 버전: http://localhost:5002
```

## 공격 실습

### 기본 인젝션
```bash
# 세미콜론으로 명령어 연결
127.0.0.1; whoami

# 파이프로 명령어 연결
127.0.0.1 | cat /etc/passwd

# AND 연산자
127.0.0.1 && id

# OR 연산자 (ping 실패 시 실행)
invalid-host || whoami
```

### 고급 기법
```bash
# 명령어 치환
$(whoami)
`id`

# 줄바꿈 문자
127.0.0.1%0Aid

# 널 바이트 (일부 시스템)
127.0.0.1%00; whoami
```

## 취약한 코드 vs 안전한 코드

### 취약한 코드
```python
# shell=True는 위험!
subprocess.run(f"ping -c 3 {host}", shell=True)

# os.system()도 위험
os.system(f"nslookup {domain}")
```

### 안전한 코드
```python
# shell=False + 리스트 인자
subprocess.run(["ping", "-c", "3", host], shell=False)
```

## 테스트 방법

### 1. pytest 실행 (권장)
```bash
cd ch03-command-injection
pytest test_app.py -v
```

**테스트 항목:**
| 테스트 | 설명 |
|--------|------|
| `test_ping_valid` | 정상 IP 입력 테스트 |
| `test_injection_accepted` | 취약: 인젝션 허용 |
| `test_injection_blocked` | 안전: 인젝션 차단 |

### 2. Docker 테스트
```bash
docker-compose up -d

# 취약한 버전 테스트 (명령어 실행됨)
curl -X POST http://localhost:5001/ping -d "host=127.0.0.1; whoami"

# 안전한 버전 테스트 (차단됨)
curl -X POST http://localhost:5002/ping -d "host=127.0.0.1; whoami"

docker-compose down
```

### 3. 수동 테스트
1. http://localhost:5001 접속
2. Host 입력란에 `127.0.0.1; whoami` 입력
3. 명령어 실행 결과 확인 (취약점)
4. http://localhost:5002에서 동일 테스트
5. 에러 또는 차단 확인 (방어 성공)

## 체크리스트
- [ ] shell=True 사용하지 않기
- [ ] 명령어와 인자를 리스트로 분리
- [ ] 사용자 입력 화이트리스트 검증
- [ ] timeout 설정으로 DoS 방지
