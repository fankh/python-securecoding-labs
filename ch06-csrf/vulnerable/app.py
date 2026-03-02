"""
CSRF 취약점 실습 - 취약한 코드
"""
from flask import Flask, request, render_template_string, session, redirect
import sqlite3

app = Flask(__name__)
app.secret_key = "secret"
# 취약점: SameSite=None → 다른 사이트에서 쿠키 전송 가능 (CSRF 허용)
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = False
DB_PATH = "users.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            email TEXT,
            balance INTEGER DEFAULT 1000
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO users (username, email, balance) VALUES (?, ?, ?)",
                   ("alice", "alice@example.com", 1000))
    cursor.execute("INSERT OR IGNORE INTO users (username, email, balance) VALUES (?, ?, ?)",
                   ("bob", "bob@example.com", 1000))
    conn.commit()
    conn.close()


TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>CSRF 취약점 실습</title></head>
<body>
    <h1>은행 서비스 (CSRF 취약)</h1>
    {% if user %}
    <p>로그인: {{ user }} | 잔액: {{ balance }}원</p>
    <h2>송금</h2>
    <form action="/transfer" method="POST">
        <input name="to" placeholder="받는 사람"><br><br>
        <input name="amount" type="number" placeholder="금액"><br><br>
        <button type="submit">송금</button>
    </form>
    <h2>이메일 변경</h2>
    <form action="/change_email" method="POST">
        <input name="email" placeholder="새 이메일"><br><br>
        <button type="submit">변경</button>
    </form>
    <a href="/logout">로그아웃</a>
    {% else %}
    <h2>로그인</h2>
    <form action="/login" method="POST">
        <input name="username" placeholder="Username"><br><br>
        <button type="submit">Login</button>
    </form>
    {% endif %}
    <hr>
    <h3>CSRF 공격 예시</h3>
    <p>공격자가 아래 HTML을 피해자가 방문하도록 유도:</p>
    <pre>&lt;img src="http://localhost:5000/transfer?to=attacker&amount=500"&gt;</pre>
    <pre>&lt;form action="http://localhost:5000/transfer" method="POST"&gt;
  &lt;input type="hidden" name="to" value="attacker"&gt;
  &lt;input type="hidden" name="amount" value="500"&gt;
&lt;/form&gt;
&lt;script&gt;document.forms[0].submit();&lt;/script&gt;</pre>
</body>
</html>
"""


@app.route("/")
def index():
    user = session.get("user")
    balance = 0
    if user:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE username = ?", (user,))
        result = cursor.fetchone()
        balance = result[0] if result else 0
        conn.close()
    return render_template_string(TEMPLATE, user=user, balance=balance)


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "")
    session["user"] = username
    return redirect("/")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    """취약점: CSRF 토큰 없음, GET 요청 허용"""
    user = session.get("user")
    if not user:
        return "Not logged in", 401

    # GET/POST 모두 허용 (취약)
    to = request.values.get("to", "")
    amount = int(request.values.get("amount", 0))

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance - ? WHERE username = ?", (amount, user))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amount, to))
    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/change_email", methods=["POST"])
def change_email():
    """취약점: CSRF 토큰 없음"""
    user = session.get("user")
    if not user:
        return "Not logged in", 401

    email = request.form.get("email", "")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET email = ? WHERE username = ?", (email, user))
    conn.commit()
    conn.close()

    return redirect("/")


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
