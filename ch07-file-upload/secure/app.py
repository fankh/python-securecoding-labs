"""
안전한 파일 업로드 실습
"""
from flask import Flask, request, send_from_directory, abort
from werkzeug.utils import secure_filename
import os
import uuid
import magic

app = Flask(__name__)
app.json.ensure_ascii = False
UPLOAD_FOLDER = "uploads_secure"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 허용된 확장자 및 MIME 타입
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt'}
ALLOWED_MIMETYPES = {
    'image/png', 'image/jpeg', 'image/gif',
    'application/pdf', 'text/plain'
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_mimetype(file_stream):
    """실제 파일 내용으로 MIME 타입 확인"""
    mime = magic.from_buffer(file_stream.read(2048), mime=True)
    file_stream.seek(0)
    return mime in ALLOWED_MIMETYPES


@app.route("/")
def index():
    files = os.listdir(UPLOAD_FOLDER)
    file_list = "".join([f'<li><a href="/uploads/{f}">{f}</a></li>' for f in files])
    return f"""
    <h1>안전한 파일 업로드 실습</h1>
    <form action="/upload" method="POST" enctype="multipart/form-data">
        <input type="file" name="file" accept=".png,.jpg,.jpeg,.gif,.pdf,.txt"><br><br>
        <button type="submit">Upload</button>
    </form>
    <hr>
    <h2>업로드된 파일</h2>
    <ul>{file_list}</ul>
    <hr>
    <h3>적용된 보안 조치</h3>
    <ul>
        <li>확장자 화이트리스트</li>
        <li>MIME 타입 검증 (매직 바이트)</li>
        <li>secure_filename() 사용</li>
        <li>UUID로 파일명 변경</li>
        <li>파일 크기 제한</li>
    </ul>
    """


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or file.filename == '':
        return "No file selected", 400

    # 1. 확장자 검증
    if not allowed_file(file.filename):
        return "File type not allowed", 400

    # 2. 파일 크기 검증
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        return "File too large (max 5MB)", 400

    # 3. MIME 타입 검증
    if not validate_mimetype(file.stream):
        return "Invalid file content", 400

    # 4. 안전한 파일명 생성
    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    new_filename = f"{uuid.uuid4().hex}.{ext}"

    filepath = os.path.join(UPLOAD_FOLDER, new_filename)
    file.save(filepath)

    return f'File uploaded: <a href="/uploads/{new_filename}">{new_filename}</a>'


@app.route("/uploads/<filename>")
def serve_file(filename):
    # secure_filename으로 한번 더 검증
    safe_filename = secure_filename(filename)
    if safe_filename != filename:
        abort(404)
    return send_from_directory(UPLOAD_FOLDER, safe_filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
