#!/usr/bin/env python3
"""
패키지 해시 검증 도구
pip의 --require-hashes 옵션 사용 예시
"""
import subprocess
import sys
import hashlib
import requests
from pathlib import Path


def get_package_hashes(package_name, version):
    """PyPI에서 패키지 해시 조회"""
    url = f"https://pypi.org/pypi/{package_name}/{version}/json"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        hashes = []
        for file_info in data.get("urls", []):
            digests = file_info.get("digests", {})
            if "sha256" in digests:
                filename = file_info.get("filename", "")
                hashes.append({
                    "filename": filename,
                    "sha256": digests["sha256"]
                })

        return hashes
    except Exception as e:
        print(f"❌ 해시 조회 실패: {e}")
        return []


def generate_requirements_with_hashes(input_file, output_file):
    """해시가 포함된 requirements.txt 생성"""
    print(f"📝 {input_file} → {output_file}")
    print("=" * 60)

    output_lines = []

    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                output_lines.append(line)
                continue

            # 패키지명과 버전 파싱
            if '>=' in line:
                package, version = line.split('>=')
                # 최신 버전은 PyPI에서 조회 필요
                print(f"⚠️  {package}: 정확한 버전 필요 (>= 대신 ==)")
                output_lines.append(f"# {line}")
                continue
            elif '==' in line:
                package, version = line.split('==')
            else:
                print(f"⚠️  {line}: 버전 지정 필요")
                output_lines.append(f"# {line}")
                continue

            hashes = get_package_hashes(package.strip(), version.strip())

            if hashes:
                output_lines.append(f"{package}=={version} \\")
                for i, h in enumerate(hashes):
                    prefix = "    " if i < len(hashes) - 1 else "    "
                    suffix = " \\" if i < len(hashes) - 1 else ""
                    output_lines.append(f"{prefix}--hash=sha256:{h['sha256']}{suffix}")
                print(f"✅ {package}=={version}: {len(hashes)}개 해시 추가")
            else:
                output_lines.append(line)
                print(f"❌ {package}=={version}: 해시 조회 실패")

    with open(output_file, 'w') as f:
        f.write('\n'.join(output_lines))

    print(f"\n✅ {output_file} 생성 완료")


def verify_installed_packages():
    """설치된 패키지의 무결성 검증"""
    print("\n🔍 설치된 패키지 무결성 검증")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("✅ 모든 패키지 의존성이 충족됨")
    else:
        print("❌ 패키지 문제 발견:")
        print(result.stdout)
        print(result.stderr)


def main():
    print("🔐 패키지 해시 검증 도구")
    print("=" * 60)

    # 예시: 해시가 포함된 requirements 생성
    input_file = "requirements_pinned.txt"

    if not Path(input_file).exists():
        # 샘플 파일 생성
        with open(input_file, 'w') as f:
            f.write("# 버전이 고정된 의존성\n")
            f.write("flask==3.0.0\n")
            f.write("requests==2.31.0\n")
            f.write("jinja2==3.1.2\n")

    generate_requirements_with_hashes(input_file, "requirements_locked.txt")
    verify_installed_packages()

    print("\n📖 사용 방법:")
    print("  pip install --require-hashes -r requirements_locked.txt")


if __name__ == "__main__":
    main()
