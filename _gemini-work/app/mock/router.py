from fastapi import APIRouter

from app.mock.data import fixture

router = APIRouter(prefix='/mock', tags=['mock'])


def _fixture(domain: str) -> dict:
    return {
        'environment': 'MOCK_ONLY',
        'domain': domain,
        'synthetic': True,
        'data': fixture(domain),
    }


@router.get('/market')
def market(): return _fixture('market')


@router.get('/meta-ads')
def meta_ads(): return _fixture('ads')


@router.get('/products')
def products(): return _fixture('products')


@router.get('/suppliers')
def suppliers(): return _fixture('suppliers')


@router.get('/campaigns')
def campaigns(): return _fixture('campaigns')


@router.get('/leads')
def leads(): return _fixture('leads')


@router.get('/orders')
def orders(): return _fixture('orders')


@router.get('/logistics')
def logistics(): return _fixture('logistics')


@router.get('/customer-conversations')
def customer_conversations(): return _fixture('conversations')


@router.get('/finance')
def finance(): return _fixture('finance')
