"""
Chapter 03: Command Injection Tests
Run: pytest test_app.py -v
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestVulnerableApp:
    @pytest.fixture
    def client(self):
        from vulnerable.app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_index(self, client):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_ping_valid(self, client):
        resp = client.post('/ping', data={'host': '127.0.0.1'})
        assert resp.status_code == 200

    def test_injection_accepted(self, client):
        """취약점: 인젝션 입력 허용"""
        resp = client.post('/ping', data={'host': '127.0.0.1; echo test'})
        assert resp.status_code == 200


class TestSecureApp:
    @pytest.fixture
    def client(self):
        from secure.app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_index(self, client):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_ping_valid(self, client):
        resp = client.post('/ping', data={'host': '127.0.0.1'})
        assert resp.status_code == 200

    def test_injection_blocked(self, client):
        """보안: 인젝션 차단 (에러 응답)"""
        resp = client.post('/ping', data={'host': '127.0.0.1; echo test'})
        # 에러 상태 확인 (status code 또는 JSON 내 error)
        assert resp.status_code == 400 or b'error' in resp.data.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
