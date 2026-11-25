"""Deterministic fixes the Commander may apply when it sends work back (A4, DEMO_PLAN_OPTION_A 7.2 step 4).

A check is '<name>:<arg>'. Closed vocabulary; what gets fixed is decided only here, never by an LLM or a room.
  verify_supplier_cost:<sku>  facts level, whole run, learnable   the supplier "re-quotes": the run's unit cost
                                                                  for <sku> is replaced by the reference cost
                                                                  (OA-D01: bad_cost = a stale/wrong quote)
  drop_blocked_action:<tool>  artifact level, not learnable       remove <tool> from requested_actions before the
                                                                  gateway is called (it was BLOCKed last attempt)
Both functions are pure: they return (new data, applied) and never write anywhere.
"""
from copy import deepcopy

CHECKS = {'verify_supplier_cost': {'level': 'facts', 'learnable': True},
          'drop_blocked_action': {'level': 'artifact', 'learnable': False}}
FIX = {'reference': 'verify_supplier_cost', 'blocked_action': 'drop_blocked_action'}  # finding rule -> check


def _split(check: str) -> tuple:
    name, _, arg = check.partition(':')
    return name, arg


def level(check: str) -> str | None:
    return CHECKS.get(_split(check)[0], {}).get('level')


def apply_facts(facts: dict, checks, ref_facts: dict) -> tuple:
    """Facts-level checks. `ref_facts` is the clean reference the QA compares with (data.facts_for((), objective);
    not the raw fixture, because a custom objective changes supplier costs). Returns (facts copy, applied)."""
    out, applied = deepcopy(facts), []
    for check in checks:
        name, sku = _split(check)
        if name != 'verify_supplier_cost':
            continue
        ref = next((s for s in ref_facts['suppliers']['items'] if s['sku'] == sku), None)
        cur = next((s for s in out['suppliers']['items'] if s['sku'] == sku), None)
        if ref is None or cur is None or cur['unit_cost_php'] == ref['unit_cost_php']:
            continue
        applied.append({'check': check, 'field': f'suppliers[{sku}].unit_cost_php',
                        'before': cur['unit_cost_php'], 'after': ref['unit_cost_php'], 'source': 'fixture'})
        cur['unit_cost_php'] = ref['unit_cost_php']
    return out, applied


def apply_artifact(art: dict, checks) -> tuple:
    """Artifact-level checks. Returns (artifact copy, applied)."""
    out, applied = deepcopy(art), []
    for check in checks:
        name, tool = _split(check)
        if name != 'drop_blocked_action':
            continue
        before = [a['tool'] for a in out.get('requested_actions', [])]
        if tool not in before:
            continue
        out['requested_actions'] = [a for a in out['requested_actions'] if a['tool'] != tool]
        applied.append({'check': check, 'field': 'requested_actions', 'before': before,
                        'after': [a['tool'] for a in out['requested_actions']], 'source': 'rework'})
    return out, applied
