from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_mock_domains_are_independent_and_synthetic():
    paths = ('market', 'meta-ads', 'products', 'suppliers', 'campaigns', 'leads', 'orders', 'logistics', 'customer-conversations', 'finance')
    for path in paths:
        response = client.get(f'/mock/{path}')
        assert response.status_code == 200
        body = response.json()
        assert body['environment'] == 'MOCK_ONLY'
        assert body['synthetic'] is True
        assert body['data']['synthetic'] is True


def test_mock_products_are_not_mutable_between_requests():
    first = client.get('/mock/products').json()
    first['data']['items'][0]['stock'] = 0
    assert client.get('/mock/products').json()['data']['items'][0]['stock'] == 50
