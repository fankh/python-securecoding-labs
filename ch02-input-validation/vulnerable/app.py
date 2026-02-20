"""
입력값 검증 취약점 실습 - 취약한 코드
"""
from flask import Flask, request, jsonify
import re

app = Flask(__name__)


@app.route("/")
def index():
    return """
    <h1>입력값 검증 취약점 실습</h1>
    <h2>사용자 등록</h2>
    <form action="/register" method="POST">
        <input name="username" placeholder="Username"><br><br>
        <input name="email" placeholder="Email"><br><br>
        <input name="age" placeholder="Age"><br><br>
        <input name="url" placeholder="Website URL"><br><br>
        <button type="submit">Register</button>
    </form>
    <hr>
    <h3>취약점</h3>
    <ul>
        <li>입력 길이 제한 없음</li>
        <li>블랙리스트 기반 필터링</li>
        <li>정규식 ReDoS 취약</li>
        <li>타입 검증 없음</li>
    </ul>
    """


@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "")
    email = request.form.get("email", "")
    age = request.form.get("age", "")
    url = request.form.get("url", "")

    errors = []

    # 취약점: 블랙리스트 기반 필터링 (우회 가능)
    blacklist = ["<script>", "javascript:", "onerror"]
    for bad in blacklist:
        if bad.lower() in username.lower():
            errors.append("Username contains forbidden characters")
            break

    # 취약점: ReDoS 취약 정규식
    # aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa! 입력 시 매우 느림
    evil_regex = re.compile(r"^([a-zA-Z0-9]+)+@")
    if email and not evil_regex.match(email):
        errors.append("Invalid email format")

    # 취약점: 타입 검증 없음
    if age:
        try:
            age_int = int(age)  # 오버플로우 가능
        except:
            pass  # 에러 무시

    # 취약점: URL 검증 없이 저장
    # file://, javascript: 등 위험한 프로토콜 허용

    if errors:
        return jsonify({"status": "error", "errors": errors})

    return jsonify({
        "status": "success",
        "data": {"username": username, "email": email, "age": age, "url": url}
    })


@app.route("/search", methods=["GET"])
def search():
    """ReDoS 테스트 엔드포인트"""
    pattern = request.args.get("pattern", "")
    text = request.args.get("text", "")

    # 취약점: 사용자 제공 정규식 직접 실행
    try:
        regex = re.compile(pattern)
        match = regex.search(text)
        return jsonify({"matched": bool(match)})
    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
