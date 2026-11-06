import json
from pathlib import Path

import pytest

from app.mock import data

FIXTURES_PATH = Path(data.__file__).with_name("fixtures.json")


def _lookup(mapping, path):
    cur = mapping
    for key in path:
        cur = cur[key]
    return cur


@pytest.mark.parametrize("domain", data.DOMAINS, ids=list(data.DOMAINS))
def test_fixture_returns_deep_copy(domain):
    expected = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))[domain]
    first = data.fixture(domain)
    assert first == expected
    first["synthetic"] = not first["synthetic"]
    if "items" in first:
        first["items"][0]["synthetic"] = False
        first["items"].append({"mutated": True})
    assert data.fixture(domain) == expected


@pytest.mark.parametrize(
    ("inject", "expected_costs"),
    [
        ((), {"LU-PH-001": 180, "LU-PH-002": 260, "LU-PH-003": 95}),
        ([], {"LU-PH-001": 180, "LU-PH-002": 260, "LU-PH-003": 95}),
        (["bad_cost"], {"LU-PH-001": data.BAD_COST_PHP, "LU-PH-002": 260, "LU-PH-003": 95}),
        (["unknown_fault"], {"LU-PH-001": 180, "LU-PH-002": 260, "LU-PH-003": 95}),
        (["unknown_a", "unknown_b"], {"LU-PH-001": 180, "LU-PH-002": 260, "LU-PH-003": 95}),
        (["bad_cost", "unknown_fault"], {"LU-PH-001": data.BAD_COST_PHP, "LU-PH-002": 260, "LU-PH-003": 95}),
    ],
    ids=[
        "default_tuple",
        "empty_list",
        "bad_cost_only",
        "unknown_single",
        "unknown_multiple",
        "bad_cost_with_unknown",
    ],
)
def test_facts_for_injections_and_isolation(inject, expected_costs):
    raw_fixtures = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    expected = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    for item in expected["suppliers"]["items"]:
        item["unit_cost_php"] = expected_costs[item["sku"]]

    result = data.facts_for(inject)
    assert result == expected
    assert data.facts_for([]) == raw_fixtures


@pytest.mark.parametrize(
    ("sample_path", "fixture_path", "expected"),
    [
        (("product", "selling_price_php"), ("products", "items", 0, "selling_price_php"), 499),
        (("product", "supplier_unit_cost_php"), ("suppliers", "items", 0, "unit_cost_php"), 180),
        (("product", "shipping_php"), ("logistics", "shipping_php"), 75),
        (("product", "payment_fee_php"), ("finance", "payment_fee_php"), 18),
        (("budget_php",), ("finance", "budget_php"), 15000),
        (("product", "stock"), ("products", "items", 0, "stock"), 50),
        (("orders", "leads"), ("leads", "total"), 100),
        (("orders", "confirmed"), ("leads", "confirmed"), 20),
        (("orders", "delivered"), ("orders", "delivered"), 15),
        (("orders", "returned"), ("orders", "returned"), 2),
        (("campaign", "status"), ("campaigns", "items", 0, "status"), "DRAFT"),
        (("campaign", "spend_php"), ("campaigns", "items", 0, "spend_php"), 4000),
        (("market",), ("market", "market"), "Philippines"),
        (("currency",), ("market", "currency"), "PHP"),
        (("product", "sku"), ("products", "items", 0, "sku"), "LU-PH-001"),
        (("product", "name"), ("products", "items", 0, "name"), "Demo bracelet"),
        (("campaign", "tracking_ok"), ("ads", "tracking_ok"), True),
    ],
    ids=[
        "price",
        "cost",
        "shipping",
        "payment_fee",
        "budget",
        "stock",
        "leads",
        "confirmed",
        "delivered",
        "returned",
        "campaign_status",
        "spend",
        "market",
        "currency",
        "sku",
        "product_name",
        "tracking_ok",
    ],
)
def test_sample_matches_fixture_values(sample_path, fixture_path, expected):
    raw_fixtures = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    fixture_value = _lookup(raw_fixtures, fixture_path)
    sample_value = _lookup(data.sample(), sample_path)
    assert sample_value == fixture_value == expected


@pytest.mark.parametrize(
    ("inject", "expected_cost"),
    [
        (None, 180),
        ([], 180),
        (["unknown_fault"], 180),
        (["bad_cost"], 9999),
    ],
    ids=[
        "default_sample",
        "facts_empty",
        "facts_unknown",
        "facts_bad_cost",
    ],
)
def test_sample_supplier_cost_with_facts(inject, expected_cost):
    facts = None if inject is None else data.facts_for(inject)
    result = data.sample(facts)
    assert result["product"]["supplier_unit_cost_php"] == expected_cost
