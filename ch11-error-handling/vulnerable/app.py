"""
취약한 에러 처리 및 로깅 실습
- 민감 정보가 에러 메시지에 노출
- 스택 트레이스가 사용자에게 표시
- 안전하지 않은 로깅
"""
from flask import Flask, request, jsonify
import sqlite3
import logging
import traceback

app = Flask(__name__)

# 취약점: 로그에 민감 정보 기록
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app.log'
)

def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT,
            credit_card TEXT
        )
    ''')
    # 테스트 데이터
    try:
        conn.execute(
            "INSERT INTO users (username, password, email, credit_card) VALUES (?, ?, ?, ?)",
            ("admin", "admin123", "admin@example.com", "4111-1111-1111-1111")
        )
        conn.commit()
    except:
        pass
    conn.close()


@app.route("/")
def index():
    return """
    <h1>취약한 에러 처리 실습</h1>
    <h3>취약점</h3>
    <ul>
        <li>상세 에러 메시지 노출</li>
        <li>스택 트레이스 노출</li>
        <li>민감 정보 로깅</li>
        <li>디버그 모드 활성화</li>
    </ul>
    <h3>테스트</h3>
    <ul>
        <li><a href="/user?id=1">/user?id=1</a> - 정상 조회</li>
        <li><a href="/user?id=abc">/user?id=abc</a> - 타입 에러</li>
        <li><a href="/user?id=999">/user?id=999</a> - 없는 사용자</li>
        <li><a href="/login">/login</a> - 로그인 테스트</li>
        <li><a href="/debug">/debug</a> - 디버그 정보</li>
    </ul>
    """


@app.route("/user")
def get_user():
    user_id = request.args.get("id")

    # 취약점: 로그에 사용자 입력 그대로 기록
    logging.info(f"User lookup requested for ID: {user_id}")

    try:
        # 취약점: 타입 변환 에러 시 상세 정보 노출
        user_id = int(user_id)

        conn = get_db()
        cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            # 취약점: 시스템 구조 정보 노출
            return jsonify({
                "error": f"User not found in database table 'users'",
                "query": f"SELECT * FROM users WHERE id = {user_id}",
                "database": "users.db"
            }), 404

        # 취약점: 민감 정보를 로그에 기록
        logging.debug(f"User found: {dict(user)}")

        return jsonify(dict(user))

    except Exception as e:
        # 취약점: 전체 스택 트레이스 노출
        error_detail = traceback.format_exc()
        logging.error(f"Error: {error_detail}")

        return jsonify({
            "error": str(e),
            "type": type(e).__name__,
            "traceback": error_detail
        }), 500


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return """
        <form method="POST">
            <input name="username" placeholder="Username"><br>
            <input name="password" type="password" placeholder="Password"><br>
            <button type="submit">Login</button>
        </form>
        """

    username = request.form.get("username")
    password = request.form.get("password")

    # 취약점: 패스워드를 평문으로 로깅
    logging.info(f"Login attempt: username={username}, password={password}")

    conn = get_db()
    cursor = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, password)
    )
    user = cursor.fetchone()
    conn.close()

    if user:
        # 취약점: 민감 정보 로깅
        logging.info(f"Login successful for user: {dict(user)}")
        return f"Welcome {username}! Credit Card: {user['credit_card']}"
    else:
        # 취약점: 사용자 존재 여부 노출 (사용자 열거 공격)
        conn = get_db()
        cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
        exists = cursor.fetchone()
        conn.close()

        if exists:
            return "Invalid password for existing user", 401
        else:
            return "Username does not exist in our system", 401


@app.route("/debug")
def debug_info():
    # 취약점: 디버그 정보 노출
    import sys
    import os

    return jsonify({
        "python_version": sys.version,
        "platform": sys.platform,
        "current_directory": os.getcwd(),
        "environment": dict(os.environ),
        "modules": list(sys.modules.keys())
    })


if __name__ == "__main__":
    init_db()
    # 취약점: 프로덕션에서 디버그 모드 활성화
    app.run(host="0.0.0.0", port=5000, debug=True)
