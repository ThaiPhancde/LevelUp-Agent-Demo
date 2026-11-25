import pytest

from app.core import gateway

HEX_CHARS = set('0123456789abcdef')


@pytest.mark.parametrize(
    ('left', 'right', 'should_equal'),
    [
        (
            {'tool': 'meta_ads.create_draft', 'target': 'CMP-LU-PH-001', 'budget_php': 15000},
            {'tool': 'meta_ads.create_draft', 'target': 'CMP-LU-PH-001', 'budget_php': 15000},
            True,
        ),
        (
            {'tool': 'meta_ads.create_draft', 'target': 'CMP-LU-PH-001', 'budget_php': 15000},
            {'budget_php': 15000, 'target': 'CMP-LU-PH-001', 'tool': 'meta_ads.create_draft'},
            True,
        ),
        (
            {
                'tool': 'meta_ads.create_draft',
                'target': 'CMP-LU-PH-001',
                'payload': {
                    'ad_set': 'AS-LU-01',
                    'objective': 'LEADS',
                    'targeting': {'country': 'PH', 'age_min': 25},
                },
            },
            {
                'target': 'CMP-LU-PH-001',
                'payload': {
                    'targeting': {'age_min': 25, 'country': 'PH'},
                    'objective': 'LEADS',
                    'ad_set': 'AS-LU-01',
                },
                'tool': 'meta_ads.create_draft',
            },
            True,
        ),
        (
            {
                'tool': 'meta_ads.create_draft',
                'target': 'CMP-LU-PH-001',
                'note': 'Chiến dịch quảng cáo thử nghiệm thị trường Philippines',
            },
            {
                'note': 'Chiến dịch quảng cáo thử nghiệm thị trường Philippines',
                'target': 'CMP-LU-PH-001',
                'tool': 'meta_ads.create_draft',
            },
            True,
        ),
        (
            {'tool': 'meta_ads.create_draft', 'target': 'CMP-LU-PH-001', 'budget_php': 15000},
            {'tool': 'meta_ads.create_draft', 'target': 'CMP-LU-PH-001', 'budget_php': 25000},
            False,
        ),
        (
            {'tool': 'meta_ads.create_draft', 'target': 'CMP-LU-PH-001', 'budget_php': 15000},
            {'tool': 'meta_ads.create_draft', 'target': 'CMP-LU-PH-002', 'budget_php': 15000},
            False,
        ),
        (
            {'tool': 'meta_ads.create_draft', 'target': 'CMP-LU-PH-001', 'budget_php': 15000},
            {'tool': 'meta_ads.publish', 'target': 'CMP-LU-PH-001', 'budget_php': 15000},
            False,
        ),
        (
            {
                'tool': 'meta_ads.create_draft',
                'target': 'CMP-LU-PH-001',
                'note': 'Chiến dịch bản nháp lần 1',
            },
            {
                'tool': 'meta_ads.create_draft',
                'target': 'CMP-LU-PH-001',
                'note': 'Chiến dịch bản nháp lần 2',
            },
            False,
        ),
    ],
    ids=[
        'identical_action_produces_same_64_hex_hash',
        'top_level_key_order_does_not_change_hash',
        'nested_dict_key_order_does_not_change_hash',
        'vietnamese_utf8_text_is_stable',
        'different_budget_php_changes_hash',
        'different_target_changes_hash',
        'different_tool_changes_hash',
        'different_vietnamese_note_changes_hash',
    ],
)
def test_action_hash(left, right, should_equal):
    h_left = gateway.action_hash(left)
    h_right = gateway.action_hash(right)
    assert isinstance(h_left, str) and len(h_left) == 64 and set(h_left) <= HEX_CHARS
    assert isinstance(h_right, str) and len(h_right) == 64 and set(h_right) <= HEX_CHARS
    assert (h_left == h_right) is should_equal


@pytest.mark.parametrize(
    ('prior', 'target', 'a_hash', 'decision', 'expected'),
    [
        (
            [],
            'CMP-LU-PH-001',
            'hash_create_draft_001',
            'ALLOW',
            None,
        ),
        (
            [
                {
                    'decision': 'ALLOW',
                    'target': 'CMP-LU-PH-001',
                    'reason': 'allowed draft creation',
                    'result': {'status': 'DRAFT', 'system': 'meta_ads (mock)', 'target': 'CMP-LU-PH-001'},
                    'attempt': 1,
                    'action_hash': 'hash_create_draft_001',
                },
            ],
            'CMP-LU-PH-001',
            'hash_create_draft_001',
            'ALLOW',
            {
                'decision': 'ALLOW',
                'target': 'CMP-LU-PH-001',
                'reason': 'allowed draft creation',
                'result': {'status': 'DRAFT', 'system': 'meta_ads (mock)', 'target': 'CMP-LU-PH-001'},
                'attempt': 1,
                'action_hash': 'hash_create_draft_001',
            },
        ),
        (
            [
                {
                    'decision': 'NEEDS_APPROVAL',
                    'target': 'CMP-LU-PH-001',
                    'reason': 'budget above threshold',
                    'result': {'status': 'WAITING_APPROVAL', 'approval_id': 4},
                    'attempt': 1,
                    'action_hash': 'hash_high_budget_001',
                },
            ],
            'CMP-LU-PH-001',
            'hash_high_budget_001',
            'NEEDS_APPROVAL',
            {
                'decision': 'NEEDS_APPROVAL',
                'target': 'CMP-LU-PH-001',
                'reason': 'budget above threshold',
                'result': {'status': 'WAITING_APPROVAL', 'approval_id': 4},
                'attempt': 1,
                'action_hash': 'hash_high_budget_001',
            },
        ),
        (
            [
                {
                    'decision': 'BLOCK',
                    'target': 'CMP-LU-PH-001',
                    'reason': 'direct publish is forbidden',
                    'result': {'status': 'BLOCKED'},
                    'attempt': 1,
                    'action_hash': 'hash_publish_001',
                },
            ],
            'CMP-LU-PH-001',
            'hash_publish_001',
            'BLOCK',
            None,
        ),
        (
            [
                {
                    'decision': 'ALLOW',
                    'target': 'CMP-LU-PH-001',
                    'reason': 'previously within threshold',
                    'result': {'status': 'DRAFT', 'system': 'meta_ads (mock)', 'target': 'CMP-LU-PH-001'},
                    'attempt': 1,
                    'action_hash': 'hash_create_draft_001',
                },
            ],
            'CMP-LU-PH-001',
            'hash_create_draft_001',
            'NEEDS_APPROVAL',
            None,
        ),
        (
            [
                {
                    'decision': 'NEEDS_APPROVAL',
                    'target': 'CMP-LU-PH-001',
                    'reason': 'previously required approval',
                    'result': {'status': 'WAITING_APPROVAL', 'approval_id': 2},
                    'attempt': 1,
                    'action_hash': 'hash_create_draft_001',
                },
            ],
            'CMP-LU-PH-001',
            'hash_create_draft_001',
            'ALLOW',
            None,
        ),
        (
            [
                {
                    'decision': 'ALLOW',
                    'target': 'CMP-LU-PH-001',
                    'reason': 'allowed draft creation',
                    'result': {'status': 'DRAFT', 'system': 'meta_ads (mock)', 'target': 'CMP-LU-PH-001'},
                    'attempt': 1,
                    'action_hash': 'hash_create_draft_001',
                },
            ],
            'CMP-LU-PH-002',
            'hash_create_draft_001',
            'ALLOW',
            None,
        ),
        (
            [
                {
                    'decision': 'ALLOW',
                    'target': 'CMP-LU-PH-001',
                    'reason': 'allowed draft creation',
                    'result': {'status': 'DRAFT', 'system': 'meta_ads (mock)', 'target': 'CMP-LU-PH-001'},
                    'attempt': 1,
                    'action_hash': 'hash_create_draft_001',
                },
            ],
            'CMP-LU-PH-001',
            'hash_create_draft_002',
            'ALLOW',
            None,
        ),
        (
            [
                {
                    'decision': 'ALLOW',
                    'target': 'CMP-LU-PH-001',
                    'reason': 'pre-A3 row without action_hash',
                    'result': {'status': 'DRAFT', 'system': 'meta_ads (mock)', 'target': 'CMP-LU-PH-001'},
                },
            ],
            'CMP-LU-PH-001',
            'hash_create_draft_001',
            'ALLOW',
            None,
        ),
        (
            [
                {
                    'decision': 'ALLOW',
                    'target': 'CMP-LU-PH-001',
                    'reason': 'first matching call',
                    'result': {'status': 'DRAFT', 'system': 'meta_ads (mock)', 'target': 'CMP-LU-PH-001'},
                    'attempt': 1,
                    'action_hash': 'hash_create_draft_001',
                },
                {
                    'decision': 'ALLOW',
                    'target': 'CMP-LU-PH-001',
                    'reason': 'second matching call',
                    'result': {'status': 'DRAFT', 'system': 'meta_ads (mock)', 'target': 'CMP-LU-PH-001'},
                    'attempt': 2,
                    'action_hash': 'hash_create_draft_001',
                },
            ],
            'CMP-LU-PH-001',
            'hash_create_draft_001',
            'ALLOW',
            {
                'decision': 'ALLOW',
                'target': 'CMP-LU-PH-001',
                'reason': 'second matching call',
                'result': {'status': 'DRAFT', 'system': 'meta_ads (mock)', 'target': 'CMP-LU-PH-001'},
                'attempt': 2,
                'action_hash': 'hash_create_draft_001',
            },
        ),
        (
            [
                {
                    'decision': 'ALLOW',
                    'target': 'CMP-LU-PH-001',
                    'reason': 'matching earlier call',
                    'result': {'status': 'DRAFT', 'system': 'meta_ads (mock)', 'target': 'CMP-LU-PH-001'},
                    'attempt': 1,
                    'action_hash': 'hash_create_draft_001',
                },
                {
                    'decision': 'ALLOW',
                    'target': 'CMP-LU-PH-002',
                    'reason': 'non-matching target after match',
                    'result': {'status': 'DRAFT', 'system': 'meta_ads (mock)', 'target': 'CMP-LU-PH-002'},
                    'attempt': 2,
                    'action_hash': 'hash_create_draft_002',
                },
            ],
            'CMP-LU-PH-001',
            'hash_create_draft_001',
            'ALLOW',
            {
                'decision': 'ALLOW',
                'target': 'CMP-LU-PH-001',
                'reason': 'matching earlier call',
                'result': {'status': 'DRAFT', 'system': 'meta_ads (mock)', 'target': 'CMP-LU-PH-001'},
                'attempt': 1,
                'action_hash': 'hash_create_draft_001',
            },
        ),
        (
            [
                {
                    'decision': 'ALLOW',
                    'target': 'CMP-LU-PH-001',
                    'reason': 'reused detail row',
                    'result': {'status': 'DRAFT', 'system': 'meta_ads (mock)', 'target': 'CMP-LU-PH-001'},
                    'attempt': 2,
                    'action_hash': 'hash_create_draft_001',
                    'reused': True,
                },
            ],
            'CMP-LU-PH-001',
            'hash_create_draft_001',
            'ALLOW',
            {
                'decision': 'ALLOW',
                'target': 'CMP-LU-PH-001',
                'reason': 'reused detail row',
                'result': {'status': 'DRAFT', 'system': 'meta_ads (mock)', 'target': 'CMP-LU-PH-001'},
                'attempt': 2,
                'action_hash': 'hash_create_draft_001',
                'reused': True,
            },
        ),
    ],
    ids=[
        'empty_prior_returns_none',
        'exact_match_allow_returns_detail',
        'exact_match_needs_approval_returns_detail',
        'block_with_everything_matching_returns_none',
        'decision_differs_old_allow_new_needs_approval',
        'decision_differs_old_needs_approval_new_allow',
        'target_differs_returns_none',
        'hash_differs_returns_none',
        'detail_without_action_hash_pre_a3_returns_none',
        'two_matches_returns_newer_last_one',
        'match_followed_by_non_matching_row_still_returns_match',
        'reused_row_with_reused_true_also_counts',
    ],
)
def test_reusable(prior, target, a_hash, decision, expected):
    assert gateway.reusable(prior, target, a_hash, decision) == expected


@pytest.mark.parametrize(
    ('rows', 'attempts', 'expected'),
    [
        (
            [],
            {'campaign': 1, 'care': 1},
            [],
        ),
        (
            [
                {
                    'id': 1,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                    'detail': {'attempt': 1, 'decision': 'ALLOW', 'target': 'CMP-LU-PH-001'},
                },
                {
                    'id': 2,
                    'task_key': 'care',
                    'tool': 'crm.reply_draft',
                    'detail': {'attempt': 1, 'decision': 'ALLOW', 'target': 'CMP-LU-PH-001'},
                },
            ],
            {'campaign': 1, 'care': 1},
            [
                {
                    'id': 1,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                    'detail': {'attempt': 1, 'decision': 'ALLOW', 'target': 'CMP-LU-PH-001'},
                },
                {
                    'id': 2,
                    'task_key': 'care',
                    'tool': 'crm.reply_draft',
                    'detail': {'attempt': 1, 'decision': 'ALLOW', 'target': 'CMP-LU-PH-001'},
                },
            ],
        ),
        (
            [
                {
                    'id': 1,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                    'detail': {'attempt': 1, 'decision': 'ALLOW', 'target': 'CMP-LU-PH-001'},
                },
                {
                    'id': 2,
                    'task_key': 'care',
                    'tool': 'crm.reply_draft',
                    'detail': {'attempt': 1, 'decision': 'ALLOW', 'target': 'CMP-LU-PH-001'},
                },
                {
                    'id': 3,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                    'detail': {'attempt': 2, 'decision': 'ALLOW', 'target': 'CMP-LU-PH-001', 'reused': True},
                },
            ],
            {'campaign': 2, 'care': 1},
            [
                {
                    'id': 2,
                    'task_key': 'care',
                    'tool': 'crm.reply_draft',
                    'detail': {'attempt': 1, 'decision': 'ALLOW', 'target': 'CMP-LU-PH-001'},
                },
                {
                    'id': 3,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                    'detail': {'attempt': 2, 'decision': 'ALLOW', 'target': 'CMP-LU-PH-001', 'reused': True},
                },
            ],
        ),
        (
            [
                {
                    'id': 1,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                    'detail': {'decision': 'ALLOW', 'target': 'CMP-LU-PH-001'},
                },
            ],
            {'campaign': 1},
            [
                {
                    'id': 1,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                    'detail': {'decision': 'ALLOW', 'target': 'CMP-LU-PH-001'},
                },
            ],
        ),
        (
            [
                {
                    'id': 1,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                    'detail': {'decision': 'ALLOW', 'target': 'CMP-LU-PH-001'},
                },
                {
                    'id': 2,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                    'detail': {'attempt': 2, 'decision': 'ALLOW', 'target': 'CMP-LU-PH-001'},
                },
            ],
            {'campaign': 2},
            [
                {
                    'id': 2,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                    'detail': {'attempt': 2, 'decision': 'ALLOW', 'target': 'CMP-LU-PH-001'},
                },
            ],
        ),
        (
            [
                {
                    'id': 1,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                    'detail': None,
                },
            ],
            {'campaign': 1},
            [
                {
                    'id': 1,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                    'detail': None,
                },
            ],
        ),
        (
            [
                {
                    'id': 1,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                },
            ],
            {'campaign': 1},
            [
                {
                    'id': 1,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                },
            ],
        ),
        (
            [
                {
                    'id': 1,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                    'detail': None,
                },
                {
                    'id': 2,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                },
            ],
            {'campaign': 2},
            [],
        ),
        (
            [
                {
                    'id': 1,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                    'detail': {'attempt': 1, 'decision': 'ALLOW', 'target': 'CMP-LU-PH-001'},
                },
                {
                    'id': 2,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                    'detail': {'attempt': 2, 'decision': 'ALLOW', 'target': 'CMP-LU-PH-001'},
                },
            ],
            {},
            [
                {
                    'id': 1,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                    'detail': {'attempt': 1, 'decision': 'ALLOW', 'target': 'CMP-LU-PH-001'},
                },
            ],
        ),
        (
            [
                {
                    'id': 1,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.publish',
                    'detail': {'attempt': 1, 'decision': 'BLOCK', 'target': 'CMP-LU-PH-001'},
                },
                {
                    'id': 2,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                    'detail': {'attempt': 2, 'decision': 'ALLOW', 'target': 'CMP-LU-PH-001'},
                },
            ],
            {'campaign': 2},
            [
                {
                    'id': 2,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                    'detail': {'attempt': 2, 'decision': 'ALLOW', 'target': 'CMP-LU-PH-001'},
                },
            ],
        ),
        (
            [
                {
                    'id': 10,
                    'task_key': 'content',
                    'tool': 'meta_ads.create_draft',
                    'detail': {'attempt': 1, 'decision': 'ALLOW', 'target': 'CMP-LU-PH-001'},
                },
                {
                    'id': 11,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.publish',
                    'detail': {'attempt': 1, 'decision': 'BLOCK', 'target': 'CMP-LU-PH-001'},
                },
                {
                    'id': 12,
                    'task_key': 'care',
                    'tool': 'crm.reply_draft',
                    'detail': {'attempt': 1, 'decision': 'ALLOW', 'target': 'CMP-LU-PH-001'},
                },
                {
                    'id': 13,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                    'detail': {'attempt': 2, 'decision': 'ALLOW', 'target': 'CMP-LU-PH-001'},
                },
                {
                    'id': 14,
                    'task_key': 'care',
                    'tool': 'crm.reply_draft',
                    'detail': {'attempt': 2, 'decision': 'NEEDS_APPROVAL', 'target': 'CMP-LU-PH-001'},
                },
                {
                    'id': 15,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                    'detail': {'attempt': 3, 'decision': 'ALLOW', 'target': 'CMP-LU-PH-001', 'reused': True},
                },
            ],
            {'content': 1, 'campaign': 3, 'care': 2},
            [
                {
                    'id': 10,
                    'task_key': 'content',
                    'tool': 'meta_ads.create_draft',
                    'detail': {'attempt': 1, 'decision': 'ALLOW', 'target': 'CMP-LU-PH-001'},
                },
                {
                    'id': 14,
                    'task_key': 'care',
                    'tool': 'crm.reply_draft',
                    'detail': {'attempt': 2, 'decision': 'NEEDS_APPROVAL', 'target': 'CMP-LU-PH-001'},
                },
                {
                    'id': 15,
                    'task_key': 'campaign',
                    'tool': 'meta_ads.create_draft',
                    'detail': {'attempt': 3, 'decision': 'ALLOW', 'target': 'CMP-LU-PH-001', 'reused': True},
                },
            ],
        ),
    ],
    ids=[
        'empty_input_returns_empty_list',
        'all_rows_attempt_1_with_tasks_at_1_all_kept',
        'retried_task_keeps_only_attempt_2_other_tasks_unaffected',
        'row_without_attempt_counts_as_1_kept_at_1',
        'row_without_attempt_counts_as_1_dropped_at_2',
        'row_with_detail_none_counts_as_1',
        'row_with_detail_missing_counts_as_1',
        'rows_with_detail_none_or_missing_dropped_at_attempt_2',
        'task_missing_from_attempts_counts_as_1',
        'block_row_of_attempt_1_disappears_when_task_at_attempt_2',
        'order_preserved_across_tasks_and_attempts',
    ],
)
def test_current_attempt(rows, attempts, expected):
    assert gateway.current_attempt(rows, attempts) == expected
