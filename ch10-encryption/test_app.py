"""
Chapter 10: Encryption Tests
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
        from vulnerable.app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_index(self, client):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_encrypt(self, client):
        resp = client.post('/encrypt', data={'plaintext': 'hello'})
        assert resp.status_code == 200

    def test_hash(self, client):
        resp = client.post('/hash', data={'text': 'password'})
        assert resp.status_code == 200


class TestSecureApp:
    @pytest.fixture
    def client(self):
        os.environ['ENCRYPTION_KEY'] = '0123456789abcdef' * 4
        from secure.app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_index(self, client):
        resp = client.get('/')
        assert resp.status_code == 200

    def test_encrypt_decrypt(self, client):
        resp = client.post('/encrypt', data={'plaintext': 'hello'})
        assert resp.status_code == 200
        data = json.loads(resp.data)
        ciphertext = data.get('ciphertext', '')

        resp = client.post('/decrypt', data={'ciphertext': ciphertext})
        assert resp.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
