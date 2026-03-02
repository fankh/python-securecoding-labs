"""
안전한 인증 실습 - bcrypt, Argon2, 안전한 JWT
"""
from flask import Flask, request, jsonify
import bcrypt
import jwt
import sqlite3
import os
import re
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.json.ensure_ascii = False
DB_PATH = "auth_secure.db"

# 환경 변수에서 시크릿 로드
JWT_SECRET = os.environ.get("JWT_SECRET", os.urandom(32).hex())
JWT_ALGORITHM = "HS256"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            role TEXT DEFAULT 'user',
            failed_attempts INTEGER DEFAULT 0,
            locked_until TIMESTAMP
        )
    """)
    # bcrypt로 비밀번호 해시
    admin_hash = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
    cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                   ("admin", admin_hash, "admin"))
    conn.commit()
    conn.close()


def validate_password(password: str) -> tuple[bool, str]:
    """비밀번호 정책 검증"""
    if len(password) < 8:
        return False, "비밀번호는 8자 이상이어야 합니다"
    if not re.search(r"[A-Z]", password):
        return False, "대문자를 포함해야 합니다"
    if not re.search(r"[a-z]", password):
        return False, "소문자를 포함해야 합니다"
    if not re.search(r"\d", password):
        return False, "숫자를 포함해야 합니다"
    if not re.search(r"[!@#$%^&*]", password):
        return False, "특수문자(!@#$%^&*)를 포함해야 합니다"
    return True, ""


def check_account_lock(cursor, username: str) -> tuple[bool, str]:
    """계정 잠금 확인"""
    cursor.execute("SELECT failed_attempts, locked_until FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    if result:
        failed_attempts, locked_until = result
        if locked_until:
            lock_time = datetime.fromisoformat(locked_until)
            if datetime.utcnow() < lock_time:
                return True, f"계정이 잠겼습니다. {lock_time}까지 대기하세요"
    return False, ""


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"status": "error", "message": "Token required"}), 401

        try:
            # 안전: 알고리즘을 명시적으로 지정
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            request.user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({"status": "error", "message": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"status": "error", "message": "Invalid token"}), 401

        return f(*args, **kwargs)
    return decorated


@app.route("/")
def index():
    return """
    <h1>안전한 인증 실습</h1>
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
    <h3>적용된 보안 조치</h3>
    <ul>
        <li>bcrypt로 비밀번호 해시 (자동 salt 포함)</li>
        <li>비밀번호 복잡도 정책</li>
        <li>JWT 알고리즘 명시적 지정</li>
        <li>환경 변수에서 시크릿 로드</li>
        <li>브루트포스 방지 (계정 잠금)</li>
    </ul>
    """


@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    # 사용자명 검증
    if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
        return jsonify({"status": "error", "message": "사용자명은 3-20자 영문/숫자/_만 가능합니다"})

    # 비밀번호 정책 검증
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        return jsonify({"status": "error", "message": error_msg})

    # bcrypt로 해시 (자동으로 salt 생성)
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                       (username, password_hash))
        conn.commit()
        return jsonify({"status": "success", "message": "User registered successfully"})
    except sqlite3.IntegrityError:
        return jsonify({"status": "error", "message": "Username already exists"})
    finally:
        conn.close()


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 계정 잠금 확인
    is_locked, lock_msg = check_account_lock(cursor, username)
    if is_locked:
        conn.close()
        return jsonify({"status": "error", "message": lock_msg})

    cursor.execute("SELECT id, username, password_hash, role, failed_attempts FROM users WHERE username = ?",
                   (username,))
    user = cursor.fetchone()

    if user and bcrypt.checkpw(password.encode(), user[2].encode()):
        # 로그인 성공: 실패 횟수 초기화
        cursor.execute("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE username = ?",
                       (username,))
        conn.commit()

        token = jwt.encode({
            "user_id": user[0],
            "username": user[1],
            "role": user[3],
            "exp": datetime.utcnow() + timedelta(hours=1)  # 짧은 만료 시간
        }, JWT_SECRET, algorithm=JWT_ALGORITHM)

        conn.close()
        return jsonify({
            "status": "success",
            "token": token,
            "message": f"Welcome {user[1]}"
        })
    else:
        # 로그인 실패: 실패 횟수 증가
        if user:
            failed = user[4] + 1
            locked_until = None
            if failed >= 5:
                locked_until = (datetime.utcnow() + timedelta(minutes=15)).isoformat()
            cursor.execute("UPDATE users SET failed_attempts = ?, locked_until = ? WHERE username = ?",
                           (failed, locked_until, username))
            conn.commit()

        conn.close()
        # 타이밍 공격 방지: 동일한 메시지
        return jsonify({"status": "error", "message": "Invalid username or password"})


@app.route("/admin", methods=["GET"])
@token_required
def admin():
    if request.user.get("role") == "admin":
        return jsonify({"status": "success", "message": "Welcome to admin panel"})
    return jsonify({"status": "error", "message": "Admin access required"}), 403


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
