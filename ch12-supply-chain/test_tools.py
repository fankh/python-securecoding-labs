"""
Chapter 12: Supply Chain Tests
Run: pytest test_tools.py -v
"""
import pytest
import subprocess
import sys
import os
import re


class TestDependencyFiles:
    def test_vulnerable_requirements_exist(self):
        assert os.path.exists('requirements_vulnerable.txt')

    def test_secure_requirements_exist(self):
        assert os.path.exists('requirements_secure.txt')

    def test_scan_script_syntax(self):
        result = subprocess.run(
            [sys.executable, '-m', 'py_compile', 'scan_dependencies.py'],
            capture_output=True
        )
        assert result.returncode == 0

    def test_check_hashes_syntax(self):
        result = subprocess.run(
            [sys.executable, '-m', 'py_compile', 'check_hashes.py'],
            capture_output=True
        )
        assert result.returncode == 0

    def test_secure_uses_pinned_versions(self):
        with open('requirements_secure.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        assert '==' in content

    def test_vulnerable_has_old_versions(self):
        """취약한 requirements에 알려진 구버전이 포함되어 있는지 확인"""
        with open('requirements_vulnerable.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        # flask==2.2.0은 알려진 취약 버전 (PYSEC-2023-62)
        assert 'flask==2.2.0' in content.lower() or 'Flask==2.2.0' in content

    def test_secure_has_newer_versions(self):
        """안전한 requirements가 취약한 것보다 새 버전을 사용하는지 확인"""
        def parse_versions(filepath):
            versions = {}
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '==' in line and not line.startswith('#'):
                        package_name, version = line.split('==', 1)
                        versions[package_name.strip().lower()] = version.strip()
            return versions

        vulnerable_versions = parse_versions('requirements_vulnerable.txt')
        secure_versions = parse_versions('requirements_secure.txt')

        common_packages = set(vulnerable_versions.keys()) & set(secure_versions.keys())
        assert len(common_packages) > 0

        # 안전한 버전이 취약한 버전보다 높은지 확인 (주 버전 기준)
        for package_name in common_packages:
            vulnerable_major = int(vulnerable_versions[package_name].split('.')[0])
            secure_major = int(secure_versions[package_name].split('.')[0])
            assert secure_major >= vulnerable_major, \
                f"{package_name}: secure({secure_versions[package_name]}) should be >= vulnerable({vulnerable_versions[package_name]})"

    def test_vulnerable_no_hash_pinning(self):
        """취약한 requirements에는 해시 핀닝이 없는지 확인"""
        with open('requirements_vulnerable.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        assert '--hash' not in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
