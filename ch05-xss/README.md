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

## 체크리스트
- [ ] 템플릿 자동 이스케이프 활성화
- [ ] |safe 필터 사용 금지
- [ ] CSP 헤더 설정
- [ ] httpOnly 쿠키 사용
