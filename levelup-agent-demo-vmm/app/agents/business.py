"""Pure compute() for the business agents. Every number comes from `facts` (mock fixtures for this run)
or from an upstream artifact in `inputs`; nothing is invented and no LLM touches these values.

Formulas (DEMO_PLAN 4.3):
  margin_per_unit = price - unit_cost - shipping - payment_fee
  breakeven_orders = ceil(campaign_budget / margin_per_unit)   (None-safe: 0 when margin <= 0)
  return_rate = returned / delivered ; net_units = delivered - returned
  roas = net_revenue / ad_spend      ; contribution_after_ads = net_units * margin - ad_spend
"""
import math

# Plain-language wording for summaries people read (codes stay in the artifact fields for rules and tests).
RISK_VN = {'HIGH': 'cao', 'MEDIUM': 'trung bình', 'LOW': 'thấp'}
DECISION_VN = {'DRAFT_READY': 'sẵn sàng để duyệt', 'HOLD_DRAFT': 'giữ ở bản nháp', 'NEEDS_REVIEW': 'cần xem lại'}
INTENT_VN = {'product_question': 'hỏi về sản phẩm', 'price_question': 'hỏi giá', 'shipping_question': 'hỏi vận chuyển',
             'order_status': 'hỏi tình trạng đơn', 'complaint': 'khiếu nại', 'return_request': 'xin đổi trả'}

MIN_MARGIN_PCT = 30.0     # Product Scout keeps candidates at or above this margin
RETURN_RATE_WARN = 0.10   # Finance flags a return rate above this
SHARE_DIGITS = 4


def _r(x, digits=2):
    return round(float(x), digits)


def _by_sku(items, sku):
    return next(i for i in items if i['sku'] == sku)


def _product(facts, sku):
    p = _by_sku(facts['products']['items'], sku)
    s = _by_sku(facts['suppliers']['items'], sku)
    return p, s


def _base(type_, agent_id, summary):
    return {'type': type_, 'agent_id': agent_id, 'summary': summary, 'synthetic': True}


def plan(facts, inputs, objective, graph):
    """01 Commander: execution plan = the task graph, in order, with constraints."""
    from app.core.registry import AGENTS, agent_for_task
    steps = [{'task_key': k, 'agent_id': agent_for_task(k), 'agent_name': AGENTS[agent_for_task(k)]['name'],
              'depends_on': list(deps)} for k, deps in graph.items()]
    return {**_base('execution_plan', '01', f'Kế hoạch {len(steps)} bước cho thị trường {facts["market"]["market"]}.'),
            'objective': objective, 'market': facts['market']['market'], 'steps': steps,
            'constraints': ['MOCK_ONLY: không kết nối hệ thống thật', 'Chiến dịch luôn ở trạng thái DRAFT',
                            'Không publish, không thanh toán, không gửi tin nhắn thật',
                            'Số liệu chỉ lấy từ Mock API']}


def market(facts, inputs):
    """02 Market Intelligence: funnel and rates from mock leads/orders."""
    leads, confirmed = facts['leads']['total'], facts['leads']['confirmed']
    delivered, returned = facts['orders']['delivered'], facts['orders']['returned']
    m = facts['market']
    return {**_base('market_report', '02', f'Phễu giả lập {m["market"]}: {leads} lead, {confirmed} xác nhận, '
                    f'{delivered} giao, {returned} hoàn.'),
            'market': m['market'], 'currency': m['currency'], 'demand_signal': m['demand_signal'],
            'funnel': {'leads': leads, 'confirmed': confirmed, 'delivered': delivered, 'returned': returned},
            'confirm_rate': _r(confirmed / leads, SHARE_DIGITS) if leads else 0.0,
            'delivery_rate': _r(delivered / confirmed, SHARE_DIGITS) if confirmed else 0.0,
            'return_rate': _r(returned / delivered, SHARE_DIGITS) if delivered else 0.0}


def product(facts, inputs):
    """03 Product Scout: margin per SKU. Select the SKU that has test-sale evidence (a mock campaign), because
    every funnel number downstream belongs to it; warn when its margin is below MIN_MARGIN_PCT. Without any
    evidence, pick the highest margin that passes, otherwise the highest margin."""
    ship, fee = facts['logistics']['shipping_php'], facts['finance']['payment_fee_php']
    evidence = {c['campaign_id'].removeprefix('CMP-') for c in facts['campaigns']['items']}
    cands = []
    for p in facts['products']['items']:
        s = _by_sku(facts['suppliers']['items'], p['sku'])
        margin = p['selling_price_php'] - s['unit_cost_php'] - ship - fee
        pct = _r(100 * margin / p['selling_price_php']) if p['selling_price_php'] else 0.0
        cands.append({'sku': p['sku'], 'name': p['name'], 'selling_price_php': p['selling_price_php'],
                      'unit_cost_php': s['unit_cost_php'], 'supplier': s['supplier'], 'lead_time_days': s['lead_time_days'],
                      'stock': p['stock'], 'margin_per_unit_php': _r(margin), 'margin_pct': pct,
                      'has_test_sale_data': p['sku'] in evidence, 'passes_margin': pct >= MIN_MARGIN_PCT})
    with_data = [c for c in cands if c['has_test_sale_data']]
    passing = sorted((c for c in cands if c['passes_margin']), key=lambda c: -c['margin_pct'])
    pick = (with_data or passing or sorted(cands, key=lambda c: -c['margin_pct']))[0]
    warnings = [] if pick['passes_margin'] else [f'{pick["sku"]}: biên {pick["margin_pct"]}% dưới ngưỡng {MIN_MARGIN_PCT:g}%']
    return {**_base('product_shortlist', '03', f'Chọn {pick["sku"]} ({pick["name"]}), biên {pick["margin_pct"]}%.'
                    + (' Cảnh báo biên thấp.' if warnings else '')),
            'candidates': cands, 'selected_sku': pick['sku'], 'warnings': warnings,
            'selection_rule': 'Ưu tiên SKU có dữ liệu bán thử (số liệu phễu thuộc về SKU đó), cảnh báo nếu biên < '
                              f'{MIN_MARGIN_PCT:g}%; không có dữ liệu thì chọn biên cao nhất đạt ngưỡng, rồi biên cao nhất.'}


def offer(facts, inputs):
    """04 Offer & Strategy: price, margin and break-even for the selected SKU."""
    sku = inputs['product']['selected_sku']
    p, s = _product(facts, sku)
    ship, fee = facts['logistics']['shipping_php'], facts['finance']['payment_fee_php']
    camp = next((c for c in facts['campaigns']['items'] if c['campaign_id'] == f'CMP-{sku}'), None)
    budget = camp['spend_php'] if camp else facts['ads']['budget_php']
    margin = p['selling_price_php'] - s['unit_cost_php'] - ship - fee
    breakeven = math.ceil(budget / margin) if margin > 0 else 0
    return {**_base('pricing_offer', '04', f'{sku}: giá {p["selling_price_php"]} PHP, biên {margin} PHP/đơn, '
                    f'hòa vốn {breakeven} đơn với ngân sách {budget} PHP.'),
            'sku': sku, 'selling_price_php': p['selling_price_php'], 'unit_cost_php': s['unit_cost_php'],
            'shipping_php': ship, 'payment_fee_php': fee, 'margin_per_unit_php': _r(margin),
            'margin_pct': _r(100 * margin / p['selling_price_php']), 'campaign_budget_php': budget,
            'breakeven_orders': breakeven, 'total_budget_php': facts['finance']['budget_php'], 'stock': p['stock']}


def content(facts, inputs):
    """05 Content & Creative: angles = pre-sale questions (lead-stage conversations); drafts reuse offer numbers."""
    o = inputs['offer']
    p, _ = _product(facts, o['sku'])
    days = facts['logistics']['delivery_days']
    intents = {}
    for c in facts['conversations']['items']:
        if c['stage'] != 'lead':
            continue
        intents[c['intent']] = intents.get(c['intent'], 0) + 1
    top = sorted(intents, key=lambda k: (-intents[k], k))[:3]
    drafts = [
        f'{p["name"]} — {o["selling_price_php"]} PHP. Delivery in {days} days.',
        f'Questions about shipping? Flat {o["shipping_php"]} PHP, arrives in {days} days.',
        f'Everyday style: {p["name"]} for {o["selling_price_php"]} PHP.',
    ]
    return {**_base('content_brief', '05', f'{len(drafts)} mẫu quảng cáo bản nháp cho {p["name"]}, khách thường {", ".join(INTENT_VN.get(t, t) for t in top)}.'),
            'sku': o['sku'], 'product_name': p['name'], 'angles': top, 'intent_counts': intents,
            'ad_drafts': drafts, 'status': 'DRAFT'}


def campaign(facts, inputs):
    """06 Campaign Operator: DRAFT campaign; the only write it asks for is a draft (gateway, Phase 5)."""
    o, c = inputs['offer'], inputs['content']
    cid = f'CMP-{o["sku"]}'
    budget = o['campaign_budget_php']
    return {**_base('campaign_plan', '06', f'Chiến dịch {cid} ở bản nháp, ngân sách {budget} PHP.'),
            'sku': o['sku'], 'campaign_id': cid, 'status': 'DRAFT', 'budget_php': budget,
            'budget_share_pct': _r(100 * budget / o['total_budget_php']) if o['total_budget_php'] else 0.0,
            'ad_draft_count': len(c['ad_drafts']), 'tracking_ok': facts['ads']['tracking_ok'],
            'requested_actions': [{'tool': 'meta_ads.create_draft', 'target': cid, 'budget_php': budget}]}


def leads(facts, inputs):
    """07 Lead & Sales: lead funnel costs; reply drafts for open lead-stage conversations."""
    cp = inputs['campaign']
    total, confirmed = facts['leads']['total'], facts['leads']['confirmed']
    open_convs = [c['conversation_id'] for c in facts['conversations']['items'] if c['stage'] == 'lead']
    spend = cp['budget_php']
    return {**_base('lead_report', '07', f'{total} lead, {confirmed} xác nhận; {len(open_convs)} hội thoại lead cần trả lời nháp.'),
            'sku': cp['sku'], 'leads': total, 'confirmed': confirmed, 'unconfirmed': total - confirmed,
            'confirm_rate': _r(confirmed / total, SHARE_DIGITS) if total else 0.0,
            'cost_per_lead_php': _r(spend / total) if total else 0.0,
            'cost_per_confirmed_php': _r(spend / confirmed) if confirmed else 0.0,
            'open_conversations': open_convs,
            'requested_actions': [{'tool': 'crm.reply_draft', 'target': cid} for cid in open_convs]}


def care(facts, inputs):
    """08 Customer Success: delivery status and after-sale tickets (complaints, returns)."""
    lr = inputs['leads']
    delivered, returned = facts['orders']['delivered'], facts['orders']['returned']
    tickets = [{'conversation_id': c['conversation_id'], 'intent': c['intent'], 'stage': c['stage']}
               for c in facts['conversations']['items'] if c['intent'] in ('complaint', 'return_request')]
    return {**_base('care_report', '08', f'{delivered} đơn đã giao, {returned} hoàn, {lr["confirmed"] - delivered} đang giao; '
                    f'{len(tickets)} ticket sau bán.'),
            'sku': lr['sku'], 'confirmed': lr['confirmed'], 'delivered': delivered, 'returned': returned,
            'in_transit': lr['confirmed'] - delivered, 'delivery_days': facts['logistics']['delivery_days'],
            'provider': facts['logistics']['provider'], 'tickets': tickets,
            'requested_actions': [{'tool': 'crm.ticket_note', 'target': t['conversation_id']} for t in tickets]}


def kpi(facts, inputs):
    """09 Sales Analyst: revenue, ROAS and CPA. Price comes from the SKU chosen upstream."""
    lr, cr = inputs['leads'], inputs['care']
    p, _ = _product(facts, cr['sku'])
    price = p['selling_price_php']
    spend = round(lr['cost_per_lead_php'] * lr['leads'], 2)  # same spend the lead report used
    net_units = cr['delivered'] - cr['returned']
    net_rev = net_units * price
    return {**_base('kpi_report', '09', f'ROAS {_r(net_rev / spend) if spend else 0.0}, CPA giao {_r(spend / cr["delivered"]) if cr["delivered"] else 0.0} PHP.'),
            'sku': cr['sku'], 'selling_price_php': price, 'ad_spend_php': spend,
            'gross_revenue_php': _r(cr['delivered'] * price), 'net_revenue_php': _r(net_rev), 'net_units': net_units,
            'roas': _r(net_rev / spend) if spend else 0.0,
            'cpa_confirmed_php': _r(spend / lr['confirmed']) if lr['confirmed'] else 0.0,
            'cpa_delivered_php': _r(spend / cr['delivered']) if cr['delivered'] else 0.0,
            'lead_to_delivered_rate': _r(cr['delivered'] / lr['leads'], SHARE_DIGITS) if lr['leads'] else 0.0,
            'return_rate': _r(cr['returned'] / cr['delivered'], SHARE_DIGITS) if cr['delivered'] else 0.0}


def finance(facts, inputs):
    """10 Finance & Risk: contribution after ads, budget use, rule-based risks (no LLM judgement)."""
    o, k = inputs['offer'], inputs['kpi']
    before = k['net_units'] * o['margin_per_unit_php']
    after = before - k['ad_spend_php']
    used = _r(100 * k['ad_spend_php'] / o['total_budget_php']) if o['total_budget_php'] else 0.0
    risks = []
    if o['margin_per_unit_php'] <= 0:
        risks.append('Biên lợi nhuận âm hoặc bằng 0: mỗi đơn đều lỗ')
    if k['net_units'] < o['breakeven_orders']:
        risks.append(f'Chưa hòa vốn: {k["net_units"]} đơn ròng < {o["breakeven_orders"]} đơn cần')
    if k['return_rate'] > RETURN_RATE_WARN:
        risks.append(f'Tỷ lệ hoàn {k["return_rate"]:.2%} vượt ngưỡng {RETURN_RATE_WARN:.0%}')
    if k['net_units'] > o['stock']:
        risks.append('Số đơn vượt tồn kho')
    level = 'HIGH' if (o['margin_per_unit_php'] <= 0 or after < 0) else ('MEDIUM' if risks else 'LOW')
    rec = {'HIGH': 'Giữ chiến dịch ở DRAFT, cần người duyệt và thêm dữ liệu trước khi mở rộng',
           'MEDIUM': 'Có thể thử nghiệm tiếp ở quy mô nhỏ, theo dõi các rủi ro đã nêu',
           'LOW': 'Đủ điều kiện đề xuất mở rộng, vẫn cần người duyệt'}[level]
    return {**_base('finance_risk_report', '10', f'Lợi nhuận sau quảng cáo {_r(after)} PHP, rủi ro {RISK_VN[level]}.'),
            'sku': o['sku'], 'margin_per_unit_php': o['margin_per_unit_php'], 'net_units': k['net_units'],
            'contribution_before_ads_php': _r(before), 'contribution_after_ads_php': _r(after),
            'breakeven_orders': o['breakeven_orders'], 'budget_used_pct': used, 'risks': risks,
            'risk_level': level, 'recommendation': rec}


def summary(objective, arts):
    """01 Commander: final summary. `arts` = every COMPLETED artifact of the run by task_key (Commander
    holds SUPERVISE), so key numbers are copied from the agents that computed them, never recomputed."""
    missing = {'status': 'NOT_RUN'}
    qa, au, mo = (arts.get(k, missing) for k in ('qa', 'audit', 'monitor'))
    o, k, f = arts.get('offer', {}), arts.get('kpi', {}), arts.get('finance', {})
    ok = all(x['status'] in ('PASS', 'WARN') for x in (qa, au, mo))  # WARN is recorded, only FAIL/NOT_RUN blocks
    # NEEDS_REVIEW: a supervisor reported FAIL (or did not run). HOLD_DRAFT: checks pass but Finance says the plan loses
    # money (risk HIGH) -> keep everything DRAFT for a human. DRAFT_READY: drafts ready for human approval.
    decision = 'NEEDS_REVIEW' if not ok else ('HOLD_DRAFT' if f.get('risk_level') == 'HIGH' else 'DRAFT_READY')
    sku_txt = o.get('sku') or 'chưa có (Offer chưa hoàn thành)'
    risk_txt = f.get('risk_level') or 'chưa đánh giá'
    return {**_base('final_summary', '01', f'Kết luận: {DECISION_VN[decision]}. SKU {sku_txt}, rủi ro {RISK_VN.get(f.get("risk_level"), risk_txt)}.'),
            'objective': objective, 'sku': o.get('sku', ''), 'decision': decision,
            'key_numbers': {'selling_price_php': o.get('selling_price_php'), 'margin_per_unit_php': o.get('margin_per_unit_php'),
                            'breakeven_orders': o.get('breakeven_orders'), 'roas': k.get('roas'),
                            'contribution_after_ads_php': f.get('contribution_after_ads_php'),
                            'risk_level': f.get('risk_level')},
            'supervision': {'qa': qa['status'], 'audit': au['status'], 'monitor': mo['status']},
            'next_steps': {'NEEDS_REVIEW': ['Xử lý các phát hiện của QA/Audit/Monitor', 'Chạy lại agent liên quan'],
                           'HOLD_DRAFT': ['Giữ chiến dịch DRAFT, không mở rộng', 'Người duyệt xem rủi ro Finance & Risk',
                                          'Thu thêm dữ liệu bán thử hoặc điều chỉnh giá/chi phí'],
                           'DRAFT_READY': ['Người duyệt xem Finance & Risk trước khi mở rộng', 'Chiến dịch giữ DRAFT đến khi được duyệt']}[decision]}
