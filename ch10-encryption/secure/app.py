"""
안전한 암호화 실습 - AES-GCM + 안전한 키 관리
"""
from flask import Flask, request, jsonify
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import base64
import hashlib

app = Flask(__name__)


def get_encryption_key() -> bytes:
    """환경 변수에서 키 로드 또는 생성"""
    key_hex = os.environ.get("ENCRYPTION_KEY")
    if key_hex:
        return bytes.fromhex(key_hex)
    # 개발용 임시 키 (프로덕션에서는 사용 금지)
    return os.urandom(32)


def derive_key(password: str, salt: bytes) -> bytes:
    """비밀번호에서 키 유도 (PBKDF2)"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600000,  # OWASP 권장
    )
    return kdf.derive(password.encode())


MASTER_KEY = get_encryption_key()


@app.route("/")
def index():
    return """
    <h1>안전한 암호화 실습</h1>
    <h2>AES-GCM 암호화</h2>
    <form action="/encrypt" method="POST">
        <input name="data" placeholder="Data to encrypt" size="40"><br><br>
        <button type="submit">Encrypt</button>
    </form>
    <h2>복호화</h2>
    <form action="/decrypt" method="POST">
        <input name="encrypted" placeholder="Encrypted data (base64)" size="60"><br><br>
        <button type="submit">Decrypt</button>
    </form>
    <hr>
    <h3>적용된 보안 조치</h3>
    <ul>
        <li>AES-256-GCM (인증된 암호화)</li>
        <li>랜덤 Nonce (매번 새로 생성)</li>
        <li>환경 변수에서 키 로드</li>
        <li>SHA-256/SHA-3 해시</li>
    </ul>
    """


@app.route("/encrypt", methods=["POST"])
def encrypt():
    """안전한 암호화: AES-256-GCM"""
    data = request.form.get("data", "")

    try:
        # 매번 새로운 nonce 생성 (12바이트)
        nonce = os.urandom(12)
        aesgcm = AESGCM(MASTER_KEY)

        # GCM 모드: 암호화 + 무결성 검증
        ciphertext = aesgcm.encrypt(nonce, data.encode(), None)

        # nonce + ciphertext를 함께 저장 (URL-safe base64로 인코딩)
        result = nonce + ciphertext
        encoded = base64.urlsafe_b64encode(result).decode()

        return jsonify({
            "status": "success",
            "encrypted": encoded,
            "note": "Nonce가 암호문에 포함됨"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": "Encryption failed"})


@app.route("/decrypt", methods=["POST"])
def decrypt():
    encrypted = request.form.get("encrypted", "")

    try:
        decoded = base64.urlsafe_b64decode(encrypted)

        # nonce 분리 (처음 12바이트)
        nonce = decoded[:12]
        ciphertext = decoded[12:]

        aesgcm = AESGCM(MASTER_KEY)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        return jsonify({
            "status": "success",
            "decrypted": plaintext.decode()
        })
    except Exception as e:
        # 암호화 오류 상세 정보 숨김
        return jsonify({"status": "error", "message": "Decryption failed"})


@app.route("/hash", methods=["POST"])
def hash_data():
    """안전한 해시: SHA-256, SHA-3"""
    data = request.form.get("data", "")

    sha256_hash = hashlib.sha256(data.encode()).hexdigest()
    sha3_hash = hashlib.sha3_256(data.encode()).hexdigest()

    return jsonify({
        "sha256": sha256_hash,
        "sha3_256": sha3_hash
    })


@app.route("/derive_key", methods=["POST"])
def derive_key_endpoint():
    """비밀번호 기반 키 유도 (PBKDF2)"""
    password = request.form.get("password", "")

    # 랜덤 salt 생성
    salt = os.urandom(16)

    # 키 유도
    derived_key = derive_key(password, salt)

    return jsonify({
        "salt": base64.b64encode(salt).decode(),
        "derived_key": base64.b64encode(derived_key).decode(),
        "iterations": 600000
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
