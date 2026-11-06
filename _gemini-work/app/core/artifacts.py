"""Artifact schemas: the hand-off contract between agents (DEMO_ONLY P4). Extra fields are allowed;
listed fields are required and type-checked. Workflow rejects an artifact that fails validation."""
from pydantic import BaseModel, ConfigDict, ValidationError, create_model

_COMMON = {'type': str, 'agent_id': str, 'summary': str, 'synthetic': bool}

SPEC = {
    'execution_plan': {'objective': str, 'market': str, 'steps': list, 'constraints': list},
    'market_report': {'market': str, 'currency': str, 'demand_signal': str, 'funnel': dict,
                      'confirm_rate': float, 'delivery_rate': float, 'return_rate': float},
    'product_shortlist': {'candidates': list, 'selected_sku': str, 'selection_rule': str},
    'pricing_offer': {'sku': str, 'selling_price_php': float, 'unit_cost_php': float, 'shipping_php': float,
                      'payment_fee_php': float, 'margin_per_unit_php': float, 'margin_pct': float,
                      'campaign_budget_php': float, 'breakeven_orders': int, 'total_budget_php': float, 'stock': int},
    'content_brief': {'sku': str, 'product_name': str, 'angles': list, 'ad_drafts': list, 'status': str},
    'campaign_plan': {'sku': str, 'campaign_id': str, 'status': str, 'budget_php': float,
                      'budget_share_pct': float, 'ad_draft_count': int, 'requested_actions': list},
    'lead_report': {'sku': str, 'leads': int, 'confirmed': int, 'unconfirmed': int, 'confirm_rate': float,
                    'cost_per_lead_php': float, 'cost_per_confirmed_php': float, 'open_conversations': list,
                    'requested_actions': list},
    'care_report': {'sku': str, 'confirmed': int, 'delivered': int, 'returned': int, 'in_transit': int,
                    'delivery_days': int, 'provider': str, 'tickets': list, 'requested_actions': list},
    'kpi_report': {'sku': str, 'selling_price_php': float, 'ad_spend_php': float, 'gross_revenue_php': float,
                   'net_revenue_php': float, 'net_units': int, 'roas': float, 'cpa_confirmed_php': float,
                   'cpa_delivered_php': float, 'lead_to_delivered_rate': float, 'return_rate': float},
    'finance_risk_report': {'sku': str, 'margin_per_unit_php': float, 'net_units': int,
                            'contribution_before_ads_php': float, 'contribution_after_ads_php': float,
                            'breakeven_orders': int, 'budget_used_pct': float, 'risks': list, 'risk_level': str,
                            'recommendation': str},
    'qa_report': {'checked': list, 'status': str, 'findings': list},
    'audit_report': {'actions': list, 'status': str, 'findings': list},
    'monitoring_report': {'tasks': list, 'status': str, 'findings': list, 'llm_calls': int, 'tokens': int},
    'final_summary': {'objective': str, 'sku': str, 'decision': str, 'key_numbers': dict,
                      'supervision': dict, 'next_steps': list},
}

_MODELS = {name: create_model(name, __config__=ConfigDict(extra='allow', strict=False),
                              **{k: (t, ...) for k, t in {**_COMMON, **fields}.items()})
           for name, fields in SPEC.items()}


def validate(payload: dict) -> list:
    """[] when valid, otherwise readable error strings. Unknown artifact type is an error."""
    model: type[BaseModel] | None = _MODELS.get(payload.get('type')) if isinstance(payload, dict) else None
    if model is None:
        return [f'unknown artifact type {payload.get("type") if isinstance(payload, dict) else payload!r}']
    try:
        model.model_validate(payload)
        return []
    except ValidationError as exc:
        return [f'{".".join(map(str, e["loc"]))}: {e["msg"]}' for e in exc.errors()]
