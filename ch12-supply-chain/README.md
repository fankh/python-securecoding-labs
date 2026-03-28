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
유사한 이름의 악성 패키지 설치 유도 (예: `reqeusts` vs `requests`)

### 3. 의존성 혼동 (Dependency Confusion)
내부 패키지명과 동일한 공개 패키지로 공격

### 4. 패키지 변조
설치 과정에서 패키지 무결성 훼손

## 실습 파일

```
ch12-supply-chain/
├── requirements_vulnerable.txt  # 취약한 의존성 (알려진 CVE 포함)
├── requirements_secure.txt      # 안전한 의존성 (== 정확한 버전 고정)
├── scan_dependencies.py         # 취약점 스캔 도구
├── check_hashes.py              # 해시 검증 도구
├── Dockerfile
└── docker-compose.yml
```

## 실습 방법

### 1. pip-audit 설치

```powershell
pip install pip-audit
```

### 2. 취약한 의존성 스캔

```powershell
python -m pip_audit --no-deps -r requirements_vulnerable.txt
```

**실제 출력 결과:**
```
Found 33 known vulnerabilities in 7 packages
Name       Version ID               Fix Versions
---------- ------- ---------------- -------------
flask      2.2.0   PYSEC-2023-62    2.2.5,2.3.2
requests   2.25.0  PYSEC-2023-74    2.31.0
requests   2.25.0  CVE-2024-35195   2.32.0
requests   2.25.0  CVE-2024-47081   2.32.4
urllib3    1.26.5  PYSEC-2023-192   1.26.17,2.0.6
urllib3    1.26.5  PYSEC-2023-212   1.26.18,2.0.7
urllib3    1.26.5  CVE-2024-37891   1.26.19,2.2.2
jinja2     3.1.0   CVE-2024-22195   3.1.3
jinja2     3.1.0   CVE-2024-34064   3.1.4
jinja2     3.1.0   CVE-2024-56326   3.1.5
jinja2     3.1.0   CVE-2024-56201   3.1.5
jinja2     3.1.0   CVE-2025-27516   3.1.6
pillow     9.5.0   PYSEC-2023-175   10.0.1
pillow     9.5.0   PYSEC-2023-227   10.0.0
pillow     9.5.0   CVE-2023-50447   10.2.0
pillow     9.5.0   CVE-2023-4863    10.0.1
pillow     9.5.0   CVE-2024-28219   10.3.0
setuptools 65.0.0  CVE-2024-6345    70.0.0
...
```

### 3. 안전한 의존성 스캔

```powershell
python -m pip_audit --no-deps -r requirements_secure.txt
```

**실제 출력 결과:**
```
No known vulnerabilities found
```

### 4. 취약 vs 안전 비교

| 패키지 | 취약 버전 | CVE 수 | 안전 버전 |
|--------|----------|--------|----------|
| flask | 2.2.0 | 2 | 3.1.3 |
| requests | 2.25.0 | 4 | 2.32.4 |
| jinja2 | 3.1.0 | 5 | 3.1.6 |
| urllib3 | 1.26.5 | 9 | 2.6.3 |
| pillow | 9.5.0 | 5 | 12.1.1 |
| setuptools | 65.0.0 | 5 | 78.1.1 |

**핵심 차이:**
```
# 취약 (알려진 CVE가 있는 구버전)
flask==2.2.0

# 안전 (CVE가 수정된 최신 버전)
flask==3.1.3
```

### 5. Docker로 스캔 실행

```powershell
docker-compose up --build
```

### 6. SBOM 생성

```powershell
pip install cyclonedx-bom
python -m cyclonedx_py requirements requirements_secure.txt --of JSON -o sbom.json
```

### 7. 해시 검증

```powershell
python check_hashes.py
pip install --require-hashes -r requirements_locked.txt
```

> **주의:** `--require-hashes` 모드에서는 **모든 하위 의존성의 해시도 필요**합니다.
> `requirements_locked.txt`에 flask의 하위 의존성(Werkzeug, MarkupSafe, itsdangerous,
> click, blinker)을 모두 포함했습니다. 하위 의존성이 누락되면 설치가 실패합니다.

## 알려진 이슈 및 해결 방법

### 이슈 1: Pillow 9.0.0 빌드 오류 (Python 3.12+)

**증상:**
```
KeyError: '__version__'
```

**원인:** Pillow 9.0.0은 Python 3.12+ 환경에서 빌드할 수 없습니다 (내부 `__version__` 참조 방식 변경).

**해결:** `requirements_vulnerable.txt`에서 Pillow를 9.5.0으로 업데이트했습니다. 9.5.0도 다수의 CVE가 존재하므로 실습 목적은 동일합니다.

> **Python 버전 주의:** `pip-audit --no-deps`는 내부적으로 패키지 빌드를 시도할 수 있습니다.
> Pillow 9.5.0은 **Python 3.12 이하**에서만 빌드 가능합니다.
> Python 3.13+에서는 Docker 컨테이너(Python 3.11)로 실행하세요:
> ```powershell
> docker run --rm -v ${PWD}:/app -w /app python:3.11-slim bash -c "pip install pip-audit -q && python -m pip_audit --no-deps -r requirements_vulnerable.txt"
> ```

```
# 변경 전 (빌드 오류 발생)
pillow==9.0.0

# 변경 후 (정상 동작)
pillow==9.5.0
```

> **참고:** `pip-audit --no-deps` 모드는 실제 설치 없이 스캔하므로 빌드 오류가 발생하지 않습니다. 이 이슈는 `pip install -r requirements_vulnerable.txt`로 직접 설치할 때만 발생합니다.

### 이슈 2: --require-hashes 하위 의존성 해시 누락

**증상:**
```
ERROR: In --require-hashes mode, all requirements must have their versions pinned with ==
and hashes specified. Werkzeug from ... does not have a hash.
```

**원인:** `--require-hashes` 모드는 **직접 의존성뿐 아니라 모든 하위 의존성**의 해시도 요구합니다.

**해결:** `requirements_locked.txt`에 flask의 모든 하위 의존성과 해시를 포함했습니다:
- flask → werkzeug, markupsafe, itsdangerous, click, blinker, jinja2

```powershell
# 정상 동작하는 해시 검증 실습
pip install --require-hashes -r requirements_locked.txt
```

## 보안 도구

### pip-audit

```powershell
# 설치
pip install pip-audit

# requirements 파일 스캔 (의존성 해결 없이 빠르게)
python -m pip_audit --no-deps -r requirements.txt

# 현재 환경의 모든 패키지 스캔
python -m pip_audit

# JSON 형식 출력
python -m pip_audit --no-deps -r requirements.txt -f json
```

> **참고:** Windows에서 `pip-audit` 명령이 인식되지 않으면 `python -m pip_audit`을 사용하세요.
> `--no-deps` 플래그를 사용하면 의존성 설치 없이 빠르게 스캔합니다.

### bandit (정적 분석)

```powershell
pip install bandit
python -m bandit -r src/
```

## 모범 사례

### 1. 버전 고정 (Pinning)

```
# 나쁨 - 취약한 버전이 설치될 수 있음
flask>=2.0

# 좋음 - 정확한 버전 고정
flask==3.1.3
```

### 2. 해시 검증

```
flask==3.1.3 \
    --hash=sha256:...
```

### 3. 정기적인 업데이트

```powershell
pip list --outdated
python -m pip_audit --fix
```

### 4. 신뢰할 수 있는 소스만 사용

```
# pip.conf
[global]
index-url = https://pypi.org/simple/
trusted-host = pypi.org
```

### 5. SBOM 유지
- 모든 의존성 추적
- 취약점 발견 시 빠른 대응

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
          python-version: '3.12'

      - name: Install pip-audit
        run: pip install pip-audit

      - name: Scan vulnerable dependencies
        run: python -m pip_audit --no-deps -r requirements.txt
```

## 테스트 방법

### 1. pytest 실행 (권장)

```powershell
cd ch12-supply-chain
python -m pytest test_tools.py -v
```

**예상 출력:**
```
test_tools.py::TestDependencyFiles::test_vulnerable_requirements_exist PASSED
test_tools.py::TestDependencyFiles::test_secure_requirements_exist PASSED
test_tools.py::TestDependencyFiles::test_scan_script_syntax PASSED
test_tools.py::TestDependencyFiles::test_check_hashes_syntax PASSED
test_tools.py::TestDependencyFiles::test_secure_uses_pinned_versions PASSED
test_tools.py::TestDependencyFiles::test_vulnerable_has_old_versions PASSED
test_tools.py::TestDependencyFiles::test_secure_has_newer_versions PASSED
test_tools.py::TestDependencyFiles::test_vulnerable_no_hash_pinning PASSED

============================== 8 passed ==============================
```

**테스트 항목:**

| 테스트 | 설명 |
|--------|------|
| `test_vulnerable_requirements_exist` | 취약 의존성 파일 존재 확인 |
| `test_secure_requirements_exist` | 안전 의존성 파일 존재 확인 |
| `test_scan_script_syntax` | 스캔 스크립트 문법 확인 |
| `test_check_hashes_syntax` | 해시 검증 스크립트 문법 확인 |
| `test_secure_uses_pinned_versions` | 버전 고정(`==`) 사용 확인 |
| `test_vulnerable_has_old_versions` | 취약한 requirements에 알려진 구버전 포함 확인 |
| `test_secure_has_newer_versions` | 안전한 버전이 취약한 버전보다 높은지 비교 |
| `test_vulnerable_no_hash_pinning` | 취약한 requirements에 해시 핀닝 미사용 확인 |

**개별 테스트 실행:**
```powershell
python -m pytest test_tools.py -k "exist" -v
python -m pytest test_tools.py -k "syntax" -v
```

### 2. 수동 확인

1. `requirements_vulnerable.txt` - 알려진 CVE가 있는 구버전
2. `requirements_secure.txt` - CVE가 수정된 최신 버전 고정
3. `pip-audit` 결과 비교 (33 vulnerabilities vs 0~1)

## 참고 자료
- [OWASP Dependency-Check](https://owasp.org/www-project-dependency-check/)
- [PyPI Security](https://pypi.org/security/)
- [CycloneDX SBOM](https://cyclonedx.org/)
- [pip-audit GitHub](https://github.com/pypa/pip-audit)
