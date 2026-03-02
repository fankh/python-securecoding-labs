# Chapter 07: 파일 업로드 보안

## 학습 목표
- 안전하지 않은 파일 업로드의 위험성 이해
- 파일 확장자 및 MIME 타입 검증 방법 학습
- 경로 탐색(Path Traversal) 공격 방어
- 안전한 파일명 생성 기법 적용

## 실습 환경

```bash
cd ch07-file-upload
docker-compose up --build

# 취약한 버전: http://localhost:5001
# 안전한 버전: http://localhost:5002
```

## 취약점 비교

| 항목 | 취약한 버전 (5001) | 안전한 버전 (5002) |
|------|-------------------|-------------------|
| 확장자 검증 | 없음 (모든 파일 허용) | 화이트리스트 (png, jpg, gif, pdf, txt) |
| MIME 타입 검증 | 없음 | 매직 바이트 검사 (`python-magic`) |
| 파일명 처리 | 원본 파일명 그대로 저장 | `secure_filename()` + UUID 변환 |
| 파일 크기 제한 | 없음 | 5MB 제한 |
| 경로 탐색 방어 | 없음 (`../` 허용) | `secure_filename()` 적용 |

## 공격 실습 (취약한 버전)

### 공격 1: 위험한 확장자 업로드

```powershell
# PHP 악성 파일 생성
Set-Content -Path test.php -Value '<?php system("whoami"); ?>'

# 업로드
curl.exe -F "file=@test.php" http://localhost:5001/upload
# 결과: 업로드 성공 — 서버에서 실행 가능한 스크립트가 저장됨
```

취약한 버전은 `.php`, `.exe`, `.sh` 등 어떤 확장자든 업로드를 허용합니다.

### 공격 2: 경로 탐색 (Path Traversal)

```bash
# 상위 디렉토리에 파일 생성 시도
curl.exe -F "file=@test.txt;filename=../../../tmp/evil.txt" \
     http://localhost:5001/upload
```

`../` 를 포함한 파일명으로 업로드 폴더를 탈출하여 임의 경로에 파일을 생성할 수 있습니다.

### 공격 3: MIME 타입 위조

```bash
# Content-Type을 image/jpeg로 위장하여 PHP 파일 업로드
curl.exe -F "file=@test.php;type=image/jpeg" \
     http://localhost:5001/upload
# 결과: Content-Type만 검사하면 우회 가능
```

### 공격 4: 확장자 우회 기법

```
test.php.jpg       # 이중 확장자
test.php%00.jpg    # 널 바이트 (구버전 취약점)
test.PhP           # 대소문자 변형
.htaccess          # 서버 설정 파일 업로드
```

## 방어 확인 (안전한 버전)

```bash
# 위험한 확장자 → 차단됨
curl.exe -F "file=@test.php" http://localhost:5002/upload
# 결과: "File type not allowed" (400)

# 정상 파일 → 업로드 성공 (UUID 파일명으로 변환됨)
echo "hello" > test.txt
curl.exe -F "file=@test.txt" http://localhost:5002/upload
# 결과: 업로드 성공, 파일명이 UUID로 변경됨 (예: a1b2c3d4.txt)
```

## 방어 기법

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

> Content-Type 헤더는 클라이언트가 위조할 수 있으므로, 파일 내용(매직 바이트)으로 실제 타입을 확인해야 합니다.

### 3. 안전한 파일명 생성

```python
from werkzeug.utils import secure_filename
import uuid

# 1. 위험 문자 제거
safe_name = secure_filename(file.filename)

# 2. UUID로 파일명 변경 (예측 불가)
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

## 테스트 방법

### 1. pytest 실행 (권장)

```bash
cd ch07-file-upload
python -m pytest test_app.py -v
```

**예상 출력:**
```
test_app.py::TestVulnerableApp::test_index PASSED                    [ 16%]
test_app.py::TestVulnerableApp::test_upload_txt PASSED               [ 33%]
test_app.py::TestVulnerableApp::test_upload_php PASSED               [ 50%]
test_app.py::TestSecureApp::test_index PASSED                        [ 66%]
test_app.py::TestSecureApp::test_upload_txt PASSED                   [ 83%]
test_app.py::TestSecureApp::test_reject_php PASSED                   [100%]

============================== 6 passed in 0.52s ==============================
```

**테스트 항목:**
| 테스트 | 설명 | 결과 |
|--------|------|------|
| `test_upload_txt` | 정상 텍스트 파일 업로드 | 두 버전 모두 통과 |
| `test_upload_php` | 취약: PHP 파일 허용 | 취약 버전만 통과 |
| `test_reject_php` | 안전: PHP 파일 거부 (400) | 안전 버전만 통과 |

**개별 테스트 실행:**
```bash
python -m pytest test_app.py::TestVulnerableApp -v
python -m pytest test_app.py::TestSecureApp -v
```

### 2. 수동 테스트 (브라우저)

#### 취약한 버전 테스트
1. http://localhost:5001 접속
2. `.php` 확장자 파일 업로드 → 성공 (취약점)
3. 업로드된 파일 목록에서 파일명이 원본 그대로인지 확인

#### 안전한 버전 테스트
1. http://localhost:5002 접속
2. `.php` 확장자 파일 업로드 → "File type not allowed" 에러 (방어 성공)
3. `.txt` 파일 업로드 → 성공, 파일명이 UUID로 변경된 것 확인

## 체크리스트
- [ ] 확장자 화이트리스트 적용
- [ ] MIME 타입 검증 (매직 바이트)
- [ ] `secure_filename()` 사용
- [ ] UUID로 파일명 변경
- [ ] 파일 크기 제한 설정
- [ ] 업로드 폴더를 웹 루트 외부에 배치

## 참고 자료
- [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [python-magic Documentation](https://github.com/ahupp/python-magic)
- [Werkzeug secure_filename](https://werkzeug.palletsprojects.com/en/3.0.x/utils/#werkzeug.utils.secure_filename)
