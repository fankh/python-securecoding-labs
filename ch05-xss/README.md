# Chapter 05: XSS (Cross-Site Scripting) 실습

## 학습 목표
- Reflected XSS vs Stored XSS 이해
- 출력 인코딩의 중요성
- CSP 헤더 설정

## 실습 환경

```bash
docker-compose up -d

# 취약한 버전: http://localhost:5001
# 안전한 버전: http://localhost:5002
```

## 공격 실습

### Stored XSS
메시지 입력창에:
```html
<script>alert('XSS')</script>
<img src=x onerror="alert('XSS')">
<svg onload="alert('XSS')">
```

### Reflected XSS
검색창에:
```html
<script>alert(document.cookie)</script>
```

## 방어 기법

### 1. 출력 인코딩 (Jinja2)
```python
# 자동 이스케이프 (기본값)
{{ user_input }}

# 명시적 이스케이프
{{ user_input | e }}
```

### 2. CSP 헤더
```python
response.headers['Content-Security-Policy'] = "script-src 'self'"
```

### 3. Bleach로 HTML 정화
```python
import bleach
clean_html = bleach.clean(user_input, tags=['b', 'i', 'u'])
```

## 테스트 방법

### 1. pytest 실행 (권장)
```bash
cd ch05-xss
pytest test_app.py -v
```

**예상 출력:**
```
test_app.py::TestVulnerableApp::test_index PASSED                    [ 20%]
test_app.py::TestVulnerableApp::test_post_message PASSED             [ 40%]
test_app.py::TestSecureApp::test_index PASSED                        [ 60%]
test_app.py::TestSecureApp::test_post_message PASSED                 [ 80%]
test_app.py::TestSecureApp::test_csp_header PASSED                   [100%]

============================== 5 passed in 0.42s ==============================
```

**테스트 항목:**
| 테스트 | 설명 | 결과 |
|--------|------|------|
| `test_post_message` | 정상 메시지 등록 테스트 | 두 버전 모두 통과 |
| `test_xss_stored` | 취약: `<script>alert('XSS')</script>` 저장 | 취약 버전만 통과 |
| `test_csp_header` | 안전: Content-Security-Policy 헤더 확인 | 안전 버전만 통과 |

**개별 테스트 실행:**
```bash
# XSS 취약점 테스트만 실행
pytest test_app.py -k "xss" -v

# CSP 헤더 테스트만 실행
pytest test_app.py -k "csp" -v
```

### 2. Docker 테스트
```bash
docker-compose up -d

# 취약한 버전 - Stored XSS
curl -X POST http://localhost:5001/post \
  -d "name=Hacker&message=<script>alert('XSS')</script>"

# 안전한 버전 - CSP 헤더 확인
curl -I http://localhost:5002/ | grep -i content-security-policy

docker-compose down
```

### 3. 수동 테스트
1. http://localhost:5001 접속
2. 메시지에 `<script>alert('XSS')</script>` 입력
3. 페이지 새로고침 후 알림창 확인 (취약점)
4. http://localhost:5002에서 동일 테스트
5. 스크립트 실행 안됨 확인 (방어 성공)

## 체크리스트
- [ ] 템플릿 자동 이스케이프 활성화
- [ ] |safe 필터 사용 금지
- [ ] CSP 헤더 설정
- [ ] httpOnly 쿠키 사용
