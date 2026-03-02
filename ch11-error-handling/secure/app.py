"""
안전한 에러 처리 및 로깅 실습
- 일반적인 에러 메시지만 사용자에게 표시
- 민감 정보 마스킹
- 구조화된 보안 로깅
"""
from flask import Flask, request, jsonify
import sqlite3
import logging
import uuid
import re
from functools import wraps

app = Flask(__name__)
app.json.ensure_ascii = False

# 보안: 구조화된 로깅 설정
class SensitiveDataFilter(logging.Filter):
    """민감 정보를 마스킹하는 로그 필터"""

    PATTERNS = [
        (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD_MASKED]'),
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_MASKED]'),
        (r'password["\']?\s*[:=]\s*["\']?[^"\'}\s]+', 'password=[MASKED]'),
    ]

    def filter(self, record):
        msg = record.getMessage()
        for pattern, replacement in self.PATTERNS:
            msg = re.sub(pattern, replacement, msg, flags=re.IGNORECASE)
        record.msg = msg
        record.args = ()
        return True


# 프로덕션용 로깅 설정
logger = logging.getLogger('secure_app')
logger.setLevel(logging.INFO)

handler = logging.FileHandler('secure_app.log')
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - [%(request_id)s] - %(message)s'
))
handler.addFilter(SensitiveDataFilter())
logger.addHandler(handler)


class RequestContextFilter(logging.Filter):
    """요청 컨텍스트를 로그에 추가"""
    def filter(self, record):
        record.request_id = getattr(request, 'request_id', 'N/A')
        return True


logger.addFilter(RequestContextFilter())


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
            password_hash TEXT,
            email TEXT,
            credit_card_last4 TEXT
        )
    ''')
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, email, credit_card_last4) VALUES (?, ?, ?, ?)",
            ("admin", "hashed_password_here", "admin@example.com", "1111")
        )
        conn.commit()
    except:
        pass
    conn.close()


def handle_errors(f):
    """에러 처리 데코레이터"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Validation error: {type(e).__name__}")
            return jsonify({"error": "Invalid input provided"}), 400
        except Exception as e:
            # 내부 로그에만 상세 정보 기록
            error_id = str(uuid.uuid4())[:8]
            logger.error(f"Error ID {error_id}: {type(e).__name__}: {str(e)}")

            # 사용자에게는 일반적인 메시지만 표시
            return jsonify({
                "error": "An unexpected error occurred",
                "error_id": error_id,
                "message": "Please contact support with this error ID"
            }), 500
    return wrapper


@app.before_request
def before_request():
    """요청마다 고유 ID 할당"""
    request.request_id = str(uuid.uuid4())[:8]


@app.route("/")
def index():
    return """
    <h1>안전한 에러 처리 실습</h1>
    <h3>적용된 보안 조치</h3>
    <ul>
        <li>일반적인 에러 메시지 사용</li>
        <li>에러 ID로 추적 가능</li>
        <li>민감 정보 마스킹 로깅</li>
        <li>디버그 모드 비활성화</li>
    </ul>
    <h3>테스트</h3>
    <ul>
        <li><a href="/user?id=1">/user?id=1</a> - 정상 조회</li>
        <li><a href="/user?id=abc">/user?id=abc</a> - 타입 에러</li>
        <li><a href="/user?id=999">/user?id=999</a> - 없는 사용자</li>
        <li><a href="/login">/login</a> - 로그인 테스트</li>
    </ul>
    """


@app.route("/user")
@handle_errors
def get_user():
    user_id = request.args.get("id")

    # 보안: 입력값 검증
    if not user_id or not user_id.isdigit():
        raise ValueError("Invalid user ID format")

    user_id = int(user_id)

    # 보안: 민감하지 않은 정보만 로깅
    logger.info(f"User lookup for ID: {user_id}")

    conn = get_db()
    cursor = conn.execute(
        "SELECT id, username FROM users WHERE id = ?",
        (user_id,)
    )
    user = cursor.fetchone()
    conn.close()

    if not user:
        # 보안: 일반적인 에러 메시지
        return jsonify({"error": "Resource not found"}), 404

    # 보안: 필요한 정보만 반환
    return jsonify({
        "id": user["id"],
        "username": user["username"]
    })


@app.route("/login", methods=["GET", "POST"])
@handle_errors
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

    # 보안: 비밀번호는 로깅하지 않음
    logger.info(f"Login attempt for user: {username}")

    conn = get_db()
    # 실제로는 password_hash와 비교해야 함
    cursor = conn.execute(
        "SELECT id, username FROM users WHERE username = ?",
        (username,)
    )
    user = cursor.fetchone()
    conn.close()

    # 보안: 동일한 에러 메시지 사용 (사용자 열거 방지)
    if not user:
        logger.info(f"Failed login attempt")
        return jsonify({"error": "Invalid credentials"}), 401

    # 실제로는 비밀번호 해시 검증 필요
    logger.info(f"Successful login for user ID: {user['id']}")
    return jsonify({
        "message": "Login successful",
        "user_id": user["id"]
    })


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    error_id = str(uuid.uuid4())[:8]
    logger.error(f"Unhandled error {error_id}: {str(e)}")
    return jsonify({
        "error": "Internal server error",
        "error_id": error_id
    }), 500


if __name__ == "__main__":
    init_db()
    # 보안: 프로덕션에서는 디버그 모드 비활성화
    app.run(host="0.0.0.0", port=5000, debug=False)
