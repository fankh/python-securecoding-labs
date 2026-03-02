# Chapter 12: 공급망 보안 (Supply Chain Security)

## 학습 목표
- 의존성 취약점 검사 방법 이해
- SBOM (Software Bill of Materials) 생성
- 패키지 무결성 검증 (해시 확인)
- 타이포스쿼팅 공격 인식

## 취약점 설명

### 1. 취약한 의존성
알려진 보안 취약점이 있는 오래된 패키지 사용

### 2. 타이포스쿼팅
유사한 이름의 악성 패키지 설치 유도

### 3. 의존성 혼동 (Dependency Confusion)
내부 패키지명과 동일한 공개 패키지 공격

### 4. 패키지 변조
설치 과정에서 패키지 무결성 훼손

## 실습 파일

```
ch12-supply-chain/
├── requirements_vulnerable.txt  # 취약한 의존성 예시
├── requirements_secure.txt      # 안전한 의존성
├── scan_dependencies.py         # 취약점 스캔 도구
├── check_hashes.py              # 해시 검증 도구
├── Dockerfile
└── docker-compose.yml
```

## 실습 방법

### 1. 의존성 스캔 실행
```bash
# Docker 사용
docker-compose up --build

# 또는 직접 실행
pip install pip-audit safety cyclonedx-bom
python scan_dependencies.py
```

### 2. 취약점 확인

**pip-audit 사용:**
```bash
pip-audit -r requirements_vulnerable.txt
```

**safety 사용:**
```bash
safety check -r requirements_vulnerable.txt --full-report
```

### 3. SBOM 생성
```bash
pip install cyclonedx-bom
cyclonedx-py requirements requirements_secure.txt -o sbom.json --format json
```

### 4. 해시 검증
```bash
python check_hashes.py
pip install --require-hashes -r requirements_locked.txt
```

## 보안 도구

### pip-audit
```bash
pip install pip-audit
pip-audit                    # 현재 환경 검사
pip-audit -r requirements.txt # 파일 검사
```

### safety
```bash
pip install safety
safety check                  # 현재 환경 검사
safety check -r requirements.txt --full-report
```

### python -m bandit(정적 분석)
```bash
pip install bandit
python -m bandit-r src/
```

## CI/CD 통합 예시

### GitHub Actions
```yaml
name: Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pip-audit safety bandit

      - name: pip-audit scan
        run: pip-audit -r requirements.txt

      - name: safety scan
        run: safety check -r requirements.txt

      - name: python -m banditscan
        run: python -m bandit-r src/ -f json -o bandit-report.json
```

## 모범 사례

1. **버전 고정 (Pinning)**
   ```
   # 나쁨
   flask>=2.0

   # 좋음
   flask==3.0.0
   ```

2. **해시 검증**
   ```
   flask==3.0.0 \
       --hash=sha256:...
   ```

3. **정기적인 업데이트**
   ```bash
   pip list --outdated
   pip-audit --fix
   ```

4. **신뢰할 수 있는 소스만 사용**
   ```
   # pip.conf
   [global]
   index-url = https://pypi.org/simple/
   trusted-host = pypi.org
   ```

5. **SBOM 유지**
   - 모든 의존성 추적
   - 취약점 발견 시 빠른 대응

## 테스트 방법

### 1. pytest 실행 (권장)
```bash
cd ch12-supply-chain
python -m pytest test_tools.py -v
```

**예상 출력:**
```
test_tools.py::test_vulnerable_requirements_exist PASSED             [ 20%]
test_tools.py::test_secure_requirements_exist PASSED                 [ 40%]
test_tools.py::test_scan_script_syntax PASSED                        [ 60%]
test_tools.py::test_check_hashes_syntax PASSED                       [ 80%]
test_tools.py::test_secure_uses_pinned_versions PASSED               [100%]

============================== 5 passed in 0.35s ==============================
```

**테스트 항목:**
| 테스트 | 설명 | 결과 |
|--------|------|------|
| `test_vulnerable_requirements_exist` | 취약 의존성 파일(`requirements_vulnerable.txt`) 존재 확인 | 통과 |
| `test_secure_requirements_exist` | 안전 의존성 파일(`requirements_secure.txt`) 존재 확인 | 통과 |
| `test_scan_script_syntax` | 스캔 스크립트(`scan_dependencies.py`) 문법 확인 | 통과 |
| `test_check_hashes_syntax` | 해시 검증 스크립트(`check_hashes.py`) 문법 확인 | 통과 |
| `test_secure_uses_pinned_versions` | 버전 고정(==) 사용 확인 (>= 사용 금지) | 통과 |

**참고:**
- pytest는 파일 존재 및 기본 구문만 테스트
- 실제 취약점 스캔은 Docker 또는 직접 스캔 섹션 참고
- pip-audit, safety 도구를 사용한 의존성 검사는 수동 실행 필요

**개별 테스트 실행:**
```bash
# 특정 테스트만 실행
python -m pytest test_tools.py::test_vulnerable_requirements_exist -v
python -m pytest test_tools.py::test_secure_uses_pinned_versions -v

# 파일 존재 테스트만 실행
python -m pytest test_tools.py -k "exist" -v

# 스크립트 문법 테스트만 실행
python -m pytest test_tools.py -k "syntax" -v
```

### 2. Docker 테스트
```bash
cd ch12-supply-chain
docker-compose up --build

# 스캔 결과 확인
docker-compose logs
```

### 3. 직접 스캔 실행
```bash
# 도구 설치
pip install pip-audit safety cyclonedx-bom

# 취약한 의존성 스캔
pip-audit -r requirements_vulnerable.txt
safety check -r requirements_vulnerable.txt

# 안전한 의존성 스캔
pip-audit -r requirements_secure.txt

# SBOM 생성
python scan_dependencies.py
```

### 4. 수동 확인
1. `requirements_vulnerable.txt` - 버전 범위 사용 (>=)
2. `requirements_secure.txt` - 정확한 버전 고정 (==)
3. `pip-audit` 결과 비교
4. 취약점 개수 차이 확인

## 참고 자료

- [OWASP Dependency-Check](https://owasp.org/www-project-dependency-check/)
- [PyPI Security](https://pypi.org/security/)
- [CycloneDX SBOM](https://cyclonedx.org/)
- [Snyk Vulnerability Database](https://security.snyk.io/)
