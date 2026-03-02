"""
Chapter 11: Error Handling Tests
Run: python -m pytest test_app.py -v
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

    def test_transfer_no_rollback(self, client):
        """취약점: 에러 시 rollback 없음 → 잔액 불일치"""
        # 초기 잔액 확인
        resp = client.get('/balance')
        balances = json.loads(resp.data)
        admin_before = next(b['balance'] for b in balances if b['username'] == 'admin')

        # 송금 중 에러 발생 (receiver="error"로 시뮬레이션)
        resp = client.post('/transfer', data={
            "from": "admin", "to": "error", "amount": "300"
        })
        assert resp.status_code == 500

        # 잔액 확인: rollback 없으므로 admin 잔액이 차감된 상태
        resp = client.get('/balance')
        balances = json.loads(resp.data)
        admin_after = next(b['balance'] for b in balances if b['username'] == 'admin')
        assert admin_after == admin_before - 300  # 돈이 사라짐!


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

    def test_transfer_rollback(self, client):
        """보안: 에러 시 rollback → 잔액 보존"""
        # 초기 잔액 확인
        resp = client.get('/balance')
        balances = json.loads(resp.data)
        admin_before = next(b['balance'] for b in balances if b['username'] == 'admin')

        # 송금 중 에러 발생 (receiver="error"로 시뮬레이션)
        resp = client.post('/transfer', data={
            "from": "admin", "to": "error", "amount": "300"
        })
        assert resp.status_code == 500

        # 잔액 확인: rollback으로 admin 잔액이 원래대로 유지
        resp = client.get('/balance')
        balances = json.loads(resp.data)
        admin_after = next(b['balance'] for b in balances if b['username'] == 'admin')
        assert admin_after == admin_before  # 잔액 보존!

    def test_transfer_success(self, client):
        """정상 송금 테스트"""
        resp = client.post('/transfer', data={
            "from": "admin", "to": "alice", "amount": "200"
        })
        assert resp.status_code == 200

        resp = client.get('/balance')
        balances = json.loads(resp.data)
        admin_balance = next(b['balance'] for b in balances if b['username'] == 'admin')
        alice_balance = next(b['balance'] for b in balances if b['username'] == 'alice')
        assert admin_balance == 800
        assert alice_balance == 1200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
