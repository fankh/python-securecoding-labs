"""
Chapter 02: Input Validation Tests
Run: pytest test_app.py -v
"""
import pytest
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestVulnerableApp:
    """취약한 버전 테스트"""

    @pytest.fixture
    def client(self):
        from vulnerable.app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_index_returns_200(self, client):
        """메인 페이지 접근"""
        resp = client.get('/')
        assert resp.status_code == 200

    def test_register_valid_input(self, client):
        """정상 입력 테스트"""
        resp = client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'age': '25',
            'website': 'http://example.com'
        })
        assert resp.status_code == 200
        assert b'testuser' in resp.data

    def test_blacklist_bypass_uppercase(self, client):
        """취약점: 블랙리스트 우회 (대소문자)"""
        resp = client.post('/register', data={
            'username': '<SCRIPT>alert(1)</SCRIPT>',
            'email': 'test@example.com',
            'age': '25',
            'website': 'http://example.com'
        })
        # 취약한 버전은 이를 허용함
        assert resp.status_code == 200

    def test_no_type_validation(self, client):
        """취약점: 타입 검증 없음"""
        resp = client.post('/register', data={
            'username': 'test',
            'email': 'not-an-email',
            'age': 'not-a-number',
            'website': 'not-a-url'
        })
        assert resp.status_code == 200

    def test_search_endpoint(self, client):
        """검색 엔드포인트 테스트"""
        resp = client.get('/search?q=test')
        assert resp.status_code == 200


class TestSecureApp:
    """안전한 버전 테스트"""

    @pytest.fixture
    def client(self):
        from secure.app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_index_returns_200(self, client):
        """메인 페이지 접근"""
        resp = client.get('/')
        assert resp.status_code == 200

    def test_register_valid_input(self, client):
        """정상 입력 테스트"""
        resp = client.post('/register', data={
            'username': 'valid_user',
            'email': 'test@example.com',
            'age': '25',
            'website': 'http://example.com'
        })
        assert resp.status_code == 200

    def test_rejects_invalid_username(self, client):
        """보안: 특수문자 포함 사용자명 처리"""
        resp = client.post('/register', data={
            'username': '<script>alert(1)</script>',
            'email': 'test@example.com',
            'age': '25',
            'website': 'http://example.com'
        })
        # 에러 응답 또는 에러 메시지 포함
        assert resp.status_code == 400 or b'error' in resp.data.lower()

    def test_rejects_invalid_email(self, client):
        """보안: 잘못된 이메일 형식 처리"""
        resp = client.post('/register', data={
            'username': 'validuser',
            'email': 'not-an-email',
            'age': '25',
            'website': 'http://example.com'
        })
        assert resp.status_code == 400 or b'error' in resp.data.lower()

    def test_rejects_invalid_age(self, client):
        """보안: 범위 외 나이 처리"""
        resp = client.post('/register', data={
            'username': 'validuser',
            'email': 'test@example.com',
            'age': '200',
            'website': 'http://example.com'
        })
        assert resp.status_code == 400 or b'error' in resp.data.lower()

    def test_safe_regex_search(self, client):
        """보안: 안전한 정규식 검색"""
        resp = client.get('/search?q=test')
        assert resp.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
