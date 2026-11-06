import pytest

from app.core import graph as g

ALL_TASKS = (
    'plan', 'market', 'product', 'offer', 'content', 'campaign',
    'leads', 'care', 'kpi', 'finance', 'qa', 'audit', 'monitor', 'summary',
)


def _statuses(**overrides):
    base = {k: 'PENDING' for k in ALL_TASKS}
    base.update(overrides)
    return base


@pytest.mark.parametrize(
    ('src', 'dst', 'expected'),
    [
        ('PENDING', 'PENDING', False),
        ('PENDING', 'RUNNING', True),
        ('PENDING', 'COMPLETED', False),
        ('PENDING', 'FAILED', False),
        ('PENDING', 'SKIPPED', True),
        ('PENDING', 'CANCELLED', True),
        ('RUNNING', 'PENDING', False),
        ('RUNNING', 'RUNNING', False),
        ('RUNNING', 'COMPLETED', True),
        ('RUNNING', 'FAILED', True),
        ('RUNNING', 'SKIPPED', False),
        ('RUNNING', 'CANCELLED', True),
        ('COMPLETED', 'PENDING', False),
        ('COMPLETED', 'RUNNING', False),
        ('COMPLETED', 'COMPLETED', False),
        ('COMPLETED', 'FAILED', False),
        ('COMPLETED', 'SKIPPED', False),
        ('COMPLETED', 'CANCELLED', False),
        ('FAILED', 'PENDING', True),
        ('FAILED', 'RUNNING', False),
        ('FAILED', 'COMPLETED', False),
        ('FAILED', 'FAILED', False),
        ('FAILED', 'SKIPPED', False),
        ('FAILED', 'CANCELLED', False),
        ('SKIPPED', 'PENDING', True),
        ('SKIPPED', 'RUNNING', False),
        ('SKIPPED', 'COMPLETED', False),
        ('SKIPPED', 'FAILED', False),
        ('SKIPPED', 'SKIPPED', False),
        ('SKIPPED', 'CANCELLED', True),
        ('CANCELLED', 'PENDING', False),
        ('CANCELLED', 'RUNNING', False),
        ('CANCELLED', 'COMPLETED', False),
        ('CANCELLED', 'FAILED', False),
        ('CANCELLED', 'SKIPPED', False),
        ('CANCELLED', 'CANCELLED', False),
        ('UNKNOWN', 'PENDING', False),
        ('PENDING', 'UNKNOWN', False),
    ],
    ids=[
        'PENDING->PENDING',
        'PENDING->RUNNING',
        'PENDING->COMPLETED',
        'PENDING->FAILED',
        'PENDING->SKIPPED',
        'PENDING->CANCELLED',
        'RUNNING->PENDING',
        'RUNNING->RUNNING',
        'RUNNING->COMPLETED',
        'RUNNING->FAILED',
        'RUNNING->SKIPPED',
        'RUNNING->CANCELLED',
        'COMPLETED->PENDING',
        'COMPLETED->RUNNING',
        'COMPLETED->COMPLETED',
        'COMPLETED->FAILED',
        'COMPLETED->SKIPPED',
        'COMPLETED->CANCELLED',
        'FAILED->PENDING',
        'FAILED->RUNNING',
        'FAILED->COMPLETED',
        'FAILED->FAILED',
        'FAILED->SKIPPED',
        'FAILED->CANCELLED',
        'SKIPPED->PENDING',
        'SKIPPED->RUNNING',
        'SKIPPED->COMPLETED',
        'SKIPPED->FAILED',
        'SKIPPED->SKIPPED',
        'SKIPPED->CANCELLED',
        'CANCELLED->PENDING',
        'CANCELLED->RUNNING',
        'CANCELLED->COMPLETED',
        'CANCELLED->FAILED',
        'CANCELLED->SKIPPED',
        'CANCELLED->CANCELLED',
        'UNKNOWN->PENDING',
        'PENDING->UNKNOWN',
    ],
)
def test_can_transition(src, dst, expected):
    assert g.can_transition(src, dst) is expected


@pytest.mark.parametrize(
    ('graph', 'expected', 'first_task', 'last_task'),
    [
        (
            g.GRAPH,
            list(ALL_TASKS),
            'plan',
            'summary',
        ),
        (
            {'top': [], 'left': ['top'], 'right': ['top'], 'bottom': ['left', 'right']},
            ['top', 'left', 'right', 'bottom'],
            'top',
            'bottom',
        ),
        (
            {'root': [], 'second': ['root'], 'first': ['root']},
            ['root', 'second', 'first'],
            'root',
            'first',
        ),
    ],
    ids=['real_graph', 'diamond_graph', 'declaration_tie_break'],
)
def test_topo_order(graph, expected, first_task, last_task):
    order = g.topo_order(graph)
    assert (
        order == expected
        and order[0] == first_task
        and order[-1] == last_task
        and all(order.index(dep) < order.index(node) for node, deps in graph.items() for dep in deps)
    )


@pytest.mark.parametrize(
    ('bad_graph', 'match'),
    [
        ({'a': ['missing']}, 'unknown dependency'),
        ({'a': ['b'], 'b': ['a']}, 'cycle in task graph'),
        ({'a': ['a']}, 'cycle in task graph'),
    ],
    ids=['unknown_dependency', 'two_node_cycle', 'self_loop'],
)
def test_topo_order_errors(bad_graph, match):
    with pytest.raises(ValueError, match=match):
        g.topo_order(bad_graph)


@pytest.mark.parametrize(
    ('task', 'expected'),
    [
        (
            'plan',
            {
                'market', 'product', 'offer', 'content', 'campaign',
                'leads', 'care', 'kpi', 'finance', 'qa', 'audit', 'monitor', 'summary',
            },
        ),
        (
            'campaign',
            {'leads', 'care', 'kpi', 'finance', 'qa', 'audit', 'monitor', 'summary'},
        ),
        (
            'finance',
            {'qa', 'audit', 'monitor', 'summary'},
        ),
        (
            'summary',
            set(),
        ),
    ],
    ids=['plan_all_13', 'campaign_downstream', 'finance_downstream', 'summary_empty'],
)
def test_descendants(task, expected):
    assert g.descendants(task, g.GRAPH) == expected


@pytest.mark.parametrize(
    ('statuses', 'expected'),
    [
        (_statuses(), 'plan'),
        (_statuses(plan='COMPLETED'), 'market'),
        (
            _statuses(
                plan='COMPLETED',
                market='COMPLETED',
                product='COMPLETED',
                offer='COMPLETED',
                content='RUNNING',
            ),
            None,
        ),
        (
            _statuses(
                plan='COMPLETED',
                market='COMPLETED',
                product='COMPLETED',
                offer='COMPLETED',
                content='COMPLETED',
            ),
            'campaign',
        ),
        ({k: 'COMPLETED' for k in ALL_TASKS}, None),
    ],
    ids=[
        'fresh_run_returns_plan',
        'after_plan_returns_market',
        'campaign_waits_for_content',
        'campaign_ready_after_offer_and_content',
        'nothing_ready_when_all_completed',
    ],
)
def test_next_ready(statuses, expected):
    assert g.next_ready(statuses, g.GRAPH) == expected


@pytest.mark.parametrize(
    ('statuses', 'graph', 'expected'),
    [
        (
            {'plan': 'COMPLETED', 'market': 'FAILED', 'product': 'PENDING', 'offer': 'PENDING'},
            {'plan': [], 'market': ['plan'], 'product': ['market'], 'offer': ['product']},
            ['product'],
        ),
        (
            _statuses(plan='COMPLETED', market='FAILED'),
            g.GRAPH,
            ['product', 'qa', 'audit', 'monitor'],
        ),
        (
            _statuses(plan='CANCELLED'),
            g.GRAPH,
            ['market'],
        ),
        (
            _statuses(plan='SKIPPED'),
            g.GRAPH,
            ['market'],
        ),
        (
            _statuses(plan='COMPLETED'),
            g.GRAPH,
            [],
        ),
    ],
    ids=[
        'market_failed_one_pass_chain_only_product',
        'market_failed_one_pass_full_graph',
        'cancelled_dependency_blocks',
        'skipped_dependency_blocks',
        'completed_dependency_does_not_block',
    ],
)
def test_to_skip(statuses, graph, expected):
    assert g.to_skip(statuses, graph) == expected


@pytest.mark.parametrize(
    ('statuses', 'expected'),
    [
        ({}, 'PENDING'),
        ({k: 'COMPLETED' for k in ALL_TASKS}, 'COMPLETED'),
        (_statuses(plan='COMPLETED', market='RUNNING'), 'RUNNING'),
        (_statuses(plan='COMPLETED', market='FAILED', product='CANCELLED'), 'CANCELLED'),
        (_statuses(plan='COMPLETED', market='FAILED'), 'FAILED'),
        (_statuses(plan='COMPLETED'), 'PENDING'),
    ],
    ids=[
        'empty_is_pending',
        'all_completed',
        'mixed_with_running',
        'cancelled_wins_over_failed',
        'failed_with_pending_leftovers',
        'pending_and_completed_nothing_failed',
    ],
)
def test_run_status(statuses, expected):
    assert g.run_status(statuses) == expected


@pytest.mark.parametrize(
    ('task', 'statuses', 'graph', 'expected'),
    [
        (
            'market',
            _statuses(
                plan='COMPLETED',
                market='FAILED',
                product='SKIPPED',
                offer='SKIPPED',
            ),
            g.GRAPH,
            {'market': 'PENDING', 'product': 'PENDING', 'offer': 'PENDING'},
        ),
        (
            'market',
            _statuses(
                plan='COMPLETED',
                market='FAILED',
                product='COMPLETED',
                offer='SKIPPED',
            ),
            g.GRAPH,
            {'market': 'PENDING', 'offer': 'PENDING'},
        ),
    ],
    ids=[
        'rearms_failed_market_and_skipped_descendants',
        'completed_descendants_untouched',
    ],
)
def test_retry_plan(task, statuses, graph, expected):
    assert g.retry_plan(task, statuses, graph) == expected


@pytest.mark.parametrize(
    ('task', 'statuses'),
    [
        ('market', _statuses(market='PENDING')),
        ('market', _statuses(market='RUNNING')),
        ('market', _statuses(market='COMPLETED')),
    ],
    ids=['pending_not_failed', 'running_not_failed', 'completed_not_failed'],
)
def test_retry_plan_non_failed_raises(task, statuses):
    with pytest.raises(ValueError, match='only a FAILED task can be retried'):
        g.retry_plan(task, statuses, g.GRAPH)
