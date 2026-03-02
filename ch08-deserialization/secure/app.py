"""
안전한 직렬화 실습 - JSON 및 itsdangerous 사용
"""
from flask import Flask, request, jsonify
from itsdangerous import URLSafeSerializer, BadSignature
import json
import os

app = Flask(__name__)
app.json.ensure_ascii = False

# 시크릿 키 (환경 변수에서 로드)
SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production")
serializer = URLSafeSerializer(SECRET_KEY)


class UserSession:
    def __init__(self, username, role="user"):
        self.username = username
        self.role = role
        self.preferences = {"theme": "light", "language": "ko"}

    def to_dict(self):
        return {
            "username": self.username,
            "role": self.role,
            "preferences": self.preferences
        }

    @classmethod
    def from_dict(cls, data):
        session = cls(data.get("username", "guest"))
        session.role = data.get("role", "user")
        session.preferences = data.get("preferences", {})
        return session


@app.route("/")
def index():
    return """
    <h1>안전한 직렬화 실습</h1>
    <h2>세션 저장/불러오기 (JSON + 서명)</h2>
    <form action="/save_session" method="POST">
        <input name="username" placeholder="Username"><br><br>
        <button type="submit">Create Session</button>
    </form>
    <h2>세션 로드 (서명된 토큰)</h2>
    <form action="/load_session" method="POST">
        <textarea name="session_token" rows="3" cols="60" placeholder="Signed session token"></textarea><br><br>
        <button type="submit">Load Session</button>
    </form>
    <hr>
    <h3>적용된 보안 조치</h3>
    <ul>
        <li>pickle 대신 JSON 사용 (코드 실행 불가)</li>
        <li>itsdangerous로 서명하여 변조 방지</li>
        <li>화이트리스트 필드만 역직렬화</li>
    </ul>
    """


@app.route("/save_session", methods=["POST"])
def save_session():
    """세션을 JSON으로 직렬화하고 서명"""
    username = request.form.get("username", "guest")

    # 입력값 검증
    if not username.isalnum() or len(username) > 50:
        return jsonify({"status": "error", "message": "Invalid username"})

    session = UserSession(username)

    # JSON으로 변환 후 서명
    session_data = session.to_dict()
    signed_token = serializer.dumps(session_data)

    return jsonify({
        "status": "success",
        "message": f"Session created for {username}",
        "session_token": signed_token
    })


@app.route("/load_session", methods=["POST"])
def load_session():
    """서명된 토큰을 검증하고 역직렬화"""
    session_token = request.form.get("session_token", "")

    try:
        # 서명 검증 및 역직렬화 (변조 시 BadSignature 예외)
        session_data = serializer.loads(session_token)

        # 화이트리스트 필드만 추출
        allowed_fields = {"username", "role", "preferences"}
        safe_data = {k: v for k, v in session_data.items() if k in allowed_fields}

        session = UserSession.from_dict(safe_data)

        return jsonify({
            "status": "success",
            "username": session.username,
            "role": session.role,
            "preferences": session.preferences
        })
    except BadSignature:
        return jsonify({"status": "error", "message": "Invalid or tampered token"})
    except Exception as e:
        return jsonify({"status": "error", "message": "Failed to load session"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
