"""
Chapter 05: XSS Tests
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
        if os.path.exists('guestbook.db'):
            os.remove('guestbook.db')
        init_db()
        with app.test_client() as client:
            yield client

    def test_index(self, client):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_post_message(self, client):
        resp = client.post('/post', data={'name': 'Test', 'message': 'Hello'})
        assert resp.status_code == 200

    def test_xss_stored(self, client):
        """취약점: XSS 저장"""
        resp = client.post('/post', data={'name': 'X', 'message': '<script>alert(1)</script>'})
        assert resp.status_code == 200


class TestSecureApp:
    @pytest.fixture
    def client(self):
        from secure.app import app, init_db
        app.config['TESTING'] = True
        if os.path.exists('guestbook_secure.db'):
            os.remove('guestbook_secure.db')
        init_db()
        with app.test_client() as client:
            yield client

    def test_index(self, client):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_csp_header(self, client):
        """보안: CSP 헤더"""
        resp = client.get('/')
        assert 'Content-Security-Policy' in resp.headers


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
