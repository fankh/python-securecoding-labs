"""
SQL Injection 방어 실습 - 안전한 코드
Parameterized Query와 ORM을 사용한 안전한 구현
"""
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
app.json.ensure_ascii = False
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users_secure.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class User(db.Model):
    """SQLAlchemy ORM 모델"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


def init_db():
    """데이터베이스 초기화"""
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", email="admin@example.com", role="admin")
            admin.set_password("admin123")
            db.session.add(admin)

            user1 = User(username="user1", email="user1@example.com", role="user")
            user1.set_password("password1")
            db.session.add(user1)

            alice = User(username="alice", email="alice@example.com", role="user")
            alice.set_password("password")
            db.session.add(alice)

            db.session.commit()


def validate_username(username: str) -> bool:
    """사용자명 유효성 검사 (화이트리스트)"""
    if not username or len(username) > 50:
        return False
    # 영문, 숫자, 언더스코어만 허용
    return bool(re.match(r"^[a-zA-Z0-9_]+$", username))


@app.route("/")
def index():
    return """
    <h1>SQL Injection 방어 실습</h1>
    <h2>안전한 로그인 (Parameterized Query + ORM)</h2>
    <form action="/login" method="POST">
        <input name="username" placeholder="Username"><br><br>
        <input name="password" type="password" placeholder="Password"><br><br>
        <button type="submit">Login</button>
    </form>
    <h2>안전한 사용자 검색</h2>
    <form action="/search" method="GET">
        <input name="q" placeholder="Search username"><br><br>
        <button type="submit">Search</button>
    </form>
    <hr>
    <h3>적용된 보안 조치</h3>
    <ul>
        <li>SQLAlchemy ORM 사용 (Parameterized Query 자동 적용)</li>
        <li>입력값 화이트리스트 검증</li>
        <li>비밀번호 해시 저장 (werkzeug)</li>
        <li>에러 메시지에서 쿼리 정보 제거</li>
    </ul>
    """


@app.route("/login", methods=["POST"])
def login():
    """안전한 로그인: ORM + 비밀번호 해시 검증"""
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    # 1. 입력값 검증
    if not validate_username(username):
        return jsonify({"status": "error", "message": "잘못된 사용자명 형식입니다"})

    if not password or len(password) > 128:
        return jsonify({"status": "error", "message": "잘못된 비밀번호 형식입니다"})

    # 2. ORM을 사용한 안전한 쿼리 (Parameterized Query 자동 적용)
    user = User.query.filter_by(username=username).first()

    # 3. 비밀번호 해시 검증
    if user and user.check_password(password):
        return jsonify({
            "status": "success",
            "message": f"로그인 성공! 환영합니다, {user.username}님",
            "user": {"id": user.id, "username": user.username, "role": user.role}
        })
    else:
        # 타이밍 공격 방지를 위해 동일한 메시지 반환
        return jsonify({"status": "error", "message": "사용자명 또는 비밀번호가 올바르지 않습니다"})


@app.route("/search")
def search():
    """안전한 검색: ORM + 입력값 검증"""
    query_param = request.args.get("q", "")

    # 1. 입력값 검증 (길이 제한)
    if len(query_param) > 50:
        return jsonify({"status": "error", "message": "검색어가 너무 깁니다"})

    # 2. 특수문자 제거 (또는 이스케이프)
    # ORM이 자동으로 이스케이프하지만, 추가 검증
    safe_query = re.sub(r"[^\w\s]", "", query_param)

    # 3. ORM을 사용한 안전한 LIKE 쿼리
    users = User.query.filter(User.username.ilike(f"%{safe_query}%")).all()

    return jsonify({
        "status": "success",
        "results": [{"id": u.id, "username": u.username, "email": u.email} for u in users]
    })


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
