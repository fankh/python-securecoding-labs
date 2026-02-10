"""
Chapter 11: Error Handling Tests
Run: pytest test_app.py -v
"""
import pytest
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestVulnerableApp:
    @pytest.fixture
    def client(self):
        from vulnerable.app import app, init_db
        app.config['TESTING'] = True
        if os.path.exists('users.db'):
            os.remove('users.db')
        init_db()
        with app.test_client() as client:
            yield client

    def test_index(self, client):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_error_exposes_trace(self, client):
        """취약점: 스택 트레이스 노출"""
        resp = client.get('/user?id=abc')
        assert resp.status_code == 500
        data = json.loads(resp.data)
        assert 'traceback' in data or 'Traceback' in str(data)


class TestSecureApp:
    @pytest.fixture
    def client(self):
        from secure.app import app, init_db
        app.config['TESTING'] = True
        if os.path.exists('users.db'):
            os.remove('users.db')
        init_db()
        with app.test_client() as client:
            yield client

    def test_index(self, client):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_error_generic(self, client):
        """보안: 일반적인 에러 메시지"""
        resp = client.get('/user?id=abc')
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert 'traceback' not in str(data).lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
