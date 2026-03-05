#!/usr/bin/env python3
"""
의존성 보안 스캔 도구
- pip-audit을 사용한 취약점 검사
- safety를 사용한 보안 검사
- SBOM 생성
"""
import subprocess
import sys
import json
from pathlib import Path


def run_command(cmd, description):
    """명령어 실행 및 결과 출력"""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    print(f"$ {' '.join(cmd)}\n")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        print(result.stdout)
        if result.stderr:
            print(f"[STDERR] {result.stderr}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("⏰ 명령어 실행 시간 초과")
        return False
    except FileNotFoundError:
        print(f"❌ 명령어를 찾을 수 없습니다: {cmd[0]}")
        return False


def check_tool_installed(tool_name):
    """도구 설치 여부 확인"""
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "show", tool_name],
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def install_security_tools():
    """보안 검사 도구 설치"""
    tools = ["pip-audit", "safety", "cyclonedx-bom"]

    for tool in tools:
        if not check_tool_installed(tool.replace("-", "_")):
            print(f"📦 {tool} 설치 중...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", tool],
                capture_output=True
            )


def scan_with_pip_audit(requirements_file):
    """pip-audit으로 취약점 스캔"""
    return run_command(
        [sys.executable, "-m", "pip_audit", "--no-deps", "-r", requirements_file],
        f"pip-audit 스캔: {requirements_file}"
    )


def scan_with_safety(requirements_file):
    """safety로 취약점 스캔"""
    return run_command(
        [sys.executable, "-m", "safety", "check", "-r", requirements_file, "--full-report"],
        f"safety 스캔: {requirements_file}"
    )


def generate_sbom(requirements_file, output_file):
    """SBOM (Software Bill of Materials) 생성"""
    return run_command(
        [
            sys.executable, "-m", "cyclonedx_py",
            "requirements",
            requirements_file,
            "-o", output_file,
            "--format", "json"
        ],
        f"SBOM 생성: {output_file}"
    )


def check_typosquatting():
    """타이포스쿼팅 패키지 경고"""
    dangerous_typos = {
        "reqeusts": "requests",
        "requets": "requests",
        "python-dateutil": "dateutil (legitimate)",
        "python3-dateutil": "python-dateutil",
        "beautifulsoup": "beautifulsoup4",
        "crypto": "pycryptodome",
    }

    print(f"\n{'='*60}")
    print("⚠️  타이포스쿼팅 경고")
    print(f"{'='*60}")
    print("\n주의해야 할 패키지명 예시:")
    for typo, correct in dangerous_typos.items():
        print(f"  ❌ {typo} → ✅ {correct}")


def main():
    print("🛡️  Python 의존성 보안 스캔 도구")
    print("=" * 60)

    # 보안 도구 설치
    install_security_tools()

    # 취약한 requirements 스캔
    vuln_file = "requirements_vulnerable.txt"
    secure_file = "requirements_secure.txt"

    if Path(vuln_file).exists():
        print("\n" + "🔴" * 30)
        print("취약한 의존성 스캔")
        print("🔴" * 30)
        scan_with_pip_audit(vuln_file)
        scan_with_safety(vuln_file)

    if Path(secure_file).exists():
        print("\n" + "🟢" * 30)
        print("안전한 의존성 스캔")
        print("🟢" * 30)
        scan_with_pip_audit(secure_file)
        scan_with_safety(secure_file)

    # SBOM 생성
    if Path(secure_file).exists():
        generate_sbom(secure_file, "sbom.json")

    # 타이포스쿼팅 경고
    check_typosquatting()

    print("\n" + "=" * 60)
    print("✅ 스캔 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()
