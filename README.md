# Python Secure Coding Labs

실습 환경이 포함된 Python 시큐어코딩 교육 자료입니다.

## 과정 구성

| Chapter | 주제 | 실습 내용 |
|---------|------|----------|
| 01 | 보안 위협 개요 | 보안 도구 설치 및 환경 구성 |
| 02 | 입력값 검증 | 화이트리스트/블랙리스트 검증 |
| 03 | 명령어 인젝션 | OS Command Injection 공격/방어 |
| 04 | SQL 인젝션 | SQLi 공격/방어, ORM 활용 |
| 05 | XSS | Reflected/Stored XSS 공격/방어 |
| 06 | CSRF | CSRF 토큰 구현 |
| 07 | 파일 업로드 | 안전한 파일 업로드 구현 |
| 08 | 역직렬화 | Pickle 취약점 및 안전한 대안 |
| 09 | 인증/인가 | JWT, bcrypt, Argon2 구현 |
| 10 | 암호화 | AES-GCM, 키 관리 |
| 11 | 에러 처리 | 안전한 로깅 시스템 |
| 12 | 공급망 보안 | 의존성 검사, SBOM 생성 |

## 빠른 시작

```bash
# 저장소 클론
git clone https://github.com/your-org/python-securecoding-labs.git
cd python-securecoding-labs

# 전체 실습 환경 실행
docker-compose up -d

# 특정 챕터만 실행
cd ch04-sql-injection
docker-compose up -d
```

## 필수 요구사항

- Docker Desktop 4.0+
- Python 3.11+
- Git

## 프로젝트 구조

```
python-securecoding-labs/
├── docker-compose.yml          # 전체 실습 환경
├── ch01-security-overview/     # 보안 개요 및 환경 설정
├── ch02-input-validation/      # 입력값 검증
├── ch03-command-injection/     # 명령어 인젝션
├── ch04-sql-injection/         # SQL 인젝션
├── ch05-xss/                   # Cross-Site Scripting
├── ch06-csrf/                  # CSRF
├── ch07-file-upload/           # 파일 업로드
├── ch08-deserialization/       # 역직렬화
├── ch09-authentication/        # 인증 및 인가
├── ch10-encryption/            # 암호화
├── ch11-error-handling/        # 에러 처리 및 로깅
└── ch12-supply-chain/          # 공급망 보안
```

## 실습 방법

각 챕터 폴더에는 다음이 포함되어 있습니다:

- `vulnerable/` - 취약한 코드 예제
- `secure/` - 안전한 코드 예제
- `README.md` - 실습 가이드
- `docker-compose.yml` - 실습 환경
- `requirements.txt` - Python 의존성

### 일반적인 실습 순서

1. 취약한 코드 분석 (`vulnerable/`)
2. 공격 시나리오 실행
3. 안전한 코드 구현 (`secure/`)
4. 방어 효과 확인

## 주의사항

이 실습 환경은 **교육 목적**으로만 사용하세요. 실제 시스템에 대한 공격에 사용하지 마세요.

## 라이선스

MIT License
