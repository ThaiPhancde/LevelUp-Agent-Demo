import copy
import json
import pathlib
import pytest

from app.agents import business as b

_FIXTURES_PATH = pathlib.Path(__file__).resolve().parent.parent / 'app' / 'mock' / 'fixtures.json'
_RAW_FACTS = json.loads(_FIXTURES_PATH.read_text(encoding='utf-8'))


def _facts():
    return copy.deepcopy(_RAW_FACTS)


@pytest.mark.parametrize(
    ('field', 'expected'),
    [
        ('type', 'market_report'),
        ('agent_id', '02'),
        ('synthetic', True),
        ('market', 'Philippines'),
        ('currency', 'PHP'),
        ('demand_signal', 'synthetic_medium'),
        ('funnel', {'leads': 100, 'confirmed': 20, 'delivered': 15, 'returned': 2}),
        ('confirm_rate', 0.2),
        ('delivery_rate', 0.75),
        ('return_rate', 0.1333),
    ],
    ids=[
        'market_type',
        'market_agent_id',
        'market_synthetic',
        'market_name',
        'market_currency',
        'market_demand_signal',
        'market_funnel_counts',
        'market_confirm_rate_20_of_100',
        'market_delivery_rate_15_of_20',
        'market_return_rate_2_of_15',
    ],
)
def test_market_default_rates(field, expected):
    out = b.market(_facts(), {})
    assert out[field] == expected


@pytest.mark.parametrize(
    ('leads_total', 'confirmed', 'delivered', 'returned', 'exp_confirm', 'exp_delivery', 'exp_return'),
    [
        (0, 0, 0, 0, 0.0, 0.0, 0.0),
        (50, 0, 0, 0, 0.0, 0.0, 0.0),
        (50, 25, 0, 0, 0.5, 0.0, 0.0),
    ],
    ids=[
        'market_zero_leads',
        'market_zero_confirmed',
        'market_zero_delivered',
    ],
)
def test_market_zero_denominators(leads_total, confirmed, delivered, returned, exp_confirm, exp_delivery, exp_return):
    facts = _facts()
    facts['leads']['total'] = leads_total
    facts['leads']['confirmed'] = confirmed
    facts['orders']['delivered'] = delivered
    facts['orders']['returned'] = returned
    out = b.market(facts, {})
    assert (
        out['confirm_rate'] == exp_confirm
        and out['delivery_rate'] == exp_delivery
        and out['return_rate'] == exp_return
    )


@pytest.mark.parametrize(
    ('idx', 'sku', 'price', 'cost', 'margin', 'margin_pct', 'has_data', 'passes'),
    [
        (0, 'LU-PH-001', 499, 180, 226.0, 45.29, True, True),
        (1, 'LU-PH-002', 699, 260, 346.0, 49.5, False, True),
        (2, 'LU-PH-003', 299, 95, 111.0, 37.12, False, True),
    ],
    ids=[
        'sku_001_bracelet_margin_226_pct_45_29',
        'sku_002_necklace_margin_346_pct_49_5',
        'sku_003_strap_margin_111_pct_37_12',
    ],
)
def test_product_candidate_margins(idx, sku, price, cost, margin, margin_pct, has_data, passes):
    out = b.product(_facts(), {})
    cand = out['candidates'][idx]
    assert (
        cand['sku'] == sku
        and cand['selling_price_php'] == price
        and cand['unit_cost_php'] == cost
        and cand['margin_per_unit_php'] == margin
        and cand['margin_pct'] == margin_pct
        and cand['has_test_sale_data'] is has_data
        and cand['passes_margin'] is passes
    )


@pytest.mark.parametrize(
    ('campaigns', 'cost_overrides', 'expected_sku', 'expected_warnings'),
    [
        (
            None,
            {},
            'LU-PH-001',
            [],
        ),
        (
            None,
            {'LU-PH-003': 180},
            'LU-PH-001',
            [],
        ),
        (
            None,
            {'LU-PH-001': 306},
            'LU-PH-001',
            ['LU-PH-001: biên 20.04% dưới ngưỡng 30%'],
        ),
        (
            [],
            {},
            'LU-PH-002',
            [],
        ),
    ],
    ids=[
        'default_selects_sku_001_with_campaign_no_warning',
        'non_selected_sku_below_30_pct_produces_no_warning',
        'selected_sku_below_30_pct_produces_warning',
        'no_campaign_evidence_selects_highest_passing_margin_sku_002',
    ],
)
def test_product_selection_and_warnings(campaigns, cost_overrides, expected_sku, expected_warnings):
    facts = _facts()
    if campaigns is not None:
        facts['campaigns']['items'] = campaigns
    for item in facts['suppliers']['items']:
        if item['sku'] in cost_overrides:
            item['unit_cost_php'] = cost_overrides[item['sku']]
    out = b.product(facts, {})
    assert out['selected_sku'] == expected_sku and out['warnings'] == expected_warnings


@pytest.mark.parametrize(
    ('field', 'expected'),
    [
        ('sku', 'LU-PH-001'),
        ('selling_price_php', 499),
        ('unit_cost_php', 180),
        ('shipping_php', 75),
        ('payment_fee_php', 18),
        ('margin_per_unit_php', 226.0),
        ('margin_pct', 45.29),
        ('campaign_budget_php', 4000),
        ('breakeven_orders', 18),
        ('total_budget_php', 15000),
        ('stock', 50),
    ],
    ids=[
        'offer_sku',
        'offer_selling_price_499',
        'offer_unit_cost_180',
        'offer_shipping_75',
        'offer_payment_fee_18',
        'offer_margin_226',
        'offer_margin_pct_45_29',
        'offer_budget_4000',
        'offer_breakeven_18',
        'offer_total_budget_15000',
        'offer_stock_50',
    ],
)
def test_offer_default_sku_001(field, expected):
    out = b.offer(_facts(), {'product': {'selected_sku': 'LU-PH-001'}})
    assert out[field] == expected


@pytest.mark.parametrize(
    ('sku', 'unit_cost_override', 'exp_margin', 'exp_pct', 'exp_budget', 'exp_breakeven'),
    [
        ('LU-PH-001', 9999, -9593.0, -1922.44, 4000, 0),
        ('LU-PH-002', None, 346.0, 49.5, 4000, 12),
    ],
    ids=[
        'offer_unit_cost_9999_gives_negative_margin_and_breakeven_0',
        'offer_sku_002_uses_ads_fallback_budget_4000_and_breakeven_12',
    ],
)
def test_offer_variants(sku, unit_cost_override, exp_margin, exp_pct, exp_budget, exp_breakeven):
    facts = _facts()
    if unit_cost_override is not None:
        for item in facts['suppliers']['items']:
            if item['sku'] == sku:
                item['unit_cost_php'] = unit_cost_override
    out = b.offer(facts, {'product': {'selected_sku': sku}})
    assert (
        out['margin_per_unit_php'] == exp_margin
        and out['margin_pct'] == exp_pct
        and out['campaign_budget_php'] == exp_budget
        and out['breakeven_orders'] == exp_breakeven
    )


@pytest.mark.parametrize(
    ('field', 'expected'),
    [
        ('sku', 'LU-PH-001'),
        ('product_name', 'Demo bracelet'),
        ('angles', ['price_question', 'product_question', 'shipping_question']),
        ('intent_counts', {'product_question': 1, 'price_question': 1, 'shipping_question': 1}),
        (
            'ad_drafts',
            [
                'Demo bracelet — 499 PHP. Delivery in 3 days.',
                'Questions about shipping? Flat 75 PHP, arrives in 3 days.',
                'Everyday style: Demo bracelet for 499 PHP.',
            ],
        ),
        ('status', 'DRAFT'),
    ],
    ids=[
        'content_sku',
        'content_product_name',
        'content_angles_only_from_lead_stage',
        'content_intent_counts_only_lead_stage',
        'content_three_ad_drafts',
        'content_status_draft',
    ],
)
def test_content_brief(field, expected):
    inputs = {'offer': {'sku': 'LU-PH-001', 'selling_price_php': 499, 'shipping_php': 75}}
    out = b.content(_facts(), inputs)
    assert out[field] == expected


@pytest.mark.parametrize(
    ('field', 'expected'),
    [
        ('sku', 'LU-PH-001'),
        ('campaign_id', 'CMP-LU-PH-001'),
        ('status', 'DRAFT'),
        ('budget_php', 4000),
        ('budget_share_pct', 26.67),
        ('ad_draft_count', 3),
        ('tracking_ok', True),
        (
            'requested_actions',
            [{'tool': 'meta_ads.create_draft', 'target': 'CMP-LU-PH-001', 'budget_php': 4000}],
        ),
    ],
    ids=[
        'campaign_sku',
        'campaign_id_cmp_lu_ph_001',
        'campaign_status_draft',
        'campaign_budget_4000',
        'campaign_budget_share_26_67_pct',
        'campaign_ad_draft_count_3',
        'campaign_tracking_ok',
        'campaign_single_create_draft_action',
    ],
)
def test_campaign_plan(field, expected):
    inputs = {
        'offer': {'sku': 'LU-PH-001', 'campaign_budget_php': 4000, 'total_budget_php': 15000},
        'content': {'ad_drafts': ['d1', 'd2', 'd3']},
    }
    out = b.campaign(_facts(), inputs)
    assert out[field] == expected


@pytest.mark.parametrize(
    ('field', 'expected'),
    [
        ('sku', 'LU-PH-001'),
        ('leads', 100),
        ('confirmed', 20),
        ('unconfirmed', 80),
        ('confirm_rate', 0.2),
        ('cost_per_lead_php', 40.0),
        ('cost_per_confirmed_php', 200.0),
        ('open_conversations', ['CONV-001', 'CONV-002', 'CONV-003']),
        (
            'requested_actions',
            [
                {'tool': 'crm.reply_draft', 'target': 'CONV-001'},
                {'tool': 'crm.reply_draft', 'target': 'CONV-002'},
                {'tool': 'crm.reply_draft', 'target': 'CONV-003'},
            ],
        ),
    ],
    ids=[
        'leads_sku',
        'leads_total_100',
        'leads_confirmed_20',
        'leads_unconfirmed_80',
        'leads_confirm_rate_0_2',
        'leads_cost_per_lead_40',
        'leads_cost_per_confirmed_200',
        'leads_open_conversations_lead_stage_ids',
        'leads_reply_draft_actions',
    ],
)
def test_leads_report(field, expected):
    inputs = {'campaign': {'sku': 'LU-PH-001', 'budget_php': 4000}}
    out = b.leads(_facts(), inputs)
    assert out[field] == expected


@pytest.mark.parametrize(
    ('field', 'expected'),
    [
        ('sku', 'LU-PH-001'),
        ('confirmed', 20),
        ('delivered', 15),
        ('returned', 2),
        ('in_transit', 5),
        ('delivery_days', 3),
        ('provider', 'Mock 3PL'),
        (
            'tickets',
            [
                {'conversation_id': 'CONV-008', 'intent': 'complaint', 'stage': 'delivered'},
                {'conversation_id': 'CONV-010', 'intent': 'return_request', 'stage': 'returned'},
                {'conversation_id': 'CONV-011', 'intent': 'return_request', 'stage': 'returned'},
                {'conversation_id': 'CONV-012', 'intent': 'complaint', 'stage': 'returned'},
            ],
        ),
        (
            'requested_actions',
            [
                {'tool': 'crm.ticket_note', 'target': 'CONV-008'},
                {'tool': 'crm.ticket_note', 'target': 'CONV-010'},
                {'tool': 'crm.ticket_note', 'target': 'CONV-011'},
                {'tool': 'crm.ticket_note', 'target': 'CONV-012'},
            ],
        ),
    ],
    ids=[
        'care_sku',
        'care_confirmed_20',
        'care_delivered_15',
        'care_returned_2',
        'care_in_transit_5',
        'care_delivery_days_3',
        'care_provider_mock_3pl',
        'care_tickets_complaint_and_return_request',
        'care_ticket_note_actions',
    ],
)
def test_care_report(field, expected):
    inputs = {'leads': {'sku': 'LU-PH-001', 'confirmed': 20}}
    out = b.care(_facts(), inputs)
    assert out[field] == expected


@pytest.mark.parametrize(
    ('field', 'expected'),
    [
        ('sku', 'LU-PH-001'),
        ('selling_price_php', 499),
        ('ad_spend_php', 4000.0),
        ('gross_revenue_php', 7485.0),
        ('net_revenue_php', 6487.0),
        ('net_units', 13),
        ('roas', 1.62),
        ('cpa_confirmed_php', 200.0),
        ('cpa_delivered_php', 266.67),
        ('lead_to_delivered_rate', 0.15),
        ('return_rate', 0.1333),
    ],
    ids=[
        'kpi_sku',
        'kpi_selling_price_499',
        'kpi_ad_spend_4000',
        'kpi_gross_revenue_7485',
        'kpi_net_revenue_6487',
        'kpi_net_units_13',
        'kpi_roas_1_62',
        'kpi_cpa_confirmed_200',
        'kpi_cpa_delivered_266_67',
        'kpi_lead_to_delivered_0_15',
        'kpi_return_rate_0_1333',
    ],
)
def test_kpi_report(field, expected):
    inputs = {
        'leads': {'cost_per_lead_php': 40.0, 'leads': 100, 'confirmed': 20},
        'care': {'sku': 'LU-PH-001', 'delivered': 15, 'returned': 2},
    }
    out = b.kpi(_facts(), inputs)
    assert out[field] == expected


@pytest.mark.parametrize(
    ('offer_in', 'kpi_in', 'exp_before', 'exp_after', 'exp_used_pct', 'exp_risks', 'exp_level'),
    [
        (
            {
                'sku': 'LU-PH-001',
                'margin_per_unit_php': 226.0,
                'breakeven_orders': 18,
                'total_budget_php': 15000,
                'stock': 50,
            },
            {'net_units': 13, 'ad_spend_php': 4000.0, 'return_rate': 0.1333},
            2938.0,
            -1062.0,
            26.67,
            [
                'Chưa hòa vốn: 13 đơn ròng < 18 đơn cần',
                'Tỷ lệ hoàn 13.33% vượt ngưỡng 10%',
            ],
            'HIGH',
        ),
        (
            {
                'sku': 'LU-PH-001',
                'margin_per_unit_php': 226.0,
                'breakeven_orders': 18,
                'total_budget_php': 15000,
                'stock': 50,
            },
            {'net_units': 20, 'ad_spend_php': 4000.0, 'return_rate': 0.1333},
            4520.0,
            520.0,
            26.67,
            ['Tỷ lệ hoàn 13.33% vượt ngưỡng 10%'],
            'MEDIUM',
        ),
        (
            {
                'sku': 'LU-PH-001',
                'margin_per_unit_php': 226.0,
                'breakeven_orders': 18,
                'total_budget_php': 15000,
                'stock': 50,
            },
            {'net_units': 20, 'ad_spend_php': 4000.0, 'return_rate': 0.05},
            4520.0,
            520.0,
            26.67,
            [],
            'LOW',
        ),
        (
            {
                'sku': 'LU-PH-001',
                'margin_per_unit_php': 0.0,
                'breakeven_orders': 0,
                'total_budget_php': 15000,
                'stock': 50,
            },
            {'net_units': 55, 'ad_spend_php': 0.0, 'return_rate': 0.05},
            0.0,
            0.0,
            0.0,
            [
                'Biên lợi nhuận âm hoặc bằng 0: mỗi đơn đều lỗ',
                'Số đơn vượt tồn kho',
            ],
            'HIGH',
        ),
    ],
    ids=[
        'finance_high_risk_default_run_negative_after_ads',
        'finance_medium_risk_positive_after_ads_with_high_return_rate',
        'finance_low_risk_positive_after_ads_and_no_risks',
        'finance_high_risk_non_positive_margin_and_over_stock',
    ],
)
def test_finance_report_and_risk_levels(
    offer_in, kpi_in, exp_before, exp_after, exp_used_pct, exp_risks, exp_level
):
    out = b.finance(_facts(), {'offer': offer_in, 'kpi': kpi_in})
    assert (
        out['contribution_before_ads_php'] == exp_before
        and out['contribution_after_ads_php'] == exp_after
        and out['budget_used_pct'] == exp_used_pct
        and out['risks'] == exp_risks
        and out['risk_level'] == exp_level
    )
