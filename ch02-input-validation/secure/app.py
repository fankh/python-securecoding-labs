"""
안전한 입력값 검증 실습
화이트리스트 + Pydantic 사용
"""

import re
from typing import Optional

from flask import Flask, jsonify, request
from pydantic import BaseModel, EmailStr, HttpUrl, ValidationError, field_validator

app = Flask(__name__)
app.json.ensure_ascii = False


class UserRegistration(BaseModel):
    """Pydantic 모델로 입력 검증"""

    username: str
    email: EmailStr
    age: int
    url: Optional[HttpUrl] = None
    gender: str
    phone: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not v or len(v) < 3 or len(v) > 20:
            raise ValueError("Username must be 3-20 characters")
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username can only contain letters, numbers, underscore")
        return v

    @field_validator("age")
    @classmethod
    def validate_age(cls, v):
        if v < 0 or v > 150:
            raise ValueError("Age must be between 0 and 150")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v):
        if not v or len(v) < 3 or len(v) > 10:
            raise ValueError("Gender must be 3-20 characters")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if not re.match(r"^\d{2,3}\-\d{3,4}\-\d{4}$", v):
            raise ValueError("Phone number can only contain numbers")
        return v


# 안전한 정규식 (ReDoS 방지)
SAFE_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


@app.route("/")
def index():
    return """
    <h1>안전한 입력값 검증 실습</h1>
    <h2>사용자 등록</h2>
    <form action="/register" method="POST">
        <input name="username" placeholder="Username (4-20자, 영문/숫자/_)" maxlength="20"><br><br>
        <input name="email" placeholder="Email"><br><br>
        <input name="age" type="number" placeholder="Age" min="0" max="150"><br><br>
        <input name="url" placeholder="Website URL (https://...)"><br><br>
        <input name="gender" placeholder="Gender"><br><br>
        <input name="phone" placeholder="Phone Number"><br><br>
        <button type="submit">Register</button>
    </form>
    <hr>
    <h3>적용된 보안 조치</h3>
    <ul>
        <li>Pydantic으로 스키마 검증</li>
        <li>화이트리스트 기반 검증</li>
        <li>길이 제한</li>
        <li>타입 강제</li>
        <li>ReDoS 안전한 정규식</li>
    </ul>
    """


@app.route("/register", methods=["POST"])
def register():
    try:
        # Pydantic으로 자동 검증
        user = UserRegistration(
            username=request.form.get("username", ""),
            email=request.form.get("email", ""),
            age=int(request.form.get("age", 0)),
            url=request.form.get("url") or None,
            gender=request.form.get("gender", ""),
            phone=request.form.get("phone", ""),
        )
        return jsonify({"status": "success", "data": user.model_dump()})

    except ValidationError as e:
        errors = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
        return jsonify({"errors": errors, "status": "error"})
    except ValueError as e:
        return jsonify({"status": "error", "errors": ["Invalid input format"]})


@app.route("/search", methods=["GET"])
def search():
    """안전한 검색: 사용자 정규식 거부"""
    query = request.args.get("q", "")

    # 정규식 사용 금지, 단순 문자열 검색만 허용
    if len(query) > 100:
        return jsonify({"error": "Query too long"})

    # 특수문자 이스케이프
    safe_query = re.escape(query)

    return jsonify(
        {
            "status": "success",
            "query": safe_query,
            "note": "사용자 입력을 정규식으로 직접 사용하지 않음",
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
