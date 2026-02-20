"""
Chapter 08: Deserialization Tests
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

    def test_save_session(self, client):
        resp = client.post('/save_session', data={'username': 'test'})
        assert resp.status_code == 200


class TestSecureApp:
    @pytest.fixture
    def client(self):
        os.environ['SECRET_KEY'] = 'test-secret-key'
        from secure.app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_index(self, client):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_save_session(self, client):
        resp = client.post('/save_session', data={'username': 'test'})
        assert resp.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
