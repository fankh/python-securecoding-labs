"""
인증 취약점 실습 - 취약한 코드
경고: 이 코드는 교육 목적으로만 사용하세요!
"""
from flask import Flask, request, jsonify
import hashlib
import jwt
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
DB_PATH = "auth.db"

# 취약점: 하드코딩된 시크릿 키
JWT_SECRET = "secret123"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'user'
        )
    """)
    # 취약점: MD5 해시로 비밀번호 저장
    admin_pass = hashlib.md5("admin123".encode()).hexdigest()
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
                   ("admin", admin_pass, "admin"))
    conn.commit()
    conn.close()


@app.route("/")
def index():
    return """
    <h1>인증 취약점 실습</h1>
    <h2>회원가입</h2>
    <form action="/register" method="POST">
        <input name="username" placeholder="Username"><br><br>
        <input name="password" type="password" placeholder="Password"><br><br>
        <button type="submit">Register</button>
    </form>
    <h2>로그인</h2>
    <form action="/login" method="POST">
        <input name="username" placeholder="Username"><br><br>
        <input name="password" type="password" placeholder="Password"><br><br>
        <button type="submit">Login</button>
    </form>
    <hr>
    <h3>취약점</h3>
    <ul>
        <li>MD5 해시 사용 (레인보우 테이블 공격 가능)</li>
        <li>Salt 없음</li>
        <li>JWT 알고리즘 "none" 허용</li>
        <li>하드코딩된 시크릿 키</li>
    </ul>
    """


@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    # 취약점: MD5 해시, salt 없음
    password_hash = hashlib.md5(password.encode()).hexdigest()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                       (username, password_hash))
        conn.commit()
        return jsonify({"status": "success", "message": "User registered"})
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "Username already exists"})
    finally:
        conn.close()


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    password_hash = hashlib.md5(password.encode()).hexdigest()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users WHERE username = ? AND password = ?",
                   (username, password_hash))
    user = cursor.fetchone()
    conn.close()

    if user:
        # 취약점: algorithms 배열에 "none" 포함 가능성
        token = jwt.encode({
            "user_id": user[0],
            "username": user[1],
            "role": user[2],
            "exp": datetime.utcnow() + timedelta(hours=24)
        }, JWT_SECRET, algorithm="HS256")

        return jsonify({
            "status": "success",
            "token": token,
            "message": f"Welcome {user[1]}"
        })
    else:
        return jsonify({"status": "error", "message": "Invalid credentials"})


@app.route("/admin", methods=["GET"])
def admin():
    """취약점: JWT 알고리즘 검증 없음"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")

    try:
        # 취약점: algorithms 미지정 - "none" 알고리즘 허용 가능
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256", "none"])

        if payload.get("role") == "admin":
            return jsonify({"status": "success", "message": "Welcome to admin panel"})
        else:
            return jsonify({"status": "error", "message": "Admin access required"})
    except jwt.ExpiredSignatureError:
        return jsonify({"status": "error", "message": "Token expired"})
    except jwt.InvalidTokenError as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
