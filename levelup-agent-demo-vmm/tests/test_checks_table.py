import copy
import pytest

from app.agents import checks

BASE_SUPPLIERS = [
    {
        'sku': 'LU-PH-001',
        'supplier': 'Mock Supplier A',
        'unit_cost_php': 180,
        'lead_time_days': 7,
        'synthetic': True,
    },
    {
        'sku': 'LU-PH-002',
        'supplier': 'Mock Supplier B',
        'unit_cost_php': 260,
        'lead_time_days': 10,
        'synthetic': True,
    },
    {
        'sku': 'LU-PH-003',
        'supplier': 'Mock Supplier C',
        'unit_cost_php': 95,
        'lead_time_days': 5,
        'synthetic': True,
    },
]


def _facts(skus=('LU-PH-001', 'LU-PH-002', 'LU-PH-003'), **cost_overrides):
    items = [copy.deepcopy(item) for item in BASE_SUPPLIERS if item['sku'] in skus]
    for item in items:
        if item['sku'] in cost_overrides:
            item['unit_cost_php'] = cost_overrides[item['sku']]
    return {'suppliers': {'items': items, 'synthetic': True}}


def _artifact(tools=None):
    base = {'agent': 'campaign', 'status': 'DRAFT'}
    if tools is not None:
        base['requested_actions'] = [{'tool': t} for t in tools]
    return copy.deepcopy(base)


@pytest.mark.parametrize(
    ('attr', 'expected'),
    [
        (
            'CHECKS',
            {
                'verify_supplier_cost': {'level': 'facts', 'learnable': True},
                'drop_blocked_action': {'level': 'artifact', 'learnable': False},
            },
        ),
        (
            'FIX',
            {
                'reference': 'verify_supplier_cost',
                'blocked_action': 'drop_blocked_action',
            },
        ),
    ],
    ids=['checks_dict_exact', 'fix_dict_exact'],
)
def test_constants(attr, expected):
    assert getattr(checks, attr) == expected


@pytest.mark.parametrize(
    ('check', 'expected'),
    [
        ('verify_supplier_cost:LU-PH-001', 'facts'),
        ('verify_supplier_cost', 'facts'),
        ('drop_blocked_action:meta_ads.publish', 'artifact'),
        ('drop_blocked_action', 'artifact'),
        ('unknown_check:LU-PH-001', None),
    ],
    ids=[
        'verify_supplier_cost_with_sku',
        'verify_supplier_cost_name_only',
        'drop_blocked_action_with_tool',
        'drop_blocked_action_name_only',
        'unknown_check_returns_none',
    ],
)
def test_level(check, expected):
    assert checks.level(check) == expected


@pytest.mark.parametrize(
    ('facts', 'check_list', 'ref_facts', 'expected_facts', 'expected_applied'),
    [
        (
            _facts(**{'LU-PH-001': 9999}),
            ['verify_supplier_cost:LU-PH-001'],
            _facts(),
            _facts(),
            [
                {
                    'check': 'verify_supplier_cost:LU-PH-001',
                    'field': 'suppliers[LU-PH-001].unit_cost_php',
                    'before': 9999,
                    'after': 180,
                    'source': 'fixture',
                }
            ],
        ),
        (
            _facts(),
            ['verify_supplier_cost:LU-PH-001'],
            _facts(),
            _facts(),
            [],
        ),
        (
            _facts(**{'LU-PH-001': 9999}),
            ['verify_supplier_cost:UNKNOWN'],
            _facts(),
            _facts(**{'LU-PH-001': 9999}),
            [],
        ),
        (
            _facts(skus=('LU-PH-001', 'LU-PH-002'), **{'LU-PH-001': 9999}),
            ['verify_supplier_cost:LU-PH-003'],
            _facts(),
            _facts(skus=('LU-PH-001', 'LU-PH-002'), **{'LU-PH-001': 9999}),
            [],
        ),
        (
            _facts(**{'LU-PH-001': 9999}),
            ['drop_blocked_action:meta_ads.publish'],
            _facts(),
            _facts(**{'LU-PH-001': 9999}),
            [],
        ),
        (
            _facts(**{'LU-PH-001': 9999, 'LU-PH-002': 8888}),
            ['verify_supplier_cost:LU-PH-001', 'verify_supplier_cost:LU-PH-002'],
            _facts(),
            _facts(),
            [
                {
                    'check': 'verify_supplier_cost:LU-PH-001',
                    'field': 'suppliers[LU-PH-001].unit_cost_php',
                    'before': 9999,
                    'after': 180,
                    'source': 'fixture',
                },
                {
                    'check': 'verify_supplier_cost:LU-PH-002',
                    'field': 'suppliers[LU-PH-002].unit_cost_php',
                    'before': 8888,
                    'after': 260,
                    'source': 'fixture',
                },
            ],
        ),
        (
            _facts(**{'LU-PH-003': 500}),
            ['verify_supplier_cost:LU-PH-003'],
            _facts(**{'LU-PH-003': 110}),
            _facts(**{'LU-PH-003': 110}),
            [
                {
                    'check': 'verify_supplier_cost:LU-PH-003',
                    'field': 'suppliers[LU-PH-003].unit_cost_php',
                    'before': 500,
                    'after': 110,
                    'source': 'fixture',
                }
            ],
        ),
    ],
    ids=[
        'replaces_9999_with_180_for_lu_ph_001',
        'already_equal_no_change',
        'unknown_sku_no_change',
        'sku_missing_in_facts_no_change',
        'artifact_level_check_ignored',
        'two_checks_for_two_skus',
        'custom_ref_facts_cost_applied',
    ],
)
def test_apply_facts(facts, check_list, ref_facts, expected_facts, expected_applied):
    facts_snapshot = copy.deepcopy(facts)
    ref_snapshot = copy.deepcopy(ref_facts)
    out, applied = checks.apply_facts(facts, check_list, ref_facts)
    assert out == expected_facts
    assert applied == expected_applied
    assert facts == facts_snapshot
    assert ref_facts == ref_snapshot
    assert out is not facts


@pytest.mark.parametrize(
    ('art', 'check_list', 'expected_art', 'expected_applied'),
    [
        (
            _artifact(['meta_ads.create_draft', 'meta_ads.publish']),
            ['drop_blocked_action:meta_ads.publish'],
            _artifact(['meta_ads.create_draft']),
            [
                {
                    'check': 'drop_blocked_action:meta_ads.publish',
                    'field': 'requested_actions',
                    'before': ['meta_ads.create_draft', 'meta_ads.publish'],
                    'after': ['meta_ads.create_draft'],
                    'source': 'rework',
                }
            ],
        ),
        (
            _artifact(['meta_ads.create_draft', 'meta_ads.publish', 'crm.reply_draft']),
            ['drop_blocked_action:meta_ads.publish'],
            _artifact(['meta_ads.create_draft', 'crm.reply_draft']),
            [
                {
                    'check': 'drop_blocked_action:meta_ads.publish',
                    'field': 'requested_actions',
                    'before': ['meta_ads.create_draft', 'meta_ads.publish', 'crm.reply_draft'],
                    'after': ['meta_ads.create_draft', 'crm.reply_draft'],
                    'source': 'rework',
                }
            ],
        ),
        (
            _artifact(['meta_ads.create_draft', 'crm.reply_draft']),
            ['drop_blocked_action:meta_ads.publish'],
            _artifact(['meta_ads.create_draft', 'crm.reply_draft']),
            [],
        ),
        (
            _artifact(['meta_ads.create_draft', 'meta_ads.publish']),
            ['verify_supplier_cost:LU-PH-001'],
            _artifact(['meta_ads.create_draft', 'meta_ads.publish']),
            [],
        ),
        (
            _artifact(None),
            ['drop_blocked_action:meta_ads.publish'],
            _artifact(None),
            [],
        ),
        (
            _artifact([]),
            ['drop_blocked_action:meta_ads.publish'],
            _artifact([]),
            [],
        ),
    ],
    ids=[
        'drop_publish_keeps_create_draft',
        'drop_publish_keeps_create_and_reply_drafts',
        'tool_not_present_applied_empty',
        'facts_level_check_ignored',
        'no_requested_actions_key_unchanged',
        'empty_requested_actions_unchanged',
    ],
)
def test_apply_artifact(art, check_list, expected_art, expected_applied):
    art_snapshot = copy.deepcopy(art)
    out, applied = checks.apply_artifact(art, check_list)
    assert out == expected_art
    assert applied == expected_applied
    assert art == art_snapshot
    assert out is not art
