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
        resp = client.post('/encrypt', data={'data': 'hello'})
        assert resp.status_code == 200
        result = json.loads(resp.data)
        assert result['status'] == 'success'
        assert 'encrypted' in result

    def test_hash(self, client):
        resp = client.post('/hash', data={'data': 'password'})
        assert resp.status_code == 200
        result = json.loads(resp.data)
        assert 'md5' in result
        assert 'sha1' in result


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
        resp = client.post('/encrypt', data={'data': 'hello'})
        assert resp.status_code == 200
        result = json.loads(resp.data)
        assert result['status'] == 'success'
        encrypted_data = result['encrypted']

        resp = client.post('/decrypt', data={'encrypted': encrypted_data})
        assert resp.status_code == 200
        result = json.loads(resp.data)
        assert result['status'] == 'success'
        assert result['decrypted'] == 'hello'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
