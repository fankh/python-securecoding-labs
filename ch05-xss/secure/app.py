"""
XSS 방어 실습 - 안전한 코드
Jinja2 자동 이스케이프 + CSP 헤더
"""
from flask import Flask, request, render_template_string, make_response
from markupsafe import escape
import sqlite3
import bleach

app = Flask(__name__)
app.json.ensure_ascii = False
DB_PATH = "guestbook_secure.db"

# 허용된 HTML 태그 (Bleach)
ALLOWED_TAGS = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
ALLOWED_ATTRS = {}


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


# 안전한 템플릿: Jinja2 자동 이스케이프 (기본값)
TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>방명록 (안전)</title></head>
<body>
    <h1>방명록 (XSS 방어)</h1>
    <form action="/post" method="POST">
        <input name="name" placeholder="이름" maxlength="50"><br><br>
        <textarea name="message" placeholder="메시지" maxlength="500"></textarea><br><br>
        <button type="submit">작성</button>
    </form>
    <hr>
    <h2>메시지 목록</h2>
    {% for msg in messages %}
    <div style="border:1px solid #ccc; padding:10px; margin:10px 0;">
        <strong>{{ msg[1] }}</strong>  <!-- 자동 이스케이프 -->
        <p>{{ msg[2] }}</p>  <!-- 자동 이스케이프 -->
        <small>{{ msg[3] }}</small>
    </div>
    {% endfor %}
    <hr>
    <h3>검색</h3>
    <form action="/search" method="GET">
        <input name="q" placeholder="검색어"><button type="submit">검색</button>
    </form>
    {% if search_query %}
    <p>검색어: {{ search_query }}</p>  <!-- 자동 이스케이프 -->
    {% endif %}
    <hr>
    <h3>적용된 보안 조치</h3>
    <ul>
        <li>Jinja2 자동 이스케이프</li>
        <li>Content-Security-Policy 헤더</li>
        <li>입력 길이 제한</li>
        <li>Bleach로 HTML 정화</li>
    </ul>
</body>
</html>
"""


@app.after_request
def add_security_headers(response):
    """보안 헤더 추가"""
    # CSP: 인라인 스크립트 차단
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response


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
    name = request.form.get("name", "Anonymous")[:50]  # 길이 제한
    message = request.form.get("message", "")[:500]

    # Bleach로 위험한 HTML 제거
    clean_name = bleach.clean(name, tags=[], strip=True)
    clean_message = bleach.clean(message, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (name, message) VALUES (?, ?)",
                   (clean_name, clean_message))
    conn.commit()
    conn.close()

    # 안전한 리다이렉트
    return '<meta http-equiv="refresh" content="0;url=/">'


@app.route("/search")
def search():
    query = request.args.get("q", "")[:100]  # 길이 제한

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages WHERE message LIKE ?", (f"%{query}%",))
    messages = cursor.fetchall()
    conn.close()

    return render_template_string(TEMPLATE, messages=messages, search_query=query)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
