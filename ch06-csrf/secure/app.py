"""
CSRF 방어 실습 - Flask-WTF 사용
"""
from flask import Flask, request, render_template_string, session, redirect
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Email
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(32)
csrf = CSRFProtect(app)
DB_PATH = "users_secure.db"


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


class TransferForm(FlaskForm):
    to = StringField('받는 사람', validators=[DataRequired()])
    amount = IntegerField('금액', validators=[DataRequired()])
    submit = SubmitField('송금')


class EmailForm(FlaskForm):
    email = StringField('이메일', validators=[DataRequired(), Email()])
    submit = SubmitField('변경')


TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>CSRF 방어 실습</title></head>
<body>
    <h1>은행 서비스 (CSRF 방어)</h1>
    {% if user %}
    <p>로그인: {{ user }} | 잔액: {{ balance }}원</p>
    <h2>송금</h2>
    <form action="/transfer" method="POST">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <input name="to" placeholder="받는 사람"><br><br>
        <input name="amount" type="number" placeholder="금액"><br><br>
        <button type="submit">송금</button>
    </form>
    <h2>이메일 변경</h2>
    <form action="/change_email" method="POST">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <input name="email" placeholder="새 이메일"><br><br>
        <button type="submit">변경</button>
    </form>
    <a href="/logout">로그아웃</a>
    {% else %}
    <h2>로그인</h2>
    <form action="/login" method="POST">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <input name="username" placeholder="Username"><br><br>
        <button type="submit">Login</button>
    </form>
    {% endif %}
    <hr>
    <h3>적용된 보안 조치</h3>
    <ul>
        <li>CSRF 토큰 검증</li>
        <li>POST 요청만 허용</li>
        <li>SameSite 쿠키</li>
        <li>Referer 검증 (선택)</li>
    </ul>
</body>
</html>
"""


@app.after_request
def set_cookie_options(response):
    """SameSite 쿠키 설정"""
    response.headers['Set-Cookie'] = response.headers.get('Set-Cookie', '') + '; SameSite=Strict'
    return response


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


@app.route("/transfer", methods=["POST"])  # POST만 허용
def transfer():
    """안전: CSRF 토큰 자동 검증"""
    user = session.get("user")
    if not user:
        return "Not logged in", 401

    to = request.form.get("to", "")
    amount = int(request.form.get("amount", 0))

    if amount <= 0:
        return "Invalid amount", 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance - ? WHERE username = ?", (amount, user))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amount, to))
    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/change_email", methods=["POST"])
def change_email():
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
