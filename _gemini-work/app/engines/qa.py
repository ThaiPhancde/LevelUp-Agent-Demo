"""QA Engine (deterministic, no LLM). Each rule is a pure function returning findings; run() combines them.

Finding = {'rule', 'severity': 'FAIL'|'WARN', 'task_key', 'detail'}.
Rules:
  schema       every business artifact present and schema-valid (rejected artifacts reported with their errors)
  reference    unit costs used by agents equal the clean reference supplier data (catches injected 9999)
  arithmetic   offer / kpi / finance / leads numbers recomputed from their own inputs
  consistency  the same SKU, margin, budget and spend flow unchanged between artifacts
  narrative    numbers written in a narrative exist in that artifact (WARN only: wording may round)
"""
import math
import re

from app.core import artifacts
from app.core.graph import BUSINESS

TOL = 0.011  # money is rounded to 2 decimals


def _f(rule, task_key, detail, severity='FAIL'):
    return {'rule': rule, 'severity': severity, 'task_key': task_key, 'detail': detail}


def _close(a, b, tol=TOL):
    return a is not None and b is not None and abs(float(a) - float(b)) <= tol


def schema(arts: dict, rejected: dict | None = None) -> list:
    out = []
    for key in BUSINESS:
        a = arts.get(key)
        if a is None:
            errs = (rejected or {}).get(key)
            out.append(_f('schema', key, 'artifact rejected: ' + '; '.join(errs) if errs else 'missing artifact'))
            continue
        out += [_f('schema', key, e) for e in artifacts.validate(a)]
    return out


def reference(arts: dict, ref_facts: dict) -> list:
    ref = {s['sku']: s['unit_cost_php'] for s in ref_facts['suppliers']['items']}
    out = []
    o = arts.get('offer')
    if o and o.get('sku') in ref and not _close(o.get('unit_cost_php'), ref[o['sku']]):
        out.append(_f('reference', 'offer', f'{o["sku"]} unit_cost_php {o.get("unit_cost_php")} != reference {ref[o["sku"]]}'))
    for c in (arts.get('product') or {}).get('candidates', []):
        if c.get('sku') in ref and not _close(c.get('unit_cost_php'), ref[c['sku']]):
            out.append(_f('reference', 'product', f'{c["sku"]} unit_cost_php {c.get("unit_cost_php")} != reference {ref[c["sku"]]}'))
    return out


def arithmetic(arts: dict) -> list:
    out = []
    o = arts.get('offer')
    if o:
        m = o['selling_price_php'] - o['unit_cost_php'] - o['shipping_php'] - o['payment_fee_php']
        if not _close(o['margin_per_unit_php'], m):
            out.append(_f('arithmetic', 'offer', f'margin_per_unit_php {o["margin_per_unit_php"]} != {m}'))
        be = math.ceil(o['campaign_budget_php'] / m) if m > 0 else 0
        if o['breakeven_orders'] != be:
            out.append(_f('arithmetic', 'offer', f'breakeven_orders {o["breakeven_orders"]} != {be}'))
    k = arts.get('kpi')
    if k:
        checks = {'net_revenue_php': k['net_units'] * k['selling_price_php'],
                  'roas': round(k['net_revenue_php'] / k['ad_spend_php'], 2) if k['ad_spend_php'] else 0.0}
        for field, want in checks.items():
            if not _close(k[field], want):
                out.append(_f('arithmetic', 'kpi', f'{field} {k[field]} != {want}'))
    f = arts.get('finance')
    if f:
        before = f['net_units'] * f['margin_per_unit_php']
        if not _close(f['contribution_before_ads_php'], before):
            out.append(_f('arithmetic', 'finance', f'contribution_before_ads_php {f["contribution_before_ads_php"]} != {before}'))
        if k and not _close(f['contribution_after_ads_php'], f['contribution_before_ads_php'] - k['ad_spend_php']):
            out.append(_f('arithmetic', 'finance', 'contribution_after_ads_php != before - ad_spend'))
    lr = arts.get('leads')
    if lr and lr['unconfirmed'] != lr['leads'] - lr['confirmed']:
        out.append(_f('arithmetic', 'leads', 'unconfirmed != leads - confirmed'))
    return out


def consistency(arts: dict) -> list:
    out = []
    sel = (arts.get('product') or {}).get('selected_sku')
    for key in ('offer', 'content', 'campaign', 'leads', 'care', 'kpi', 'finance'):
        a = arts.get(key)
        if a and sel and a.get('sku') != sel:
            out.append(_f('consistency', key, f'sku {a.get("sku")} != selected {sel}'))
    o, c, k, f = (arts.get(x) for x in ('offer', 'campaign', 'kpi', 'finance'))
    if o and c and not _close(c['budget_php'], o['campaign_budget_php']):
        out.append(_f('consistency', 'campaign', 'budget_php != offer.campaign_budget_php'))
    if c and k and not _close(k['ad_spend_php'], c['budget_php']):
        out.append(_f('consistency', 'kpi', 'ad_spend_php != campaign.budget_php'))
    if o and f and not _close(f['margin_per_unit_php'], o['margin_per_unit_php']):
        out.append(_f('consistency', 'finance', 'margin_per_unit_php != offer.margin_per_unit_php'))
    if c and c.get('status') != 'DRAFT':
        out.append(_f('consistency', 'campaign', f'campaign status {c.get("status")} is not DRAFT'))
    return out


_NUM = re.compile(r'-?\d+(?:[.,]\d+)?')


def _numbers(obj, acc):
    if isinstance(obj, bool):
        return acc
    if isinstance(obj, (int, float)):
        acc.add(round(float(obj), 2))
    elif isinstance(obj, dict):
        for v in obj.values():
            _numbers(v, acc)
    elif isinstance(obj, list):
        acc.add(float(len(obj)))
        for v in obj:
            _numbers(v, acc)
    elif isinstance(obj, str):
        acc.update(round(float(n.replace(',', '.')), 2) for n in _NUM.findall(obj))
    return acc


def narrative(arts: dict) -> list:
    out = []
    for key in BUSINESS:
        a = arts.get(key)
        if not a or not a.get('narrative'):
            continue
        known = _numbers({k: v for k, v in a.items() if k != 'narrative'}, set())
        for n in _NUM.findall(a['narrative']):
            if round(float(n.replace(',', '.')), 2) not in known:
                out.append(_f('narrative', key, f'number {n} in narrative not found in artifact', 'WARN'))
    return out


def status(findings: list) -> str:
    if any(f['severity'] == 'FAIL' for f in findings):
        return 'FAIL'
    return 'WARN' if findings else 'PASS'


def run(arts: dict, ref_facts: dict, rejected: dict | None = None) -> dict:
    findings = schema(arts, rejected) + reference(arts, ref_facts) + arithmetic(arts) + consistency(arts) + narrative(arts)
    return {'engine': 'qa', 'status': status(findings), 'findings': findings,
            'checked': [k for k in BUSINESS if k in arts]}
