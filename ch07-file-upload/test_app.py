"""
Chapter 07: File Upload Tests
Run: pytest test_app.py -v
"""
import pytest
import sys
import os
import io

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestVulnerableApp:
    @pytest.fixture
    def client(self):
        from vulnerable.app import app
        app.config['TESTING'] = True
        os.makedirs('uploads', exist_ok=True)
        with app.test_client() as client:
            yield client

    def test_index(self, client):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_upload_txt(self, client):
        data = {'file': (io.BytesIO(b'test'), 'test.txt')}
        resp = client.post('/upload', data=data, content_type='multipart/form-data')
        assert resp.status_code == 200

    def test_upload_php(self, client):
        """취약점: PHP 파일 허용"""
        data = {'file': (io.BytesIO(b'<?php ?>'), 'shell.php')}
        resp = client.post('/upload', data=data, content_type='multipart/form-data')
        assert resp.status_code == 200


class TestSecureApp:
    @pytest.fixture
    def client(self):
        from secure.app import app
        app.config['TESTING'] = True
        os.makedirs('uploads_secure', exist_ok=True)
        with app.test_client() as client:
            yield client

    def test_index(self, client):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_reject_php(self, client):
        """보안: PHP 파일 거부"""
        data = {'file': (io.BytesIO(b'<?php ?>'), 'shell.php')}
        resp = client.post('/upload', data=data, content_type='multipart/form-data')
        assert resp.status_code == 400


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
