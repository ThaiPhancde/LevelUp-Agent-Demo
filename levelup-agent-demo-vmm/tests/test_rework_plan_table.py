import copy
import pytest

from app.core import graph as g

ALL_TASKS = (
    'plan', 'market', 'product', 'offer', 'content', 'campaign',
    'leads', 'care', 'kpi', 'finance', 'qa', 'audit', 'monitor', 'summary',
)

FIXABLE = {
    'reference': 'verify_supplier_cost',
    'blocked_action': 'drop_blocked_action',
}

REF_PRODUCT_001 = {
    'rule': 'reference',
    'severity': 'FAIL',
    'task_key': 'product',
    'detail': 'LU-PH-001 unit_cost_php 9999 != reference 180',
}
REF_OFFER_001 = {
    'rule': 'reference',
    'severity': 'FAIL',
    'task_key': 'offer',
    'detail': 'LU-PH-001 unit_cost_php 9999 != reference 180',
}
REF_OFFER_002 = {
    'rule': 'reference',
    'severity': 'FAIL',
    'task_key': 'offer',
    'detail': 'LU-PH-002 unit_cost_php 9999 != reference 210',
}
REF_FINANCE_003 = {
    'rule': 'reference',
    'severity': 'FAIL',
    'task_key': 'finance',
    'detail': 'LU-PH-003 unit_cost_php 9999 != reference 250',
}
BLOCKED_CAMPAIGN_PUBLISH = {
    'rule': 'blocked_action',
    'severity': 'FAIL',
    'task_key': 'campaign',
    'detail': 'meta_ads.publish by agent 06 was blocked',
}
BLOCKED_CARE_REPLY = {
    'rule': 'blocked_action',
    'severity': 'FAIL',
    'task_key': 'care',
    'detail': 'crm.reply_draft by agent 08 was blocked',
}


def _decision_statuses(**overrides):
    base = {k: 'COMPLETED' for k in ALL_TASKS}
    base['monitor'] = 'PENDING'
    base['summary'] = 'PENDING'
    base.update(overrides)
    return copy.deepcopy(base)


def _changes_for(*tasks):
    return {t: ('COMPLETED', 'PENDING') for t in tasks}


@pytest.mark.parametrize(
    ('task', 'src', 'dst', 'expected'),
    [
        ('market', 'COMPLETED', 'PENDING', True),
        ('product', 'COMPLETED', 'PENDING', True),
        ('offer', 'COMPLETED', 'PENDING', True),
        ('content', 'COMPLETED', 'PENDING', True),
        ('campaign', 'COMPLETED', 'PENDING', True),
        ('leads', 'COMPLETED', 'PENDING', True),
        ('care', 'COMPLETED', 'PENDING', True),
        ('kpi', 'COMPLETED', 'PENDING', True),
        ('finance', 'COMPLETED', 'PENDING', True),
        ('plan', 'COMPLETED', 'PENDING', False),
        ('qa', 'COMPLETED', 'PENDING', False),
        ('audit', 'COMPLETED', 'PENDING', False),
        ('monitor', 'COMPLETED', 'PENDING', False),
        ('summary', 'COMPLETED', 'PENDING', False),
        ('product', 'FAILED', 'PENDING', False),
        ('product', 'SKIPPED', 'PENDING', False),
        ('product', 'RUNNING', 'PENDING', False),
        ('product', 'PENDING', 'PENDING', False),
        ('product', 'CANCELLED', 'PENDING', False),
        ('product', 'COMPLETED', 'RUNNING', False),
        ('product', 'COMPLETED', 'COMPLETED', False),
        ('product', 'COMPLETED', 'FAILED', False),
        ('product', 'COMPLETED', 'SKIPPED', False),
        ('product', 'COMPLETED', 'CANCELLED', False),
    ],
    ids=[
        'business_market_completed_to_pending',
        'business_product_completed_to_pending',
        'business_offer_completed_to_pending',
        'business_content_completed_to_pending',
        'business_campaign_completed_to_pending',
        'business_leads_completed_to_pending',
        'business_care_completed_to_pending',
        'business_kpi_completed_to_pending',
        'business_finance_completed_to_pending',
        'plan_refused',
        'soft_qa_refused',
        'soft_audit_refused',
        'soft_monitor_refused',
        'soft_summary_refused',
        'failed_to_pending_refused',
        'skipped_to_pending_refused',
        'running_to_pending_refused',
        'pending_to_pending_refused',
        'cancelled_to_pending_refused',
        'completed_to_running_refused',
        'completed_to_completed_refused',
        'completed_to_failed_refused',
        'completed_to_skipped_refused',
        'completed_to_cancelled_refused',
    ],
)
def test_can_rework(task, src, dst, expected):
    assert g.can_rework(task, src, dst) is expected


@pytest.mark.parametrize(
    ('findings', 'statuses', 'rounds_used', 'max_rework', 'fixable', 'expected_reason'),
    [
        (
            [REF_PRODUCT_001],
            _decision_statuses(campaign='FAILED'),
            0,
            2,
            FIXABLE,
            'business_task_not_completed',
        ),
        (
            [REF_PRODUCT_001],
            _decision_statuses(leads='SKIPPED'),
            0,
            2,
            FIXABLE,
            'business_task_not_completed',
        ),
        (
            [],
            _decision_statuses(product='FAILED'),
            2,
            0,
            FIXABLE,
            'business_task_not_completed',
        ),
        (
            [],
            _decision_statuses(),
            0,
            2,
            FIXABLE,
            'no_fail',
        ),
        (
            [
                {
                    'rule': 'reference',
                    'severity': 'WARN',
                    'task_key': 'product',
                    'detail': 'LU-PH-001 unit_cost_php 9999 != reference 180',
                },
                {
                    'rule': 'blocked_action',
                    'severity': 'WARN',
                    'task_key': 'campaign',
                    'detail': 'meta_ads.publish by agent 06 was blocked',
                },
            ],
            _decision_statuses(),
            1,
            1,
            FIXABLE,
            'no_fail',
        ),
        (
            [
                {
                    'rule': 'schema',
                    'severity': 'FAIL',
                    'task_key': 'product',
                    'detail': 'LU-PH-001 missing required key',
                },
                {
                    'rule': 'arithmetic',
                    'severity': 'FAIL',
                    'task_key': 'finance',
                    'detail': 'LU-PH-001 margin mismatch',
                },
                {
                    'rule': 'not_via_gateway',
                    'severity': 'FAIL',
                    'task_key': 'campaign',
                    'detail': 'meta_ads.create_draft bypassed gateway',
                },
            ],
            _decision_statuses(),
            0,
            2,
            FIXABLE,
            'no_fixable_rule',
        ),
        (
            [
                {
                    'rule': 'reference',
                    'severity': 'FAIL',
                    'task_key': 'plan',
                    'detail': 'LU-PH-001 unit_cost_php 9999 != reference 180',
                },
                {
                    'rule': 'blocked_action',
                    'severity': 'FAIL',
                    'task_key': 'qa',
                    'detail': 'meta_ads.publish by agent 06 was blocked',
                },
            ],
            _decision_statuses(),
            0,
            2,
            FIXABLE,
            'no_fixable_rule',
        ),
        (
            [REF_PRODUCT_001],
            _decision_statuses(),
            1,
            1,
            {},
            'no_fixable_rule',
        ),
        (
            [REF_PRODUCT_001],
            _decision_statuses(),
            1,
            1,
            FIXABLE,
            'exhausted',
        ),
        (
            [REF_PRODUCT_001],
            _decision_statuses(),
            2,
            1,
            FIXABLE,
            'exhausted',
        ),
        (
            [REF_PRODUCT_001],
            _decision_statuses(),
            0,
            0,
            FIXABLE,
            'exhausted',
        ),
    ],
    ids=[
        'failed_business_task_wins_over_fixable_fail',
        'skipped_business_task_wins_over_fixable_fail',
        'failed_business_task_wins_over_no_fail_and_exhausted',
        'empty_findings_returns_no_fail',
        'only_warn_findings_returns_no_fail_before_exhausted',
        'only_unfixable_rules_schema_arithmetic_not_via_gateway',
        'fixable_rule_on_non_business_task_plan_or_qa',
        'empty_fixable_map_returns_no_fixable_rule_before_exhausted',
        'rounds_used_equals_max_rework_exhausted',
        'rounds_used_exceeds_max_rework_exhausted',
        'max_rework_zero_exhausted',
    ],
)
def test_rework_plan_none(findings, statuses, rounds_used, max_rework, fixable, expected_reason):
    findings_in = copy.deepcopy(findings)
    statuses_in = copy.deepcopy(statuses)
    fixable_in = copy.deepcopy(fixable)
    plan, reason = g.rework_plan(
        findings_in,
        statuses_in,
        rounds_used,
        g.GRAPH,
        soft=g.SOFT,
        max_rework=max_rework,
        fixable=fixable_in,
    )
    assert plan is None
    assert reason == expected_reason
    assert findings_in == findings
    assert statuses_in == statuses


@pytest.mark.parametrize(
    ('findings', 'statuses', 'rounds_used', 'max_rework', 'expected_plan'),
    [
        (
            [REF_PRODUCT_001, REF_OFFER_001],
            _decision_statuses(),
            0,
            1,
            {
                'target': 'product',
                'findings': [REF_PRODUCT_001, REF_OFFER_001],
                'feedback': [REF_PRODUCT_001],
                'checks': ['verify_supplier_cost:LU-PH-001'],
                'changes': _changes_for(
                    'product', 'offer', 'content', 'campaign',
                    'leads', 'care', 'kpi', 'finance', 'qa', 'audit',
                ),
                'reason': 'reference tại product',
            },
        ),
        (
            [BLOCKED_CAMPAIGN_PUBLISH],
            _decision_statuses(),
            0,
            1,
            {
                'target': 'campaign',
                'findings': [BLOCKED_CAMPAIGN_PUBLISH],
                'feedback': [BLOCKED_CAMPAIGN_PUBLISH],
                'checks': ['drop_blocked_action:meta_ads.publish'],
                'changes': _changes_for(
                    'campaign', 'leads', 'care', 'kpi', 'finance', 'qa', 'audit',
                ),
                'reason': 'blocked_action tại campaign',
            },
        ),
        (
            [BLOCKED_CAMPAIGN_PUBLISH, REF_PRODUCT_001],
            _decision_statuses(),
            0,
            2,
            {
                'target': 'product',
                'findings': [BLOCKED_CAMPAIGN_PUBLISH, REF_PRODUCT_001],
                'feedback': [REF_PRODUCT_001],
                'checks': [
                    'drop_blocked_action:meta_ads.publish',
                    'verify_supplier_cost:LU-PH-001',
                ],
                'changes': _changes_for(
                    'product', 'offer', 'content', 'campaign',
                    'leads', 'care', 'kpi', 'finance', 'qa', 'audit',
                ),
                'reason': 'reference tại product',
            },
        ),
        (
            [
                {
                    'rule': 'reference',
                    'severity': 'WARN',
                    'task_key': 'market',
                    'detail': 'LU-PH-001 unit_cost_php 9999 != reference 180',
                },
                {
                    'rule': 'schema',
                    'severity': 'FAIL',
                    'task_key': 'market',
                    'detail': 'LU-PH-001 schema drift',
                },
                REF_PRODUCT_001,
            ],
            _decision_statuses(),
            0,
            1,
            {
                'target': 'product',
                'findings': [REF_PRODUCT_001],
                'feedback': [REF_PRODUCT_001],
                'checks': ['verify_supplier_cost:LU-PH-001'],
                'changes': _changes_for(
                    'product', 'offer', 'content', 'campaign',
                    'leads', 'care', 'kpi', 'finance', 'qa', 'audit',
                ),
                'reason': 'reference tại product',
            },
        ),
        (
            [REF_PRODUCT_001, REF_OFFER_002],
            _decision_statuses(),
            1,
            g.MAX_REWORK_CEILING,
            {
                'target': 'product',
                'findings': [REF_PRODUCT_001, REF_OFFER_002],
                'feedback': [REF_PRODUCT_001],
                'checks': [
                    'verify_supplier_cost:LU-PH-001',
                    'verify_supplier_cost:LU-PH-002',
                ],
                'changes': _changes_for(
                    'product', 'offer', 'content', 'campaign',
                    'leads', 'care', 'kpi', 'finance', 'qa', 'audit',
                ),
                'reason': 'reference tại product',
            },
        ),
        (
            [BLOCKED_CARE_REPLY],
            _decision_statuses(),
            0,
            1,
            {
                'target': 'care',
                'findings': [BLOCKED_CARE_REPLY],
                'feedback': [BLOCKED_CARE_REPLY],
                'checks': ['drop_blocked_action:crm.reply_draft'],
                'changes': _changes_for('care', 'kpi', 'finance', 'qa', 'audit'),
                'reason': 'blocked_action tại care',
            },
        ),
        (
            [REF_FINANCE_003],
            _decision_statuses(),
            0,
            1,
            {
                'target': 'finance',
                'findings': [REF_FINANCE_003],
                'feedback': [REF_FINANCE_003],
                'checks': ['verify_supplier_cost:LU-PH-003'],
                'changes': _changes_for('finance', 'qa', 'audit'),
                'reason': 'reference tại finance',
            },
        ),
        (
            [BLOCKED_CAMPAIGN_PUBLISH],
            _decision_statuses(audit='PENDING', monitor='PENDING', summary='PENDING'),
            0,
            1,
            {
                'target': 'campaign',
                'findings': [BLOCKED_CAMPAIGN_PUBLISH],
                'feedback': [BLOCKED_CAMPAIGN_PUBLISH],
                'checks': ['drop_blocked_action:meta_ads.publish'],
                'changes': _changes_for('campaign', 'leads', 'care', 'kpi', 'finance', 'qa'),
                'reason': 'blocked_action tại campaign',
            },
        ),
    ],
    ids=[
        'reference_on_product_and_offer_deduplicates_check_and_targets_product',
        'blocked_action_on_campaign_resets_campaign_through_audit',
        'both_reference_and_blocked_action_picks_earliest_and_sorts_checks',
        'warn_with_fixable_rule_and_unfixable_fail_are_ignored',
        'retry_and_second_rework_round_statuses_only_multiple_skus',
        'blocked_action_on_care_resets_only_downstream',
        'reference_on_finance_resets_finance_qa_audit',
        'pending_descendants_excluded_from_changes',
    ],
)
def test_rework_plan_planned(findings, statuses, rounds_used, max_rework, expected_plan):
    findings_in = copy.deepcopy(findings)
    statuses_in = copy.deepcopy(statuses)
    plan, status = g.rework_plan(
        findings_in,
        statuses_in,
        rounds_used,
        g.GRAPH,
        soft=g.SOFT,
        max_rework=max_rework,
        fixable=copy.deepcopy(FIXABLE),
    )
    assert status == 'planned'
    assert plan == expected_plan
    assert all(val == ('COMPLETED', 'PENDING') for val in plan['changes'].values())
    assert 'monitor' not in plan['changes']
    assert 'summary' not in plan['changes']


@pytest.mark.parametrize(
    ('key', 'attempt', 'rework', 'expected', 'must_contain'),
    [
        (
            'product',
            2,
            'reference tại product',
            'Làm lại theo yêu cầu của Commander (lần thử #2): reference tại product.',
            ('reference tại product', '#2'),
        ),
        (
            'campaign',
            3,
            'blocked_action tại campaign',
            'Làm lại theo yêu cầu của Commander (lần thử #3): blocked_action tại campaign.',
            ('blocked_action tại campaign', '#3'),
        ),
        (
            'product',
            1,
            'reference tại product',
            'Làm lại theo yêu cầu của Commander (lần thử #1): reference tại product.',
            ('reference tại product', '#1'),
        ),
        (
            'product',
            2,
            None,
            'Làm lại lần thử #2 sau khi được retry.',
            ('#2', 'retry'),
        ),
        (
            'product',
            1,
            None,
            'Mọi phụ thuộc đã hoàn tất: market.',
            ('market',),
        ),
    ],
    ids=[
        'rework_reference_at_product_attempt_2',
        'rework_blocked_action_at_campaign_attempt_3',
        'rework_overrides_attempt_1',
        'retry_without_rework_attempt_2',
        'first_attempt_without_rework',
    ],
)
def test_dispatch_reason_rework(key, attempt, rework, expected, must_contain):
    text = g.dispatch_reason(key, g.GRAPH, soft=g.SOFT, attempt=attempt, rework=rework)
    assert text == expected
    assert all(part in text for part in must_contain)
