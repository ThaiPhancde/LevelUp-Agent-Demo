"""Single source of mock business data. Router, /sample and agents all read through here."""
import json
import re
from copy import deepcopy
from pathlib import Path

_FIXTURES = json.loads(Path(__file__).with_name('fixtures.json').read_text(encoding='utf-8'))
DOMAINS = tuple(_FIXTURES)
BAD_COST_PHP = 9999  # DEMO_ONLY P5: injected supplier cost for LU-PH-001

_DEFAULT_OBJECTIVES = {
    '',
    'Phân tích thị trường Philippines, chọn sản phẩm tiềm năng và lập chiến dịch bán hàng giả lập.',
    'Đề xuất kế hoạch bán thử sản phẩm tại Philippines, không chạy quảng cáo thật.',
}

_MARKET_ALIASES = [
    (r'thái\s*lan|thailand', 'Thái Lan'),
    (r'việt\s*nam|vietnam', 'Việt Nam'),
    (r'singapore', 'Singapore'),
    (r'malaysia', 'Malaysia'),
    (r'indonesia', 'Indonesia'),
    (r'đài\s*loan|taiwan', 'Đài Loan'),
    (r'nhật\s*bản|japan', 'Nhật Bản'),
    (r'hàn\s*quốc|korea', 'Hàn Quốc'),
    (r'philippines', 'Philippines'),
]


def _extract_custom_product_name(objective: str) -> str:
    # Look for explicit product name patterns in Vietnamese or English
    patterns = [
        r'(?:sản phẩm|bán thử|ra mắt|kinh doanh|mặt hàng)\s+([^,.;—\-]{4,55})',
        r'["“]([^"”]{4,55})["”]',
    ]
    for pat in patterns:
        m = re.search(pat, objective, flags=re.IGNORECASE)
        if m:
            cand = m.group(1).strip()
            cand = re.sub(r'\s+(?:tại|ở|với|ngân sách|giá|mục tiêu).*$', '', cand, flags=re.IGNORECASE).strip()
            if len(cand) >= 4:
                return cand
    return 'Máy pha cà phê cầm tay EspressoGo'


def _apply_custom_objective(facts: dict, objective: str | None) -> None:
    if not objective or not isinstance(objective, str):
        return
    obj = objective.strip()
    if len(obj) < 28 or obj in _DEFAULT_OBJECTIVES:
        return
    # Keep default fixtures if it's the standard Philippines bracelet prompt without custom product/market
    if 'philippines' in obj.lower() and ('bracelet' in obj.lower() or 'vòng tay' in obj.lower() or 'sản phẩm tiềm năng' in obj.lower()):
        return

    # 1. Detect target market
    market_name = 'Đông Nam Á'
    for pat, name in _MARKET_ALIASES:
        if re.search(pat, obj, flags=re.IGNORECASE):
            market_name = name
            break
    facts['market']['market'] = market_name
    facts['market']['demand_signal'] = 'synthetic_high_growth'

    # 2. Detect custom product name & price/budget overrides
    prod_name = _extract_custom_product_name(obj)
    price_match = re.search(r'giá(?:\s*bán|\s*dự kiến)?\s*(\d{3,5})', obj, flags=re.IGNORECASE)
    budget_match = re.search(r'ngân\s*sách(?:\s*quảng\s*cáo|\s*thử\s*nghiệm)?\s*(\d{3,6})', obj, flags=re.IGNORECASE)

    price = int(price_match.group(1)) if price_match else 1290
    spend = int(budget_match.group(1)) if budget_match else 3500
    unit_cost = max(120, round(price * 0.35))

    # Update the 3 candidate SKUs to reflect the custom product line
    items = facts['products']['items']
    sup_items = facts['suppliers']['items']
    items[0]['name'] = prod_name
    items[0]['selling_price_php'] = price
    items[0]['stock'] = 80
    sup_items[0]['unit_cost_php'] = unit_cost

    items[1]['name'] = f'{prod_name} Pro'
    items[1]['selling_price_php'] = round(price * 1.35)
    items[1]['stock'] = 45
    sup_items[1]['unit_cost_php'] = round(unit_cost * 1.4)

    items[2]['name'] = f'Bộ phụ kiện {prod_name}'
    items[2]['selling_price_php'] = max(199, round(price * 0.45))
    items[2]['stock'] = 150
    sup_items[2]['unit_cost_php'] = max(70, round(unit_cost * 0.42))

    # Update campaign spend and healthy conversion funnel (leads=100 so spend/100 has exact 2-decimal precision)
    facts['ads']['budget_php'] = spend
    facts['campaigns']['items'][0]['spend_php'] = spend
    facts['finance']['budget_php'] = max(15000, spend * 4)
    facts['leads']['total'] = 100
    facts['leads']['confirmed'] = 35
    facts['orders']['delivered'] = 28
    facts['orders']['returned'] = 2


def fixture(domain: str) -> dict:
    return deepcopy(_FIXTURES[domain])


def facts_for(inject=(), objective: str | None = None) -> dict:
    """Run-scoped copy of all fixtures with custom scenario & error injections applied. Never mutates fixtures."""
    facts = deepcopy(_FIXTURES)
    _apply_custom_objective(facts, objective)
    if 'bad_cost' in (inject or ()):
        for item in facts['suppliers']['items']:
            if item['sku'] == 'LU-PH-001':
                item['unit_cost_php'] = BAD_COST_PHP
    return facts


def sample(facts=None) -> dict:
    """Legacy /sample shape, derived from fixtures so there is only one set of numbers."""
    f = facts or _FIXTURES
    prod = next(i for i in f['products']['items'] if i['sku'] == 'LU-PH-001')
    sup = next(i for i in f['suppliers']['items'] if i['sku'] == 'LU-PH-001')
    camp = f['campaigns']['items'][0]
    return {
        'market': f['market']['market'], 'currency': f['market']['currency'], 'budget_php': f['finance']['budget_php'],
        'product': {'sku': prod['sku'], 'name': prod['name'], 'supplier_unit_cost_php': sup['unit_cost_php'],
                    'selling_price_php': prod['selling_price_php'], 'shipping_php': f['logistics']['shipping_php'],
                    'payment_fee_php': f['finance']['payment_fee_php'], 'stock': prod['stock']},
        'orders': {'leads': f['leads']['total'], 'confirmed': f['leads']['confirmed'],
                   'delivered': f['orders']['delivered'], 'returned': f['orders']['returned']},
        'campaign': {'status': camp['status'], 'spend_php': camp['spend_php'], 'tracking_ok': f['ads']['tracking_ok']},
        'note': 'All numbers are synthetic. No verified market demand or live supplier data.',
    }
