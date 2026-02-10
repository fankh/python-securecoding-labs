"""
Command Injection 취약점 실습 - 취약한 코드
경고: 이 코드는 교육 목적으로만 사용하세요!
"""
from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)


@app.route("/")
def index():
    return """
    <h1>Command Injection 취약점 실습</h1>
    <h2>네트워크 진단 도구</h2>
    <form action="/ping" method="POST">
        <input name="host" placeholder="Enter hostname or IP" size="40"><br><br>
        <button type="submit">Ping</button>
    </form>
    <form action="/dns" method="POST">
        <input name="domain" placeholder="Enter domain" size="40"><br><br>
        <button type="submit">DNS Lookup</button>
    </form>
    <hr>
    <h3>공격 예시</h3>
    <ul>
        <li><code>127.0.0.1; cat /etc/passwd</code></li>
        <li><code>127.0.0.1 | whoami</code></li>
        <li><code>127.0.0.1 && id</code></li>
        <li><code>$(whoami)</code></li>
    </ul>
    """


@app.route("/ping", methods=["POST"])
def ping():
    """취약점: shell=True로 사용자 입력 실행"""
    host = request.form.get("host", "")

    # 취약한 코드 - 사용자 입력을 쉘 명령어에 직접 삽입
    command = f"ping -c 3 {host}"

    try:
        # shell=True는 명령어 인젝션에 취약
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        return jsonify({
            "status": "success",
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr
        })
    except subprocess.TimeoutExpired:
        return jsonify({"status": "error", "message": "Command timed out"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/dns", methods=["POST"])
def dns_lookup():
    """취약점: os.system() 사용"""
    domain = request.form.get("domain", "")

    # 취약한 코드 - os.system() 사용
    command = f"nslookup {domain}"

    try:
        # os.popen()도 동일하게 취약
        result = os.popen(command).read()
        return jsonify({
            "status": "success",
            "command": command,
            "output": result
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
