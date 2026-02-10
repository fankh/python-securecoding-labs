"""
Pickle 역직렬화 취약점 실습 - 취약한 코드
경고: 이 코드는 교육 목적으로만 사용하세요!
"""
from flask import Flask, request, jsonify
import pickle
import base64

app = Flask(__name__)

# 간단한 세션 저장소
sessions = {}


class UserSession:
    def __init__(self, username, role="user"):
        self.username = username
        self.role = role
        self.preferences = {"theme": "light", "language": "ko"}


@app.route("/")
def index():
    return """
    <h1>Pickle 역직렬화 취약점 실습</h1>
    <h2>세션 저장/불러오기</h2>
    <form action="/save_session" method="POST">
        <input name="username" placeholder="Username"><br><br>
        <button type="submit">Create Session</button>
    </form>
    <h2>세션 로드 (Base64 Pickle)</h2>
    <form action="/load_session" method="POST">
        <textarea name="session_data" rows="5" cols="60" placeholder="Base64 encoded pickle data"></textarea><br><br>
        <button type="submit">Load Session</button>
    </form>
    <hr>
    <h3>공격 방법</h3>
    <p>exploit.py를 실행하여 악성 pickle 페이로드를 생성하세요.</p>
    <pre>python exploit.py</pre>
    """


@app.route("/save_session", methods=["POST"])
def save_session():
    """세션을 pickle로 직렬화하여 반환"""
    username = request.form.get("username", "guest")
    session = UserSession(username)

    # pickle로 직렬화
    pickled = pickle.dumps(session)
    encoded = base64.b64encode(pickled).decode()

    return jsonify({
        "status": "success",
        "message": f"Session created for {username}",
        "session_data": encoded,
        "warning": "이 데이터를 load_session에 붙여넣어 테스트하세요"
    })


@app.route("/load_session", methods=["POST"])
def load_session():
    """취약점: 사용자 입력을 pickle.loads()로 역직렬화"""
    session_data = request.form.get("session_data", "")

    try:
        # 취약한 코드 - 신뢰할 수 없는 데이터를 pickle.loads()
        decoded = base64.b64decode(session_data)
        session = pickle.loads(decoded)  # RCE 취약점!

        return jsonify({
            "status": "success",
            "username": getattr(session, "username", "unknown"),
            "role": getattr(session, "role", "unknown"),
            "preferences": getattr(session, "preferences", {})
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
