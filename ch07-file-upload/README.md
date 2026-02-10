# Chapter 07: 파일 업로드 보안

## 학습 목표
- 안전하지 않은 파일 업로드의 위험성 이해
- 파일 확장자 및 MIME 타입 검증 방법 학습
- 경로 탐색(Path Traversal) 공격 방어
- 안전한 파일명 생성 기법 적용

## 취약점 설명

### 1. 확장자 검증 없음
모든 파일 유형 업로드 허용 (스크립트 파일, 실행 파일 등)

### 2. MIME 타입 검증 없음
Content-Type 헤더만 검사하거나 아예 검사하지 않음

### 3. 경로 탐색 (Path Traversal)
`../` 를 포함한 파일명으로 디렉토리 탈출 가능

### 4. 원본 파일명 사용
예측 가능한 파일명으로 직접 접근 가능

### 5. 파일 크기 제한 없음
대용량 파일 업로드로 DoS 공격 가능

## 실습 방법

```bash
docker-compose up --build
```

- 취약한 버전: http://localhost:5001
- 안전한 버전: http://localhost:5002

## 공격 시나리오

### 1. 스크립트 파일 업로드
```bash
# 허용되지 않은 확장자 테스트
echo 'test content' > test.php
curl -F "file=@test.php" http://localhost:5001/upload

# 취약한 버전: 업로드 성공
# 안전한 버전: "File type not allowed" 에러
```

### 2. 경로 탐색 공격
```bash
# 상위 디렉토리에 파일 생성 시도
curl -F "file=@test.txt;filename=../../../tmp/evil.txt" \
     http://localhost:5001/upload
```

### 3. 확장자 우회 기법
```
# 이중 확장자
test.php.jpg

# 널 바이트 (구버전 취약점)
test.php%00.jpg

# 대소문자 변형
test.PhP
```

### 4. MIME 타입 위조
```bash
# Content-Type을 image/jpeg로 위장
curl -F "file=@test.php;type=image/jpeg" \
     http://localhost:5001/upload
```

## 보안 조치

### 1. 확장자 화이트리스트
```python
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
```

### 2. MIME 타입 검증 (매직 바이트)
```python
import magic

def validate_mimetype(file_stream):
    mime = magic.from_buffer(file_stream.read(2048), mime=True)
    file_stream.seek(0)
    return mime in ALLOWED_MIMETYPES
```

### 3. 안전한 파일명 생성
```python
from werkzeug.utils import secure_filename
import uuid

# 1. 위험 문자 제거
safe_name = secure_filename(file.filename)

# 2. UUID로 파일명 변경
new_filename = f"{uuid.uuid4().hex}.{ext}"
```

### 4. 파일 크기 제한
```python
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

file.seek(0, 2)
size = file.tell()
file.seek(0)

if size > MAX_FILE_SIZE:
    return "File too large", 400
```

### 5. 파일 저장 경로 분리
```python
# 웹 루트 외부에 저장
UPLOAD_FOLDER = "/var/uploads"  # 웹 서버가 직접 접근 불가

# 다운로드 시 send_from_directory 사용
return send_from_directory(UPLOAD_FOLDER, safe_filename)
```

## 검증 체크리스트

| 항목 | 취약 버전 | 안전 버전 |
|------|----------|----------|
| 확장자 검증 | ✗ | ✓ 화이트리스트 |
| MIME 검증 | ✗ | ✓ 매직 바이트 |
| secure_filename | ✗ | ✓ |
| UUID 파일명 | ✗ | ✓ |
| 크기 제한 | ✗ | ✓ 5MB |
| 경로 탐색 방어 | ✗ | ✓ |

## 참고 자료

- [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [python-magic Documentation](https://github.com/ahupp/python-magic)
- [Werkzeug secure_filename](https://werkzeug.palletsprojects.com/en/3.0.x/utils/#werkzeug.utils.secure_filename)
