"""
암호화 취약점 실습 - 취약한 코드
"""
from flask import Flask, request, jsonify
from Crypto.Cipher import DES, AES
from Crypto.Util.Padding import pad, unpad
import base64
import hashlib

app = Flask(__name__)

# 취약점: 하드코딩된 암호화 키
HARDCODED_KEY = b"secret12"  # DES 키 (8바이트)
WEAK_IV = b"12345678"  # 고정된 IV


@app.route("/")
def index():
    return """
    <h1>암호화 취약점 실습</h1>
    <h2>데이터 암호화</h2>
    <form action="/encrypt" method="POST">
        <input name="data" placeholder="Data to encrypt" size="40"><br><br>
        <button type="submit">Encrypt</button>
    </form>
    <h2>데이터 복호화</h2>
    <form action="/decrypt" method="POST">
        <input name="encrypted" placeholder="Encrypted data (base64)" size="40"><br><br>
        <button type="submit">Decrypt</button>
    </form>
    <hr>
    <h3>취약점</h3>
    <ul>
        <li>DES 사용 (deprecated, 56-bit key)</li>
        <li>ECB 모드 (패턴 노출)</li>
        <li>하드코딩된 키</li>
        <li>고정된 IV</li>
    </ul>
    """


@app.route("/encrypt", methods=["POST"])
def encrypt():
    """취약점: DES + ECB 모드"""
    data = request.form.get("data", "")

    try:
        # 취약점: DES (deprecated) + ECB 모드 (패턴 노출)
        cipher = DES.new(HARDCODED_KEY, DES.MODE_ECB)
        padded_data = pad(data.encode(), DES.block_size)
        encrypted = cipher.encrypt(padded_data)
        encoded = base64.urlsafe_b64encode(encrypted).decode()

        return jsonify({
            "status": "success",
            "encrypted": encoded,
            "warning": "DES + ECB 모드 사용 (취약)"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/decrypt", methods=["POST"])
def decrypt():
    encrypted = request.form.get("encrypted", "")

    try:
        cipher = DES.new(HARDCODED_KEY, DES.MODE_ECB)
        decoded = base64.urlsafe_b64decode(encrypted)
        decrypted = unpad(cipher.decrypt(decoded), DES.block_size)

        return jsonify({
            "status": "success",
            "decrypted": decrypted.decode()
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/hash", methods=["POST"])
def hash_data():
    """취약점: MD5 해시"""
    data = request.form.get("data", "")

    # 취약점: MD5 (collision 취약)
    md5_hash = hashlib.md5(data.encode()).hexdigest()
    # 취약점: SHA1 (deprecated)
    sha1_hash = hashlib.sha1(data.encode()).hexdigest()

    return jsonify({
        "md5": md5_hash,
        "sha1": sha1_hash,
        "warning": "MD5/SHA1은 암호학적으로 안전하지 않음"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
