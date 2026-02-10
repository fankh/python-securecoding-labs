"""
Chapter 12: Supply Chain Tests
Run: pytest test_tools.py -v
"""
import pytest
import subprocess
import sys
import os


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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
