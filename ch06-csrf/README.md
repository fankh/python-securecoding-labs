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

## 테스트 방법

### 1. pytest 실행 (권장)
```bash
cd ch06-csrf
pytest test_app.py -v
```

**테스트 항목:**
| 테스트 | 설명 |
|--------|------|
| `test_index` | 메인 페이지 접근 |
| (취약 버전) | CSRF 토큰 없이 요청 허용 |
| (안전 버전) | CSRF 토큰 검증 |

### 2. Docker 테스트
```bash
docker-compose up -d

# 취약한 버전 - CSRF 공격 시뮬레이션
# 1. 브라우저에서 http://localhost:5001 접속 후 alice로 로그인
# 2. 새 탭에서 아래 HTML 파일 열기

# 안전한 버전 - CSRF 토큰 필요
curl -X POST http://localhost:5002/transfer \
  -d "to=attacker&amount=100"
# 결과: CSRF 토큰 누락으로 실패

docker-compose down
```

### 3. 수동 테스트
1. http://localhost:5001 접속, alice로 로그인
2. 개발자 도구에서 CSRF 토큰 없이 송금 요청
3. 송금 성공 확인 (취약점)
4. http://localhost:5002에서 동일 테스트
5. CSRF 토큰 없으면 거부 확인 (방어 성공)

## 체크리스트
- [ ] CSRF 토큰 구현
- [ ] POST 요청만 허용
- [ ] SameSite=Strict 쿠키
