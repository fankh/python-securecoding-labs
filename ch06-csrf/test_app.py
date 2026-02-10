"""
Chapter 06: CSRF Tests
Run: pytest test_app.py -v
"""
import pytest
import sys
import os

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


class TestSecureApp:
    @pytest.fixture
    def client(self):
        from secure.app import app, init_db
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SECRET_KEY'] = 'test-secret-key'
        if os.path.exists('users_secure.db'):
            os.remove('users_secure.db')
        init_db()
        with app.test_client() as client:
            yield client

    def test_index(self, client):
        resp = client.get('/')
        assert resp.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
