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
app.json.ensure_ascii = False

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
        conn.execute(
            "INSERT INTO users (username, password, email, credit_card) VALUES (?, ?, ?, ?)",
            ("alice", "password", "alice@example.com", "4222-2222-2222-2222")
        )
        conn.commit()
    except:
        pass
    # 잔액 테이블
    conn.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            balance INTEGER DEFAULT 1000
        )
    ''')
    try:
        conn.execute("INSERT INTO accounts (username, balance) VALUES (?, ?)", ("admin", 1000))
        conn.execute("INSERT INTO accounts (username, balance) VALUES (?, ?)", ("alice", 1000))
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


@app.route("/balance")
def get_balance():
    """잔액 조회"""
    conn = get_db()
    rows = conn.execute("SELECT username, balance FROM accounts").fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/transfer", methods=["POST"])
def transfer():
    """취약점: 에러 발생 시 rollback 없음 → 데이터 불일치"""
    sender = request.form.get("from", "")
    receiver = request.form.get("to", "")
    amount = request.form.get("amount", "0")

    conn = get_db()
    try:
        amount = int(amount)

        # 1단계: 보내는 사람 잔액 차감 (이 시점에서 커밋됨)
        conn.execute(
            "UPDATE accounts SET balance = balance - ? WHERE username = ?",
            (amount, sender)
        )
        conn.commit()  # 취약점: 중간에 커밋 → 2단계 실패 시 돈이 사라짐

        # 2단계: 받는 사람 잔액 증가 (여기서 에러 발생 가능)
        if receiver == "error":
            raise Exception("DB connection lost")  # 시뮬레이션: 네트워크 에러

        conn.execute(
            "UPDATE accounts SET balance = balance + ? WHERE username = ?",
            (amount, receiver)
        )
        conn.commit()
        conn.close()

        return jsonify({
            "status": "success",
            "message": f"{sender} → {receiver}: {amount}원 송금 완료"
        })
    except Exception as e:
        # 취약점: rollback 없음 → 1단계만 실행되어 돈이 사라짐
        conn.close()
        logging.error(f"Transfer error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "warning": "송금 중 에러 발생 — rollback 없음으로 데이터 불일치 가능"
        }), 500


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
