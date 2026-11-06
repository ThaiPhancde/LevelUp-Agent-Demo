"""Agent Registry: one entry per role (DEMO_ONLY A.1). Permissions follow DEMO_PLAN.md section 5.

READ           read Mock API data
WRITE_DRAFT    create DRAFT objects in a mock system (campaign draft, reply draft, ticket note)
WRITE_EXTERNAL publish / pay / send for real — granted to nobody; Audit blocks it (Phase 5)
SUPERVISE      read run evidence (artifacts, decision_log, llm_calls)
"""

READ, WRITE_DRAFT, WRITE_EXTERNAL, SUPERVISE = 'READ', 'WRITE_DRAFT', 'WRITE_EXTERNAL', 'SUPERVISE'

AGENTS = {
    '01': {'name': 'Sales Director / Commander', 'group': 'business', 'tasks': ['plan', 'summary'],
           'responsibility': 'Phân rã mục tiêu, giao việc, tổng hợp báo cáo cuối',
           'tools': ['workflow.plan'], 'permissions': [READ, SUPERVISE],
           'outputs': ['execution_plan', 'final_summary']},
    '02': {'name': 'Market Intelligence', 'group': 'business', 'tasks': ['market'],
           'responsibility': 'Phân tích thị trường giả lập từ mock market/ads/leads',
           'tools': ['mock.market', 'mock.meta_ads', 'mock.leads', 'mock.orders'], 'permissions': [READ],
           'outputs': ['market_report']},
    '03': {'name': 'Product Scout', 'group': 'business', 'tasks': ['product'],
           'responsibility': 'So sánh sản phẩm và nhà cung cấp giả lập, chọn sản phẩm',
           'tools': ['mock.products', 'mock.suppliers', 'mock.logistics', 'mock.finance'], 'permissions': [READ],
           'outputs': ['product_shortlist']},
    '04': {'name': 'Offer & Strategy', 'group': 'business', 'tasks': ['offer'],
           'responsibility': 'Tính giá bán, biên lợi nhuận, điểm hòa vốn',
           'tools': ['mock.campaigns', 'mock.finance'], 'permissions': [READ],
           'outputs': ['pricing_offer']},
    '05': {'name': 'Content & Creative', 'group': 'business', 'tasks': ['content'],
           'responsibility': 'Tạo content brief và mẫu quảng cáo DRAFT',
           'tools': ['mock.customer_conversations'], 'permissions': [READ],
           'outputs': ['content_brief']},
    '06': {'name': 'Campaign Operator', 'group': 'business', 'tasks': ['campaign'],
           'responsibility': 'Lập chiến dịch quảng cáo DRAFT, không bao giờ publish',
           'tools': ['mock.campaigns', 'meta_ads.create_draft'], 'permissions': [READ, WRITE_DRAFT],
           'outputs': ['campaign_plan']},
    '07': {'name': 'Lead & Sales', 'group': 'business', 'tasks': ['leads'],
           'responsibility': 'Xử lý lead giả lập, soạn câu trả lời nháp',
           'tools': ['mock.leads', 'mock.customer_conversations', 'crm.reply_draft'], 'permissions': [READ, WRITE_DRAFT],
           'outputs': ['lead_report']},
    '08': {'name': 'Customer Success', 'group': 'business', 'tasks': ['care'],
           'responsibility': 'Chăm sóc sau bán, theo dõi giao hàng và đổi trả giả lập',
           'tools': ['mock.orders', 'mock.logistics', 'mock.customer_conversations', 'crm.ticket_note'],
           'permissions': [READ, WRITE_DRAFT], 'outputs': ['care_report']},
    '09': {'name': 'Sales Analyst', 'group': 'business', 'tasks': ['kpi'],
           'responsibility': 'Tính KPI: tỷ lệ chuyển đổi, CPA, ROAS',
           'tools': ['mock.campaigns', 'mock.products'], 'permissions': [READ], 'outputs': ['kpi_report']},
    '10': {'name': 'Finance & Risk', 'group': 'business', 'tasks': ['finance'],
           'responsibility': 'Phân tích lợi nhuận, ngân sách và rủi ro',
           'tools': ['mock.finance'], 'permissions': [READ], 'outputs': ['finance_risk_report']},
    '11': {'name': 'QA Tester', 'group': 'supervisory', 'tasks': ['qa'],
           'responsibility': 'Kiểm tra đầu ra: schema, phép tính, nhất quán số liệu',
           'tools': ['engine.qa'], 'permissions': [READ, SUPERVISE], 'outputs': ['qa_report']},
    '12': {'name': 'Auditor', 'group': 'supervisory', 'tasks': ['audit'],
           'responsibility': 'Kiểm tra quyền, hành động WRITE, phê duyệt và lịch sử',
           'tools': ['engine.audit'], 'permissions': [READ, SUPERVISE], 'outputs': ['audit_report']},
    '13': {'name': 'Monitor', 'group': 'supervisory', 'tasks': ['monitor'],
           'responsibility': 'Theo dõi thời gian, lần thử, lỗi, token',
           'tools': ['engine.monitor'], 'permissions': [READ, SUPERVISE], 'outputs': ['monitoring_report']},
}

# Tool name -> permission it needs. Anything not listed is treated as WRITE_EXTERNAL (deny by default).
TOOL_PERMISSION = {
    'meta_ads.create_draft': WRITE_DRAFT,
    'crm.reply_draft': WRITE_DRAFT,
    'crm.ticket_note': WRITE_DRAFT,
    'meta_ads.publish': WRITE_EXTERNAL,
    'payment.charge': WRITE_EXTERNAL,
    'messaging.send': WRITE_EXTERNAL,
}


def agent_for_task(task_key: str) -> str:
    return next(aid for aid, a in AGENTS.items() if task_key in a['tasks'])


def required_permission(tool: str) -> str:
    if tool.startswith('mock.') or tool.startswith('engine.') or tool == 'workflow.plan':
        return READ
    return TOOL_PERMISSION.get(tool, WRITE_EXTERNAL)


def allowed(agent_id: str, tool: str) -> bool:
    """Pure permission check: the agent holds the permission the tool needs. WRITE_EXTERNAL is never held."""
    need = required_permission(tool)
    return need != WRITE_EXTERNAL and need in AGENTS.get(agent_id, {}).get('permissions', ())


def public() -> list:
    return [{'id': aid, **{k: a[k] for k in ('name', 'group', 'responsibility', 'tasks', 'tools', 'permissions', 'outputs')}}
            for aid, a in AGENTS.items()]
