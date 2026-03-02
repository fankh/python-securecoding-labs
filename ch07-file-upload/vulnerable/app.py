"""
파일 업로드 취약점 실습 - 취약한 코드
"""
from flask import Flask, request, send_from_directory
import os

app = Flask(__name__)
app.json.ensure_ascii = False
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def index():
    files = os.listdir(UPLOAD_FOLDER)
    file_list = "".join([f'<li><a href="/uploads/{f}">{f}</a></li>' for f in files])
    return f"""
    <h1>파일 업로드 취약점 실습</h1>
    <form action="/upload" method="POST" enctype="multipart/form-data">
        <input type="file" name="file"><br><br>
        <button type="submit">Upload</button>
    </form>
    <hr>
    <h2>업로드된 파일</h2>
    <ul>{file_list}</ul>
    <hr>
    <h3>취약점</h3>
    <ul>
        <li>확장자 검증 없음</li>
        <li>MIME 타입 검증 없음</li>
        <li>파일명 검증 없음 (Path Traversal)</li>
        <li>실행 가능 파일 업로드 가능</li>
    </ul>
    <h3>공격 예시</h3>
    <ul>
        <li>실행 파일(.php, .exe 등) 업로드</li>
        <li>../../../etc/passwd 파일명 사용</li>
        <li>.htaccess 업로드</li>
    </ul>
    """


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file:
        return "No file", 400

    # 취약점: 파일명 검증 없이 저장
    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    return f'File uploaded: <a href="/uploads/{filename}">{filename}</a>'


@app.route("/uploads/<path:filename>")
def serve_file(filename):
    # 취약점: Path Traversal 가능
    return send_from_directory(UPLOAD_FOLDER, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
