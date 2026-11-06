import copy
import pytest

from app.engines import audit, monitor


BASE_ARTS = {
    'campaign': {
        'type': 'campaign_plan',
        'agent_id': '06',
        'summary': 'Chiến dịch CMP-LU-PH-001 ở trạng thái DRAFT, ngân sách 4000 PHP.',
        'synthetic': True,
        'sku': 'LU-PH-001',
        'campaign_id': 'CMP-LU-PH-001',
        'status': 'DRAFT',
        'budget_php': 4000.0,
        'budget_share_pct': 26.67,
        'ad_draft_count': 3,
        'requested_actions': [
            {'tool': 'meta_ads.create_draft', 'target': 'CMP-LU-PH-001'},
        ],
    },
    'leads': {
        'type': 'lead_report',
        'agent_id': '07',
        'summary': '100 lead, 20 xác nhận; 3 hội thoại lead cần trả lời nháp.',
        'synthetic': True,
        'sku': 'LU-PH-001',
        'leads': 100,
        'confirmed': 20,
        'unconfirmed': 80,
        'confirm_rate': 0.2,
        'cost_per_lead_php': 40.0,
        'cost_per_confirmed_php': 200.0,
        'open_conversations': ['CONV-001'],
        'requested_actions': [
            {'tool': 'crm.reply_draft', 'target': 'CONV-001'},
        ],
    },
    'care': {
        'type': 'care_report',
        'agent_id': '08',
        'summary': '15 đơn đã giao, 2 hoàn, 5 đang giao; 4 ticket sau bán.',
        'synthetic': True,
        'sku': 'LU-PH-001',
        'confirmed': 20,
        'delivered': 15,
        'returned': 2,
        'in_transit': 5,
        'delivery_days': 3,
        'provider': 'Mock 3PL',
        'tickets': ['CONV-008'],
        'requested_actions': [
            {'tool': 'crm.ticket_note', 'target': 'CONV-008'},
        ],
    },
}

BASE_TOOL_CALLS = [
    {
        'task_key': 'campaign',
        'agent_id': '06',
        'tool': 'meta_ads.create_draft',
        'allowed': 1,
        'detail': {'decision': 'ALLOW', 'target': 'CMP-LU-PH-001'},
    },
    {
        'task_key': 'leads',
        'agent_id': '07',
        'tool': 'crm.reply_draft',
        'allowed': 1,
        'detail': {'decision': 'ALLOW', 'target': 'CONV-001'},
    },
    {
        'task_key': 'care',
        'agent_id': '08',
        'tool': 'crm.ticket_note',
        'allowed': 1,
        'detail': {'decision': 'ALLOW', 'target': 'CONV-008'},
    },
]

ALL_TASKS = (
    'plan', 'market', 'product', 'offer', 'content', 'campaign',
    'leads', 'care', 'kpi', 'finance', 'qa', 'audit', 'monitor', 'summary',
)


def _audit_inputs():
    return copy.deepcopy(BASE_ARTS), copy.deepcopy(BASE_TOOL_CALLS)


def _evidence(task_overrides=None, llm=None, narrative_sources=None):
    tasks = [
        {'task_key': k, 'status': 'COMPLETED', 'attempt': 1, 'error': None}
        for k in ALL_TASKS
    ]
    if task_overrides:
        by_key = {t['task_key']: t for t in tasks}
        for key, patch in task_overrides.items():
            by_key[key].update(copy.deepcopy(patch))
    return {
        'tasks': tasks,
        'llm': copy.deepcopy(llm) if llm is not None else {'calls': 0, 'tokens': 0, 'errors': 0},
        'narrative_sources': copy.deepcopy(narrative_sources) if narrative_sources is not None else {},
    }


@pytest.mark.parametrize(
    ('agent_id', 'tool', 'expected'),
    [
        # Agent 02 (READ only)
        ('02', 'meta_ads.create_draft', {'decision': 'BLOCK', 'permission': 'WRITE_DRAFT', 'reason': 'agent 02 lacks WRITE_DRAFT'}),
        ('02', 'meta_ads.publish', {'decision': 'BLOCK', 'permission': 'WRITE_EXTERNAL', 'reason': 'WRITE_EXTERNAL is never granted in the demo'}),
        ('02', 'crm.reply_draft', {'decision': 'BLOCK', 'permission': 'WRITE_DRAFT', 'reason': 'agent 02 lacks WRITE_DRAFT'}),
        ('02', 'crm.ticket_note', {'decision': 'BLOCK', 'permission': 'WRITE_DRAFT', 'reason': 'agent 02 lacks WRITE_DRAFT'}),
        ('02', 'payment.charge', {'decision': 'BLOCK', 'permission': 'WRITE_EXTERNAL', 'reason': 'WRITE_EXTERNAL is never granted in the demo'}),
        ('02', 'messaging.send', {'decision': 'BLOCK', 'permission': 'WRITE_EXTERNAL', 'reason': 'WRITE_EXTERNAL is never granted in the demo'}),
        ('02', 'mock.market', {'decision': 'ALLOW', 'permission': 'READ', 'reason': 'allowed by registry'}),
        ('02', 'unknown.tool', {'decision': 'BLOCK', 'permission': 'WRITE_EXTERNAL', 'reason': 'WRITE_EXTERNAL is never granted in the demo'}),
        # Agent 06 (READ, WRITE_DRAFT)
        ('06', 'meta_ads.create_draft', {'decision': 'ALLOW', 'permission': 'WRITE_DRAFT', 'reason': 'allowed by registry'}),
        ('06', 'meta_ads.publish', {'decision': 'BLOCK', 'permission': 'WRITE_EXTERNAL', 'reason': 'WRITE_EXTERNAL is never granted in the demo'}),
        ('06', 'crm.reply_draft', {'decision': 'ALLOW', 'permission': 'WRITE_DRAFT', 'reason': 'allowed by registry'}),
        ('06', 'crm.ticket_note', {'decision': 'ALLOW', 'permission': 'WRITE_DRAFT', 'reason': 'allowed by registry'}),
        ('06', 'payment.charge', {'decision': 'BLOCK', 'permission': 'WRITE_EXTERNAL', 'reason': 'WRITE_EXTERNAL is never granted in the demo'}),
        ('06', 'messaging.send', {'decision': 'BLOCK', 'permission': 'WRITE_EXTERNAL', 'reason': 'WRITE_EXTERNAL is never granted in the demo'}),
        ('06', 'mock.market', {'decision': 'ALLOW', 'permission': 'READ', 'reason': 'allowed by registry'}),
        ('06', 'unknown.tool', {'decision': 'BLOCK', 'permission': 'WRITE_EXTERNAL', 'reason': 'WRITE_EXTERNAL is never granted in the demo'}),
        # Agent 07 (READ, WRITE_DRAFT)
        ('07', 'meta_ads.create_draft', {'decision': 'ALLOW', 'permission': 'WRITE_DRAFT', 'reason': 'allowed by registry'}),
        ('07', 'meta_ads.publish', {'decision': 'BLOCK', 'permission': 'WRITE_EXTERNAL', 'reason': 'WRITE_EXTERNAL is never granted in the demo'}),
        ('07', 'crm.reply_draft', {'decision': 'ALLOW', 'permission': 'WRITE_DRAFT', 'reason': 'allowed by registry'}),
        ('07', 'crm.ticket_note', {'decision': 'ALLOW', 'permission': 'WRITE_DRAFT', 'reason': 'allowed by registry'}),
        ('07', 'payment.charge', {'decision': 'BLOCK', 'permission': 'WRITE_EXTERNAL', 'reason': 'WRITE_EXTERNAL is never granted in the demo'}),
        ('07', 'messaging.send', {'decision': 'BLOCK', 'permission': 'WRITE_EXTERNAL', 'reason': 'WRITE_EXTERNAL is never granted in the demo'}),
        ('07', 'mock.market', {'decision': 'ALLOW', 'permission': 'READ', 'reason': 'allowed by registry'}),
        ('07', 'unknown.tool', {'decision': 'BLOCK', 'permission': 'WRITE_EXTERNAL', 'reason': 'WRITE_EXTERNAL is never granted in the demo'}),
        # Agent 08 (READ, WRITE_DRAFT)
        ('08', 'meta_ads.create_draft', {'decision': 'ALLOW', 'permission': 'WRITE_DRAFT', 'reason': 'allowed by registry'}),
        ('08', 'meta_ads.publish', {'decision': 'BLOCK', 'permission': 'WRITE_EXTERNAL', 'reason': 'WRITE_EXTERNAL is never granted in the demo'}),
        ('08', 'crm.reply_draft', {'decision': 'ALLOW', 'permission': 'WRITE_DRAFT', 'reason': 'allowed by registry'}),
        ('08', 'crm.ticket_note', {'decision': 'ALLOW', 'permission': 'WRITE_DRAFT', 'reason': 'allowed by registry'}),
        ('08', 'payment.charge', {'decision': 'BLOCK', 'permission': 'WRITE_EXTERNAL', 'reason': 'WRITE_EXTERNAL is never granted in the demo'}),
        ('08', 'messaging.send', {'decision': 'BLOCK', 'permission': 'WRITE_EXTERNAL', 'reason': 'WRITE_EXTERNAL is never granted in the demo'}),
        ('08', 'mock.market', {'decision': 'ALLOW', 'permission': 'READ', 'reason': 'allowed by registry'}),
        ('08', 'unknown.tool', {'decision': 'BLOCK', 'permission': 'WRITE_EXTERNAL', 'reason': 'WRITE_EXTERNAL is never granted in the demo'}),
        # Agent 11 (READ, SUPERVISE)
        ('11', 'meta_ads.create_draft', {'decision': 'BLOCK', 'permission': 'WRITE_DRAFT', 'reason': 'agent 11 lacks WRITE_DRAFT'}),
        ('11', 'meta_ads.publish', {'decision': 'BLOCK', 'permission': 'WRITE_EXTERNAL', 'reason': 'WRITE_EXTERNAL is never granted in the demo'}),
        ('11', 'crm.reply_draft', {'decision': 'BLOCK', 'permission': 'WRITE_DRAFT', 'reason': 'agent 11 lacks WRITE_DRAFT'}),
        ('11', 'crm.ticket_note', {'decision': 'BLOCK', 'permission': 'WRITE_DRAFT', 'reason': 'agent 11 lacks WRITE_DRAFT'}),
        ('11', 'payment.charge', {'decision': 'BLOCK', 'permission': 'WRITE_EXTERNAL', 'reason': 'WRITE_EXTERNAL is never granted in the demo'}),
        ('11', 'messaging.send', {'decision': 'BLOCK', 'permission': 'WRITE_EXTERNAL', 'reason': 'WRITE_EXTERNAL is never granted in the demo'}),
        ('11', 'mock.market', {'decision': 'ALLOW', 'permission': 'READ', 'reason': 'allowed by registry'}),
        ('11', 'unknown.tool', {'decision': 'BLOCK', 'permission': 'WRITE_EXTERNAL', 'reason': 'WRITE_EXTERNAL is never granted in the demo'}),
    ],
    ids=[
        '02_create_draft_block', '02_publish_block', '02_reply_draft_block', '02_ticket_note_block',
        '02_payment_charge_block', '02_messaging_send_block', '02_mock_market_allow', '02_unknown_tool_block',
        '06_create_draft_allow', '06_publish_block', '06_reply_draft_allow', '06_ticket_note_allow',
        '06_payment_charge_block', '06_messaging_send_block', '06_mock_market_allow', '06_unknown_tool_block',
        '07_create_draft_allow', '07_publish_block', '07_reply_draft_allow', '07_ticket_note_allow',
        '07_payment_charge_block', '07_messaging_send_block', '07_mock_market_allow', '07_unknown_tool_block',
        '08_create_draft_allow', '08_publish_block', '08_reply_draft_allow', '08_ticket_note_allow',
        '08_payment_charge_block', '08_messaging_send_block', '08_mock_market_allow', '08_unknown_tool_block',
        '11_create_draft_block', '11_publish_block', '11_reply_draft_block', '11_ticket_note_block',
        '11_payment_charge_block', '11_messaging_send_block', '11_mock_market_allow', '11_unknown_tool_block',
    ],
)
def test_check_action_matrix(monkeypatch, agent_id, tool, expected):
    monkeypatch.delenv('APPROVAL_THRESHOLD_PHP', raising=False)
    assert audit.check_action(agent_id, tool) == expected


@pytest.mark.parametrize(
    ('env_threshold', 'budget_php', 'expected'),
    [
        (
            None,
            4999,
            {'decision': 'ALLOW', 'permission': 'WRITE_DRAFT', 'reason': 'allowed by registry'},
        ),
        (
            None,
            5000,
            {
                'decision': 'NEEDS_APPROVAL',
                'permission': 'WRITE_DRAFT',
                'reason': 'budget 5000 >= approval threshold 5000 PHP',
            },
        ),
        (
            None,
            9000,
            {
                'decision': 'NEEDS_APPROVAL',
                'permission': 'WRITE_DRAFT',
                'reason': 'budget 9000 >= approval threshold 5000 PHP',
            },
        ),
        (
            '3000',
            4000,
            {
                'decision': 'NEEDS_APPROVAL',
                'permission': 'WRITE_DRAFT',
                'reason': 'budget 4000 >= approval threshold 3000 PHP',
            },
        ),
    ],
    ids=[
        'default_threshold_4999_allow',
        'default_threshold_5000_needs_approval',
        'default_threshold_9000_needs_approval',
        'custom_threshold_3000_turns_4000_into_needs_approval',
    ],
)
def test_check_action_budget_threshold(monkeypatch, env_threshold, budget_php, expected):
    if env_threshold is None:
        monkeypatch.delenv('APPROVAL_THRESHOLD_PHP', raising=False)
    else:
        monkeypatch.setenv('APPROVAL_THRESHOLD_PHP', env_threshold)
    assert audit.check_action('06', 'meta_ads.create_draft', {'budget_php': budget_php}) == expected


@pytest.mark.parametrize(
    ('mutator', 'expected_status', 'expected_findings'),
    [
        (
            'clean',
            'PASS',
            [],
        ),
        (
            'blocked_action',
            'FAIL',
            [
                {
                    'rule': 'blocked_action',
                    'severity': 'FAIL',
                    'task_key': 'campaign',
                    'detail': 'meta_ads.publish by agent 06 was blocked',
                },
            ],
        ),
        (
            'pending_approval',
            'WARN',
            [
                {
                    'rule': 'pending_approval',
                    'severity': 'WARN',
                    'task_key': 'campaign',
                    'detail': 'meta_ads.create_draft waits for human approval',
                },
            ],
        ),
        (
            'not_via_gateway',
            'FAIL',
            [
                {
                    'rule': 'not_via_gateway',
                    'severity': 'FAIL',
                    'task_key': 'leads',
                    'detail': 'crm.reply_draft CONV-002 has no gateway decision',
                },
            ],
        ),
        (
            'draft_only',
            'FAIL',
            [
                {
                    'rule': 'draft_only',
                    'severity': 'FAIL',
                    'task_key': 'campaign',
                    'detail': 'campaign status ACTIVE',
                },
            ],
        ),
    ],
    ids=[
        'clean_tool_calls_pass',
        'block_decision_fails_blocked_action',
        'needs_approval_warns_pending_approval',
        'missing_gateway_call_fails_not_via_gateway',
        'campaign_not_draft_fails_draft_only',
    ],
)
def test_audit_run(mutator, expected_status, expected_findings):
    arts, tool_calls = _audit_inputs()
    if mutator == 'blocked_action':
        tool_calls.append(
            {
                'task_key': 'campaign',
                'agent_id': '06',
                'tool': 'meta_ads.publish',
                'allowed': 0,
                'detail': {'decision': 'BLOCK', 'target': 'CMP-LU-PH-001'},
            }
        )
    elif mutator == 'pending_approval':
        tool_calls[0]['detail']['decision'] = 'NEEDS_APPROVAL'
    elif mutator == 'not_via_gateway':
        arts['leads']['requested_actions'].append({'tool': 'crm.reply_draft', 'target': 'CONV-002'})
    elif mutator == 'draft_only':
        arts['campaign']['status'] = 'ACTIVE'

    result = audit.run(arts, tool_calls)
    assert (
        result['engine'] == 'audit'
        and result['status'] == expected_status
        and result['findings'] == expected_findings
    )


@pytest.mark.parametrize(
    ('error', 'expected'),
    [
        ('timeout after 15s', 'timeout'),
        ('Timeout waiting for model', 'timeout'),
        ('Empty model response', 'empty_response'),
        ('empty narrative', 'empty_response'),
        ('Upstream schema validation failed', 'task_failed'),
        (None, 'task_failed'),
    ],
    ids=[
        'timeout_lowercase',
        'timeout_capitalized',
        'empty_model_response',
        'empty_narrative',
        'other_error_string',
        'none_error',
    ],
)
def test_monitor_classify(error, expected):
    assert monitor.classify(error) == expected


@pytest.mark.parametrize(
    ('task_overrides', 'llm', 'narrative_sources', 'expected_status', 'expected_findings'),
    [
        (
            None,
            {'calls': 2, 'tokens': 320, 'errors': 0},
            {'market': 'mock', 'offer': 'llm'},
            'PASS',
            [],
        ),
        (
            {'market': {'status': 'FAILED', 'error': 'Timeout after 10s'}},
            None,
            None,
            'FAIL',
            [
                {
                    'rule': 'timeout',
                    'severity': 'FAIL',
                    'task_key': 'market',
                    'detail': 'Timeout after 10s',
                },
            ],
        ),
        (
            {'offer': {'status': 'FAILED', 'error': 'Empty model response'}},
            None,
            None,
            'FAIL',
            [
                {
                    'rule': 'empty_response',
                    'severity': 'FAIL',
                    'task_key': 'offer',
                    'detail': 'Empty model response',
                },
            ],
        ),
        (
            {'content': {'status': 'FAILED', 'error': 'empty narrative'}},
            None,
            None,
            'FAIL',
            [
                {
                    'rule': 'empty_response',
                    'severity': 'FAIL',
                    'task_key': 'content',
                    'detail': 'empty narrative',
                },
            ],
        ),
        (
            {'kpi': {'status': 'FAILED', 'error': 'Unexpected gateway exception'}},
            None,
            None,
            'FAIL',
            [
                {
                    'rule': 'task_failed',
                    'severity': 'FAIL',
                    'task_key': 'kpi',
                    'detail': 'Unexpected gateway exception',
                },
            ],
        ),
        (
            {'finance': {'status': 'SKIPPED', 'error': 'blocked by failed kpi'}},
            None,
            None,
            'WARN',
            [
                {
                    'rule': 'skipped',
                    'severity': 'WARN',
                    'task_key': 'finance',
                    'detail': 'blocked by failed kpi',
                },
            ],
        ),
        (
            {'leads': {'status': 'COMPLETED', 'attempt': 2}},
            None,
            None,
            'WARN',
            [
                {
                    'rule': 'retried',
                    'severity': 'WARN',
                    'task_key': 'leads',
                    'detail': 'completed on attempt 2',
                },
            ],
        ),
        (
            None,
            {'calls': 3, 'tokens': 450, 'errors': 2},
            None,
            'WARN',
            [
                {
                    'rule': 'llm_errors',
                    'severity': 'WARN',
                    'task_key': None,
                    'detail': '2 failed LLM call(s)',
                },
            ],
        ),
        (
            None,
            None,
            {'market': 'llm', 'finance': 'mock_budget', 'kpi': 'mock_budget'},
            'WARN',
            [
                {
                    'rule': 'token_budget',
                    'severity': 'WARN',
                    'task_key': None,
                    'detail': 'LLM token budget reached; mock text used for finance, kpi',
                },
            ],
        ),
        (
            {
                'monitor': {'status': 'FAILED', 'attempt': 2, 'error': 'Timeout in monitor'},
                'summary': {'status': 'SKIPPED', 'attempt': 3, 'error': 'Empty model response'},
            },
            None,
            None,
            'PASS',
            [],
        ),
    ],
    ids=[
        'all_completed_pass',
        'timeout_fails_timeout_rule',
        'empty_model_response_fails_empty_response_rule',
        'empty_narrative_fails_empty_response_rule',
        'other_error_fails_task_failed_rule',
        'skipped_task_warns_skipped_rule',
        'attempt_2_completed_warns_retried_rule',
        'llm_errors_warns_llm_errors_rule',
        'mock_budget_source_warns_token_budget_rule',
        'monitor_and_summary_tasks_ignored',
    ],
)
def test_monitor_run(task_overrides, llm, narrative_sources, expected_status, expected_findings):
    ev = _evidence(task_overrides=task_overrides, llm=llm, narrative_sources=narrative_sources)
    result = monitor.run(ev)
    assert (
        result['engine'] == 'monitor'
        and result['status'] == expected_status
        and result['findings'] == expected_findings
        and result['tasks'] == ev['tasks']
        and result['llm_calls'] == ev['llm']['calls']
        and result['tokens'] == ev['llm']['tokens']
    )
