import copy
import pytest

from app.core import graph as g

ALL_TASKS = (
    'plan', 'market', 'product', 'offer', 'content', 'campaign',
    'leads', 'care', 'kpi', 'finance', 'qa', 'audit', 'monitor', 'summary',
)

BASE_PENDING = {k: 'PENDING' for k in ALL_TASKS}

BASE_BUSINESS_COMPLETED = {
    'plan': 'COMPLETED',
    'market': 'COMPLETED',
    'product': 'COMPLETED',
    'offer': 'COMPLETED',
    'content': 'COMPLETED',
    'campaign': 'COMPLETED',
    'leads': 'COMPLETED',
    'care': 'COMPLETED',
    'kpi': 'COMPLETED',
    'finance': 'COMPLETED',
    'qa': 'PENDING',
    'audit': 'PENDING',
    'monitor': 'PENDING',
    'summary': 'PENDING',
}


def _statuses(base=BASE_PENDING, **overrides):
    out = copy.deepcopy(base)
    out.update(overrides)
    return out


@pytest.mark.parametrize(
    ('statuses', 'soft', 'expected'),
    [
        (
            _statuses(BASE_BUSINESS_COMPLETED),
            g.SOFT,
            'qa',
        ),
        (
            _statuses(BASE_BUSINESS_COMPLETED, kpi='FAILED', finance='SKIPPED'),
            g.SOFT,
            'qa',
        ),
        (
            _statuses(BASE_BUSINESS_COMPLETED, kpi='FAILED', finance='SKIPPED', qa='COMPLETED'),
            g.SOFT,
            'audit',
        ),
        (
            _statuses(
                BASE_BUSINESS_COMPLETED,
                kpi='FAILED',
                finance='SKIPPED',
                qa='COMPLETED',
                audit='FAILED',
            ),
            g.SOFT,
            'monitor',
        ),
        (
            _statuses(
                BASE_BUSINESS_COMPLETED,
                kpi='FAILED',
                finance='SKIPPED',
                qa='COMPLETED',
                audit='FAILED',
                monitor='SKIPPED',
            ),
            g.SOFT,
            'summary',
        ),
        (
            _statuses(BASE_BUSINESS_COMPLETED, kpi='FAILED', finance='PENDING'),
            g.SOFT,
            None,
        ),
        (
            _statuses(BASE_BUSINESS_COMPLETED, finance='RUNNING'),
            g.SOFT,
            None,
        ),
        (
            _statuses(BASE_BUSINESS_COMPLETED, finance='CANCELLED'),
            g.SOFT,
            None,
        ),
        (
            _statuses(
                BASE_BUSINESS_COMPLETED,
                qa='COMPLETED',
                audit='COMPLETED',
                monitor='RUNNING',
            ),
            g.SOFT,
            None,
        ),
        (
            _statuses(BASE_BUSINESS_COMPLETED, kpi='FAILED', finance='SKIPPED'),
            (),
            None,
        ),
        (
            _statuses(
                BASE_BUSINESS_COMPLETED,
                qa='FAILED',
                audit='COMPLETED',
                monitor='COMPLETED',
            ),
            (),
            None,
        ),
    ],
    ids=[
        'all_business_completed_returns_qa',
        'kpi_failed_finance_skipped_returns_qa',
        'after_qa_completed_returns_audit',
        'after_qa_completed_and_audit_failed_returns_monitor',
        'summary_ready_when_qa_audit_monitor_finished',
        'qa_not_ready_while_business_task_pending',
        'qa_not_ready_while_business_task_running',
        'qa_not_ready_when_business_task_cancelled',
        'summary_waits_for_monitor_to_finish',
        'strict_regression_kpi_failed_finance_skipped_blocks_qa',
        'strict_regression_qa_failed_blocks_summary',
    ],
)
def test_next_ready_soft(statuses, soft, expected):
    assert g.next_ready(statuses, g.GRAPH, soft=soft) == expected


@pytest.mark.parametrize(
    ('statuses', 'soft', 'expected'),
    [
        (
            _statuses(BASE_BUSINESS_COMPLETED, kpi='FAILED', finance='PENDING'),
            g.SOFT,
            ['finance'],
        ),
        (
            _statuses(BASE_BUSINESS_COMPLETED, kpi='FAILED', finance='SKIPPED'),
            g.SOFT,
            [],
        ),
        (
            _statuses(
                BASE_BUSINESS_COMPLETED,
                kpi='FAILED',
                finance='SKIPPED',
                qa='FAILED',
                audit='SKIPPED',
                monitor='FAILED',
            ),
            g.SOFT,
            [],
        ),
        (
            _statuses(plan='COMPLETED', market='CANCELLED'),
            g.SOFT,
            ['product', 'qa', 'audit', 'monitor'],
        ),
        (
            _statuses(BASE_BUSINESS_COMPLETED, qa='CANCELLED', audit='COMPLETED'),
            g.SOFT,
            ['monitor', 'summary'],
        ),
        (
            _statuses(BASE_BUSINESS_COMPLETED, kpi='FAILED', finance='PENDING'),
            (),
            ['finance', 'qa', 'audit', 'monitor'],
        ),
    ],
    ids=[
        'kpi_failed_skips_finance_but_not_soft_tasks',
        'kpi_failed_and_finance_skipped_skips_no_soft_task',
        'failed_and_skipped_supervisors_do_not_skip_summary',
        'cancelled_business_dep_skips_direct_business_and_soft_tasks',
        'cancelled_qa_skips_monitor_and_summary',
        'strict_regression_kpi_failed_skips_finance_and_soft_tasks',
    ],
)
def test_to_skip_soft(statuses, soft, expected):
    assert g.to_skip(statuses, g.GRAPH, soft=soft) == expected


@pytest.mark.parametrize(
    ('task', 'src', 'dst', 'soft', 'expected'),
    [
        ('qa', 'COMPLETED', 'PENDING', g.SOFT, True),
        ('audit', 'COMPLETED', 'PENDING', g.SOFT, True),
        ('monitor', 'COMPLETED', 'PENDING', g.SOFT, True),
        ('summary', 'COMPLETED', 'PENDING', g.SOFT, True),
        ('qa', 'COMPLETED', 'RUNNING', g.SOFT, False),
        ('qa', 'FAILED', 'PENDING', g.SOFT, False),
        ('qa', 'SKIPPED', 'PENDING', g.SOFT, False),
        ('market', 'COMPLETED', 'PENDING', g.SOFT, False),
        ('kpi', 'COMPLETED', 'PENDING', g.SOFT, False),
        ('qa', 'COMPLETED', 'PENDING', (), False),
    ],
    ids=[
        'qa_completed_to_pending',
        'audit_completed_to_pending',
        'monitor_completed_to_pending',
        'summary_completed_to_pending',
        'soft_completed_to_running_disallowed',
        'soft_failed_to_pending_disallowed',
        'soft_skipped_to_pending_disallowed',
        'business_market_completed_to_pending_disallowed',
        'business_kpi_completed_to_pending_disallowed',
        'strict_regression_without_soft_disallowed',
    ],
)
def test_can_rerun(task, src, dst, soft, expected):
    assert g.can_rerun(task, src, dst, soft=soft) is expected


@pytest.mark.parametrize(
    ('task', 'statuses', 'soft', 'expected'),
    [
        (
            'kpi',
            _statuses(
                BASE_BUSINESS_COMPLETED,
                kpi='FAILED',
                finance='SKIPPED',
                qa='COMPLETED',
                audit='COMPLETED',
                monitor='FAILED',
                summary='COMPLETED',
            ),
            g.SOFT,
            {
                'kpi': 'PENDING',
                'finance': 'PENDING',
                'qa': 'PENDING',
                'audit': 'PENDING',
                'monitor': 'PENDING',
                'summary': 'PENDING',
            },
        ),
        (
            'market',
            _statuses(
                plan='COMPLETED',
                market='FAILED',
                product='COMPLETED',
                offer='SKIPPED',
                content='SKIPPED',
                campaign='SKIPPED',
                leads='SKIPPED',
                care='SKIPPED',
                kpi='SKIPPED',
                finance='SKIPPED',
                qa='COMPLETED',
                audit='FAILED',
                monitor='COMPLETED',
                summary='SKIPPED',
            ),
            g.SOFT,
            {
                'market': 'PENDING',
                'offer': 'PENDING',
                'content': 'PENDING',
                'campaign': 'PENDING',
                'leads': 'PENDING',
                'care': 'PENDING',
                'kpi': 'PENDING',
                'finance': 'PENDING',
                'qa': 'PENDING',
                'audit': 'PENDING',
                'monitor': 'PENDING',
                'summary': 'PENDING',
            },
        ),
        (
            'kpi',
            _statuses(
                BASE_BUSINESS_COMPLETED,
                kpi='FAILED',
                finance='SKIPPED',
                qa='COMPLETED',
                audit='PENDING',
                monitor='PENDING',
                summary='PENDING',
            ),
            g.SOFT,
            {
                'kpi': 'PENDING',
                'finance': 'PENDING',
                'qa': 'PENDING',
            },
        ),
        (
            'qa',
            _statuses(
                BASE_BUSINESS_COMPLETED,
                qa='FAILED',
                audit='COMPLETED',
                monitor='COMPLETED',
                summary='COMPLETED',
            ),
            g.SOFT,
            {
                'qa': 'PENDING',
                'monitor': 'PENDING',
                'summary': 'PENDING',
            },
        ),
        (
            'kpi',
            _statuses(
                BASE_BUSINESS_COMPLETED,
                kpi='FAILED',
                finance='SKIPPED',
                qa='COMPLETED',
                audit='FAILED',
                monitor='SKIPPED',
                summary='SKIPPED',
            ),
            (),
            {
                'kpi': 'PENDING',
                'finance': 'PENDING',
                'monitor': 'PENDING',
                'summary': 'PENDING',
            },
        ),
    ],
    ids=[
        'kpi_failed_rearms_skipped_finance_and_completed_or_failed_soft',
        'market_failed_never_rearms_completed_business_product',
        'kpi_failed_ignores_already_pending_soft_descendants',
        'qa_failed_rearms_monitor_and_summary_not_audit',
        'strict_regression_rearms_only_skipped_descendants',
    ],
)
def test_retry_plan_soft(task, statuses, soft, expected):
    assert g.retry_plan(task, statuses, g.GRAPH, soft=soft) == expected
