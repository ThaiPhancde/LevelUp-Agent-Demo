import copy
import json
import pathlib
import pytest

from app.engines import qa

FIXTURES_PATH = pathlib.Path(__file__).resolve().parents[1] / 'app' / 'mock' / 'fixtures.json'
REF_FACTS = json.loads(FIXTURES_PATH.read_text(encoding='utf-8'))

BUSINESS_KEYS = [
    'market',
    'product',
    'offer',
    'content',
    'campaign',
    'leads',
    'care',
    'kpi',
    'finance',
]


def _valid_artifacts() -> dict:
    return copy.deepcopy({
        'market': {
            'type': 'market_report',
            'agent_id': '02',
            'summary': 'Philippines synthetic funnel: 100 leads, 20 confirmed, 15 delivered, 2 returned.',
            'synthetic': True,
            'market': 'Philippines',
            'currency': 'PHP',
            'demand_signal': 'synthetic_medium',
            'funnel': {'leads': 100, 'confirmed': 20, 'delivered': 15, 'returned': 2},
            'confirm_rate': 0.2,
            'delivery_rate': 0.75,
            'return_rate': 0.1333,
        },
        'product': {
            'type': 'product_shortlist',
            'agent_id': '03',
            'summary': 'Selected LU-PH-001 (Demo bracelet) with 45.29% margin.',
            'synthetic': True,
            'candidates': [
                {
                    'sku': 'LU-PH-001',
                    'name': 'Demo bracelet',
                    'selling_price_php': 499.0,
                    'unit_cost_php': 180.0,
                    'margin_pct': 45.29,
                },
                {
                    'sku': 'LU-PH-002',
                    'name': 'Demo necklace',
                    'selling_price_php': 699.0,
                    'unit_cost_php': 260.0,
                },
                {
                    'sku': 'LU-PH-003',
                    'name': 'Demo phone strap',
                    'selling_price_php': 299.0,
                    'unit_cost_php': 95.0,
                },
            ],
            'selected_sku': 'LU-PH-001',
            'selection_rule': 'funnel_data_then_highest_margin',
        },
        'offer': {
            'type': 'pricing_offer',
            'agent_id': '04',
            'summary': 'LU-PH-001 price 499 PHP, margin 226 PHP, breakeven 18 orders on 4000 PHP budget.',
            'synthetic': True,
            'sku': 'LU-PH-001',
            'selling_price_php': 499.0,
            'unit_cost_php': 180.0,
            'shipping_php': 75.0,
            'payment_fee_php': 18.0,
            'margin_per_unit_php': 226.0,
            'margin_pct': 45.29,
            'campaign_budget_php': 4000.0,
            'breakeven_orders': 18,
            'total_budget_php': 15000.0,
            'stock': 50,
        },
        'content': {
            'type': 'content_brief',
            'agent_id': '05',
            'summary': '3 DRAFT ad creatives for Demo bracelet.',
            'synthetic': True,
            'sku': 'LU-PH-001',
            'product_name': 'Demo bracelet',
            'angles': ['product_question', 'price_question', 'shipping_question'],
            'ad_drafts': [{'draft_id': 'AD-01'}, {'draft_id': 'AD-02'}, {'draft_id': 'AD-03'}],
            'status': 'DRAFT',
        },
        'campaign': {
            'type': 'campaign_plan',
            'agent_id': '06',
            'summary': 'Campaign CMP-LU-PH-001 in DRAFT with 4000 PHP budget.',
            'synthetic': True,
            'sku': 'LU-PH-001',
            'campaign_id': 'CMP-LU-PH-001',
            'status': 'DRAFT',
            'budget_php': 4000.0,
            'budget_share_pct': 26.67,
            'ad_draft_count': 3,
            'requested_actions': [{'tool': 'meta_ads.create_draft'}],
        },
        'leads': {
            'type': 'lead_report',
            'agent_id': '07',
            'summary': '100 leads, 20 confirmed, 80 unconfirmed.',
            'synthetic': True,
            'sku': 'LU-PH-001',
            'leads': 100,
            'confirmed': 20,
            'unconfirmed': 80,
            'confirm_rate': 0.2,
            'cost_per_lead_php': 40.0,
            'cost_per_confirmed_php': 200.0,
            'open_conversations': ['CONV-001', 'CONV-002', 'CONV-003'],
            'requested_actions': [{'tool': 'crm.reply_draft'}],
        },
        'care': {
            'type': 'care_report',
            'agent_id': '08',
            'summary': '15 delivered, 2 returned, 5 in transit.',
            'synthetic': True,
            'sku': 'LU-PH-001',
            'confirmed': 20,
            'delivered': 15,
            'returned': 2,
            'in_transit': 5,
            'delivery_days': 3,
            'provider': 'Mock 3PL',
            'tickets': ['ORD-008', 'ORD-010', 'ORD-011', 'ORD-012'],
            'requested_actions': [{'tool': 'crm.ticket_note'}],
        },
        'kpi': {
            'type': 'kpi_report',
            'agent_id': '09',
            'summary': 'Net revenue 6487 PHP on 13 net units, ROAS 1.62.',
            'synthetic': True,
            'sku': 'LU-PH-001',
            'selling_price_php': 499.0,
            'ad_spend_php': 4000.0,
            'gross_revenue_php': 7485.0,
            'net_revenue_php': 6487.0,
            'net_units': 13,
            'roas': 1.62,
            'cpa_confirmed_php': 200.0,
            'cpa_delivered_php': 266.67,
            'lead_to_delivered_rate': 0.15,
            'return_rate': 0.1333,
        },
        'finance': {
            'type': 'finance_risk_report',
            'agent_id': '10',
            'summary': 'Contribution 2938 PHP before ads and -1062 PHP after ads.',
            'synthetic': True,
            'sku': 'LU-PH-001',
            'margin_per_unit_php': 226.0,
            'net_units': 13,
            'contribution_before_ads_php': 2938.0,
            'contribution_after_ads_php': -1062.0,
            'breakeven_orders': 18,
            'budget_used_pct': 26.67,
            'risks': ['below_breakeven', 'return_rate'],
            'risk_level': 'HIGH',
            'recommendation': 'Keep campaign in DRAFT pending human review',
        },
    })


def test_run_valid_scenario_passes():
    arts = _valid_artifacts()
    res = qa.run(arts, REF_FACTS)
    assert res == {
        'engine': 'qa',
        'status': 'PASS',
        'findings': [],
        'checked': BUSINESS_KEYS,
    }


@pytest.mark.parametrize(
    ('missing_key', 'rejected', 'expected_detail'),
    [
        ('market', None, 'missing artifact'),
        ('offer', None, 'missing artifact'),
        ('finance', None, 'missing artifact'),
        (
            'kpi',
            {'kpi': ['roas: Field required', 'net_units: Input should be a valid integer']},
            'artifact rejected: roas: Field required; net_units: Input should be a valid integer',
        ),
        (
            'campaign',
            {'campaign': ['budget_php: Field required']},
            'artifact rejected: budget_php: Field required',
        ),
    ],
    ids=[
        'missing_market_artifact',
        'missing_offer_artifact',
        'missing_finance_artifact',
        'rejected_kpi_artifact_errors_in_detail',
        'rejected_campaign_artifact_error_in_detail',
    ],
)
def test_schema_missing_and_rejected(missing_key, rejected, expected_detail):
    arts = _valid_artifacts()
    arts.pop(missing_key)
    findings = qa.schema(arts, rejected=rejected)
    assert findings == [
        {
            'rule': 'schema',
            'severity': 'FAIL',
            'task_key': missing_key,
            'detail': expected_detail,
        }
    ]


@pytest.mark.parametrize(
    ('task_key', 'field_to_remove', 'expected_detail'),
    [
        ('market', 'funnel', 'funnel: Field required'),
        ('product', 'selected_sku', 'selected_sku: Field required'),
        ('offer', 'selling_price_php', 'selling_price_php: Field required'),
        ('content', 'ad_drafts', 'ad_drafts: Field required'),
        ('campaign', 'budget_php', 'budget_php: Field required'),
        ('leads', 'unconfirmed', 'unconfirmed: Field required'),
        ('care', 'delivered', 'delivered: Field required'),
        ('kpi', 'roas', 'roas: Field required'),
        ('finance', 'risk_level', 'risk_level: Field required'),
    ],
    ids=[
        'market_missing_funnel',
        'product_missing_selected_sku',
        'offer_missing_selling_price',
        'content_missing_ad_drafts',
        'campaign_missing_budget',
        'leads_missing_unconfirmed',
        'care_missing_delivered',
        'kpi_missing_roas',
        'finance_missing_risk_level',
    ],
)
def test_schema_missing_required_field(task_key, field_to_remove, expected_detail):
    arts = _valid_artifacts()
    del arts[task_key][field_to_remove]
    findings = qa.schema(arts)
    assert findings == [
        {
            'rule': 'schema',
            'severity': 'FAIL',
            'task_key': task_key,
            'detail': expected_detail,
        }
    ]


@pytest.mark.parametrize(
    ('mutator', 'expected_findings'),
    [
        (
            lambda a: (
                a['offer'].update({
                    'unit_cost_php': 9999.0,
                    'margin_per_unit_php': -9593.0,
                    'breakeven_orders': 0,
                }),
                a['finance'].update({
                    'margin_per_unit_php': -9593.0,
                    'contribution_before_ads_php': -124709.0,
                    'contribution_after_ads_php': -128709.0,
                }),
            ),
            [
                {
                    'rule': 'reference',
                    'severity': 'FAIL',
                    'task_key': 'offer',
                    'detail': 'LU-PH-001 unit_cost_php 9999.0 != reference 180',
                }
            ],
        ),
        (
            lambda a: a['product']['candidates'][0].update({'unit_cost_php': 9999.0}),
            [
                {
                    'rule': 'reference',
                    'severity': 'FAIL',
                    'task_key': 'product',
                    'detail': 'LU-PH-001 unit_cost_php 9999.0 != reference 180',
                }
            ],
        ),
        (
            lambda a: a['product']['candidates'][1].update({'unit_cost_php': 350.0}),
            [
                {
                    'rule': 'reference',
                    'severity': 'FAIL',
                    'task_key': 'product',
                    'detail': 'LU-PH-002 unit_cost_php 350.0 != reference 260',
                }
            ],
        ),
        (
            lambda a: a['product']['candidates'][2].update({'unit_cost_php': 120.0}),
            [
                {
                    'rule': 'reference',
                    'severity': 'FAIL',
                    'task_key': 'product',
                    'detail': 'LU-PH-003 unit_cost_php 120.0 != reference 95',
                }
            ],
        ),
        (
            lambda a: a['offer'].update({'unit_cost_php': 180.01}),
            [],
        ),
    ],
    ids=[
        'offer_cost_injected_9999',
        'candidate_lu_ph_001_cost_differs',
        'candidate_lu_ph_002_cost_differs',
        'candidate_lu_ph_003_cost_differs',
        'offer_cost_within_tolerance_passes',
    ],
)
def test_reference_rule(mutator, expected_findings):
    arts = _valid_artifacts()
    mutator(arts)
    assert qa.reference(arts, REF_FACTS) == expected_findings
    assert qa.run(arts, REF_FACTS)['findings'] == expected_findings


@pytest.mark.parametrize(
    ('mutator', 'expected_findings'),
    [
        (
            lambda a: (
                a['offer'].update({'margin_per_unit_php': 200.0}),
                a['finance'].update({
                    'margin_per_unit_php': 200.0,
                    'contribution_before_ads_php': 2600.0,
                    'contribution_after_ads_php': -1400.0,
                }),
            ),
            [
                {
                    'rule': 'arithmetic',
                    'severity': 'FAIL',
                    'task_key': 'offer',
                    'detail': 'margin_per_unit_php 200.0 != 226.0',
                }
            ],
        ),
        (
            lambda a: a['offer'].update({'breakeven_orders': 25}),
            [
                {
                    'rule': 'arithmetic',
                    'severity': 'FAIL',
                    'task_key': 'offer',
                    'detail': 'breakeven_orders 25 != 18',
                }
            ],
        ),
        (
            lambda a: (
                a['offer'].update({
                    'selling_price_php': 250.0,
                    'margin_per_unit_php': -23.0,
                    'breakeven_orders': 0,
                }),
                a['kpi'].update({
                    'selling_price_php': 250.0,
                    'net_revenue_php': 3250.0,
                    'roas': 0.81,
                }),
                a['finance'].update({
                    'margin_per_unit_php': -23.0,
                    'contribution_before_ads_php': -299.0,
                    'contribution_after_ads_php': -4299.0,
                }),
            ),
            [],
        ),
        (
            lambda a: (
                a['offer'].update({
                    'selling_price_php': 273.0,
                    'margin_per_unit_php': 0.0,
                    'breakeven_orders': 0,
                }),
                a['kpi'].update({
                    'selling_price_php': 273.0,
                    'net_revenue_php': 3549.0,
                    'roas': 0.89,
                }),
                a['finance'].update({
                    'margin_per_unit_php': 0.0,
                    'contribution_before_ads_php': 0.0,
                    'contribution_after_ads_php': -4000.0,
                }),
            ),
            [],
        ),
        (
            lambda a: (
                a['offer'].update({
                    'selling_price_php': 250.0,
                    'margin_per_unit_php': -23.0,
                    'breakeven_orders': 10,
                }),
                a['kpi'].update({
                    'selling_price_php': 250.0,
                    'net_revenue_php': 3250.0,
                    'roas': 0.81,
                }),
                a['finance'].update({
                    'margin_per_unit_php': -23.0,
                    'contribution_before_ads_php': -299.0,
                    'contribution_after_ads_php': -4299.0,
                }),
            ),
            [
                {
                    'rule': 'arithmetic',
                    'severity': 'FAIL',
                    'task_key': 'offer',
                    'detail': 'breakeven_orders 10 != 0',
                }
            ],
        ),
        (
            lambda a: a['kpi'].update({'net_revenue_php': 6000.0, 'roas': 1.5}),
            [
                {
                    'rule': 'arithmetic',
                    'severity': 'FAIL',
                    'task_key': 'kpi',
                    'detail': 'net_revenue_php 6000.0 != 6487.0',
                }
            ],
        ),
        (
            lambda a: a['kpi'].update({'roas': 2.05}),
            [
                {
                    'rule': 'arithmetic',
                    'severity': 'FAIL',
                    'task_key': 'kpi',
                    'detail': 'roas 2.05 != 1.62',
                }
            ],
        ),
        (
            lambda a: a['finance'].update({
                'contribution_before_ads_php': 3000.0,
                'contribution_after_ads_php': -1000.0,
            }),
            [
                {
                    'rule': 'arithmetic',
                    'severity': 'FAIL',
                    'task_key': 'finance',
                    'detail': 'contribution_before_ads_php 3000.0 != 2938.0',
                }
            ],
        ),
        (
            lambda a: a['finance'].update({'contribution_after_ads_php': -500.0}),
            [
                {
                    'rule': 'arithmetic',
                    'severity': 'FAIL',
                    'task_key': 'finance',
                    'detail': 'contribution_after_ads_php != before - ad_spend',
                }
            ],
        ),
        (
            lambda a: a['leads'].update({'unconfirmed': 75}),
            [
                {
                    'rule': 'arithmetic',
                    'severity': 'FAIL',
                    'task_key': 'leads',
                    'detail': 'unconfirmed != leads - confirmed',
                }
            ],
        ),
        (
            lambda a: (
                a['offer'].update({'margin_per_unit_php': 226.01}),
                a['kpi'].update({'net_revenue_php': 6487.01, 'roas': 1.63}),
                a['finance'].update({
                    'margin_per_unit_php': 226.01,
                    'contribution_before_ads_php': 2938.13,
                    'contribution_after_ads_php': -1061.88,
                }),
            ),
            [],
        ),
        (
            lambda a: (
                a['offer'].update({'margin_per_unit_php': 225.99}),
                a['kpi'].update({'net_revenue_php': 6486.99, 'roas': 1.61}),
                a['finance'].update({
                    'margin_per_unit_php': 225.99,
                    'contribution_before_ads_php': 2937.87,
                    'contribution_after_ads_php': -1062.12,
                }),
            ),
            [],
        ),
    ],
    ids=[
        'wrong_margin',
        'wrong_breakeven',
        'breakeven_zero_when_margin_negative_passes',
        'breakeven_zero_when_margin_zero_passes',
        'breakeven_nonzero_when_margin_negative_fails',
        'wrong_net_revenue',
        'wrong_roas',
        'wrong_contribution_before_ads',
        'wrong_contribution_after_ads',
        'unconfirmed_mismatch',
        'plus_0_01_tolerance_passes',
        'minus_0_01_tolerance_passes',
    ],
)
def test_arithmetic_rule(mutator, expected_findings):
    arts = _valid_artifacts()
    mutator(arts)
    assert qa.arithmetic(arts) == expected_findings
    assert qa.run(arts, REF_FACTS)['findings'] == expected_findings


@pytest.mark.parametrize(
    'task_key',
    ['offer', 'content', 'campaign', 'leads', 'care', 'kpi', 'finance'],
    ids=[
        'sku_mismatch_offer',
        'sku_mismatch_content',
        'sku_mismatch_campaign',
        'sku_mismatch_leads',
        'sku_mismatch_care',
        'sku_mismatch_kpi',
        'sku_mismatch_finance',
    ],
)
def test_consistency_sku_mismatch_per_task(task_key):
    arts = _valid_artifacts()
    arts[task_key]['sku'] = 'LU-PH-002'
    if task_key == 'offer':
        arts['offer']['unit_cost_php'] = 260.0
        arts['offer']['selling_price_php'] = 579.0
    expected = [
        {
            'rule': 'consistency',
            'severity': 'FAIL',
            'task_key': task_key,
            'detail': 'sku LU-PH-002 != selected LU-PH-001',
        }
    ]
    assert qa.consistency(arts) == expected
    assert qa.run(arts, REF_FACTS)['findings'] == expected


@pytest.mark.parametrize(
    ('mutator', 'expected_findings'),
    [
        (
            lambda a: (
                a['campaign'].update({'budget_php': 5000.0}),
                a['kpi'].update({'ad_spend_php': 5000.0, 'roas': 1.3}),
                a['finance'].update({'contribution_after_ads_php': -2062.0}),
            ),
            [
                {
                    'rule': 'consistency',
                    'severity': 'FAIL',
                    'task_key': 'campaign',
                    'detail': 'budget_php != offer.campaign_budget_php',
                }
            ],
        ),
        (
            lambda a: (
                a['kpi'].update({'ad_spend_php': 3000.0, 'roas': 2.16}),
                a['finance'].update({'contribution_after_ads_php': -62.0}),
            ),
            [
                {
                    'rule': 'consistency',
                    'severity': 'FAIL',
                    'task_key': 'kpi',
                    'detail': 'ad_spend_php != campaign.budget_php',
                }
            ],
        ),
        (
            lambda a: a['finance'].update({
                'margin_per_unit_php': 200.0,
                'contribution_before_ads_php': 2600.0,
                'contribution_after_ads_php': -1400.0,
            }),
            [
                {
                    'rule': 'consistency',
                    'severity': 'FAIL',
                    'task_key': 'finance',
                    'detail': 'margin_per_unit_php != offer.margin_per_unit_php',
                }
            ],
        ),
        (
            lambda a: a['campaign'].update({'status': 'ACTIVE'}),
            [
                {
                    'rule': 'consistency',
                    'severity': 'FAIL',
                    'task_key': 'campaign',
                    'detail': 'campaign status ACTIVE is not DRAFT',
                }
            ],
        ),
    ],
    ids=[
        'budget_mismatch_between_campaign_and_offer',
        'spend_mismatch_between_kpi_and_campaign',
        'margin_mismatch_between_finance_and_offer',
        'campaign_status_not_draft',
    ],
)
def test_consistency_other_rules(mutator, expected_findings):
    arts = _valid_artifacts()
    mutator(arts)
    assert qa.consistency(arts) == expected_findings
    assert qa.run(arts, REF_FACTS)['findings'] == expected_findings


@pytest.mark.parametrize(
    ('task_key', 'narrative_text', 'expected_findings', 'expected_status'),
    [
        (
            'offer',
            'Projected bonus of 7777 PHP for this campaign.',
            [
                {
                    'rule': 'narrative',
                    'severity': 'WARN',
                    'task_key': 'offer',
                    'detail': 'number 7777 in narrative not found in artifact',
                }
            ],
            'WARN',
        ),
        (
            'offer',
            'Price is 499 PHP with unit margin 226 PHP and 18 breakeven orders on 4000 PHP budget.',
            [],
            'PASS',
        ),
        (
            'offer',
            'Biên lợi nhuận đạt 45,29% ở mức giá 499 PHP.',
            [],
            'PASS',
        ),
        (
            'finance',
            'Contribution before ads is 2938 PHP and after ads is -1062 PHP across 13 net units.',
            [],
            'PASS',
        ),
    ],
    ids=[
        'unmatched_number_in_narrative_warns',
        'matching_numbers_in_narrative_pass',
        'comma_decimal_45_29_matches_45_dot_29',
        'negative_number_in_narrative_matches',
    ],
)
def test_narrative_rule(task_key, narrative_text, expected_findings, expected_status):
    arts = _valid_artifacts()
    arts[task_key]['narrative'] = narrative_text
    assert qa.narrative(arts) == expected_findings
    res = qa.run(arts, REF_FACTS)
    assert res['findings'] == expected_findings
    assert res['status'] == expected_status


@pytest.mark.parametrize(
    ('findings', 'expected'),
    [
        ([], 'PASS'),
        (
            [{'rule': 'narrative', 'severity': 'WARN', 'task_key': 'offer', 'detail': 'warn only'}],
            'WARN',
        ),
        (
            [{'rule': 'schema', 'severity': 'FAIL', 'task_key': 'offer', 'detail': 'missing artifact'}],
            'FAIL',
        ),
        (
            [
                {'rule': 'narrative', 'severity': 'WARN', 'task_key': 'offer', 'detail': 'warn'},
                {'rule': 'arithmetic', 'severity': 'FAIL', 'task_key': 'offer', 'detail': 'fail'},
            ],
            'FAIL',
        ),
    ],
    ids=[
        'empty_findings_is_pass',
        'warn_only_is_warn',
        'fail_only_is_fail',
        'fail_beats_warn',
    ],
)
def test_status_aggregation(findings, expected):
    assert qa.status(findings) == expected
