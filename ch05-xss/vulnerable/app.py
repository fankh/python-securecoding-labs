"""
XSS 취약점 실습 - 취약한 코드
"""
from flask import Flask, request, render_template_string
import sqlite3

app = Flask(__name__)
app.json.ensure_ascii = False
DB_PATH = "guestbook.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            name TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


# 취약점: 사용자 입력을 이스케이프 없이 HTML에 삽입
TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>방명록 (XSS 취약)</title></head>
<body>
    <h1>방명록</h1>
    <form action="/post" method="POST">
        <input name="name" placeholder="이름"><br><br>
        <textarea name="message" placeholder="메시지"></textarea><br><br>
        <button type="submit">작성</button>
    </form>
    <hr>
    <h2>메시지 목록</h2>
    {% for msg in messages %}
    <div style="border:1px solid #ccc; padding:10px; margin:10px 0;">
        <strong>{{ msg[1] | safe }}</strong>  <!-- 취약점: safe 필터 -->
        <p>{{ msg[2] | safe }}</p>  <!-- 취약점: safe 필터 -->
        <small>{{ msg[3] }}</small>
    </div>
    {% endfor %}
    <hr>
    <h3>검색 (Reflected XSS)</h3>
    <form action="/search" method="GET">
        <input name="q" placeholder="검색어"><button type="submit">검색</button>
    </form>
    {% if search_query %}
    <p>검색어: {{ search_query | safe }}</p>  <!-- 취약점: Reflected XSS -->
    {% endif %}
    <hr>
    <h3>공격 예시</h3>
    <ul>
        <li><code>&lt;script&gt;alert('XSS')&lt;/script&gt;</code></li>
        <li><code>&lt;img src=x onerror="alert('XSS')"&gt;</code></li>
        <li><code>&lt;a href="javascript:alert('XSS')"&gt;Click&lt;/a&gt;</code></li>
    </ul>
</body>
</html>
"""


@app.route("/")
def index():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages ORDER BY created_at DESC LIMIT 20")
    messages = cursor.fetchall()
    conn.close()
    return render_template_string(TEMPLATE, messages=messages, search_query=None)


@app.route("/post", methods=["POST"])
def post():
    name = request.form.get("name", "Anonymous")
    message = request.form.get("message", "")

    # 취약점: 입력값 검증 없이 저장 (Stored XSS)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (name, message) VALUES (?, ?)", (name, message))
    conn.commit()
    conn.close()

    return '<script>alert("작성 완료!");location.href="/";</script>'


@app.route("/search")
def search():
    query = request.args.get("q", "")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE message LIKE ?", (f"%{query}%",))
    messages = cursor.fetchall()
    conn.close()

    # 취약점: 검색어를 이스케이프 없이 표시 (Reflected XSS)
    return render_template_string(TEMPLATE, messages=messages, search_query=query)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
