"""
SQL Injection 취약점 실습 - 취약한 코드
"""
from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
app.json.ensure_ascii = False
DB_PATH = "users.db"


def init_db():
    """데이터베이스 초기화"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT,
            role TEXT DEFAULT 'user'
        )
    """)
    # 테스트 데이터 삽입
    cursor.execute("INSERT OR IGNORE INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
                   ("admin", "admin123", "admin@example.com", "admin"))
    cursor.execute("INSERT OR IGNORE INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
                   ("user1", "password1", "user1@example.com", "user"))
    cursor.execute("INSERT OR IGNORE INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
                   ("user2", "password2", "user2@example.com", "user"))
    cursor.execute("INSERT OR IGNORE INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
                   ("alice", "password", "alice@example.com", "user"))
    conn.commit()
    conn.close()


@app.route("/")
def index():
    return """
    <h1>SQL Injection 취약점 실습</h1>
    <h2>취약한 로그인</h2>
    <form action="/login" method="POST">
        <input name="username" placeholder="Username"><br><br>
        <input name="password" type="password" placeholder="Password"><br><br>
        <button type="submit">Login</button>
    </form>
    <h2>취약한 사용자 검색</h2>
    <form action="/search" method="GET">
        <input name="q" placeholder="Search username"><br><br>
        <button type="submit">Search</button>
    </form>
    <hr>
    <h3>공격 예시</h3>
    <ul>
        <li>로그인: username에 <code>' OR '1'='1' --</code> 입력</li>
        <li>검색: <code>' UNION SELECT id, username, password FROM users--</code></li>
    </ul>
    """


@app.route("/login", methods=["POST"])
def login():
    """취약점: 사용자 입력을 직접 쿼리에 삽입"""
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    # 취약한 코드 - 문자열 포맷팅으로 쿼리 생성
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(query)
        user = cursor.fetchone()
        conn.close()

        if user:
            return jsonify({
                "status": "success",
                "message": f"로그인 성공! 환영합니다, {user[1]}님",
                "user": {"id": user[0], "username": user[1], "role": user[4]},
                "executed_query": query  # 디버그용 - 실제 환경에서는 절대 노출 금지
            })
        else:
            return jsonify({"status": "error", "message": "로그인 실패"})
    except Exception as e:
        conn.close()
        return jsonify({"status": "error", "message": str(e), "query": query})


@app.route("/search")
def search():
    """취약점: UNION 기반 SQL Injection"""
    query_param = request.args.get("q", "")

    # 취약한 코드
    query = f"SELECT id, username, email FROM users WHERE username LIKE '%{query_param}%'"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()

        return jsonify({
            "status": "success",
            "results": [{"id": r[0], "username": r[1], "email": r[2]} for r in results],
            "executed_query": query
        })
    except Exception as e:
        conn.close()
        return jsonify({"status": "error", "message": str(e), "query": query})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
