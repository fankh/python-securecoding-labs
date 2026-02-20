"""
Command Injection 방어 실습 - 안전한 코드
subprocess를 shell=False로 사용하고 입력값 검증
"""
from flask import Flask, request, jsonify
import subprocess
import re
import shlex

app = Flask(__name__)

# 허용된 호스트 패턴 (화이트리스트)
IP_PATTERN = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
HOSTNAME_PATTERN = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$")


def validate_host(host: str) -> bool:
    """호스트명/IP 유효성 검사"""
    if not host or len(host) > 255:
        return False
    # IP 주소 검증
    if IP_PATTERN.match(host):
        parts = host.split(".")
        return all(0 <= int(p) <= 255 for p in parts)
    # 호스트명 검증
    return bool(HOSTNAME_PATTERN.match(host))


def validate_domain(domain: str) -> bool:
    """도메인 유효성 검사"""
    if not domain or len(domain) > 255:
        return False
    return bool(HOSTNAME_PATTERN.match(domain))


@app.route("/")
def index():
    return """
    <h1>Command Injection 방어 실습</h1>
    <h2>안전한 네트워크 진단 도구</h2>
    <form action="/ping" method="POST">
        <input name="host" placeholder="Enter hostname or IP" size="40"><br><br>
        <button type="submit">Ping</button>
    </form>
    <form action="/dns" method="POST">
        <input name="domain" placeholder="Enter domain" size="40"><br><br>
        <button type="submit">DNS Lookup</button>
    </form>
    <hr>
    <h3>적용된 보안 조치</h3>
    <ul>
        <li>subprocess.run()에 shell=False 사용</li>
        <li>명령어와 인자를 리스트로 분리</li>
        <li>입력값 화이트리스트 검증 (IP, 도메인 형식)</li>
        <li>실행 시간 제한 (timeout)</li>
    </ul>
    """


@app.route("/ping", methods=["POST"])
def ping():
    """안전한 ping: shell=False + 입력 검증"""
    host = request.form.get("host", "").strip()

    # 1. 입력값 검증
    if not validate_host(host):
        return jsonify({
            "status": "error",
            "message": "유효하지 않은 호스트 형식입니다. IP 주소 또는 도메인을 입력하세요."
        })

    try:
        # 2. shell=False + 인자 리스트로 분리 (안전)
        result = subprocess.run(
            ["ping", "-c", "3", host],  # 명령어와 인자를 리스트로 분리
            shell=False,  # 쉘을 거치지 않음
            capture_output=True,
            text=True,
            timeout=10
        )
        return jsonify({
            "status": "success",
            "stdout": result.stdout,
            "stderr": result.stderr
        })
    except subprocess.TimeoutExpired:
        return jsonify({"status": "error", "message": "요청 시간이 초과되었습니다"})
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "ping 명령어를 찾을 수 없습니다"})
    except Exception as e:
        return jsonify({"status": "error", "message": "명령 실행 중 오류가 발생했습니다"})


@app.route("/dns", methods=["POST"])
def dns_lookup():
    """안전한 DNS 조회: shell=False + 입력 검증"""
    domain = request.form.get("domain", "").strip()

    # 1. 입력값 검증
    if not validate_domain(domain):
        return jsonify({
            "status": "error",
            "message": "유효하지 않은 도메인 형식입니다."
        })

    try:
        # 2. shell=False로 안전하게 실행
        result = subprocess.run(
            ["nslookup", domain],
            shell=False,
            capture_output=True,
            text=True,
            timeout=10
        )
        return jsonify({
            "status": "success",
            "output": result.stdout
        })
    except subprocess.TimeoutExpired:
        return jsonify({"status": "error", "message": "요청 시간이 초과되었습니다"})
    except Exception as e:
        return jsonify({"status": "error", "message": "명령 실행 중 오류가 발생했습니다"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
