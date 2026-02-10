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

## 체크리스트
- [ ] shell=True 사용하지 않기
- [ ] 명령어와 인자를 리스트로 분리
- [ ] 사용자 입력 화이트리스트 검증
- [ ] timeout 설정으로 DoS 방지
