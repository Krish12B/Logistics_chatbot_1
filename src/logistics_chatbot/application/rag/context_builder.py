"""Context formatting utilities for grounding LLM prompts in retrieved facts."""
from __future__ import annotations

from typing import Any, Dict

from logistics_chatbot.domain.entities.models import RetrievedContext


def format_shipment(shipment: dict) -> str:
    """Turn a legacy shipment database row (dict) into plain text for the LLM."""
    return "\n".join([
        f"Shipment ID: {shipment['shipment_id']}",
        f"Status: {shipment['status']}",
        f"Origin: {shipment['origin']}",
        f"Destination: {shipment['destination']}",
        f"Current location: {shipment.get('current_location') or 'Unknown'}",
        f"Route: {shipment.get('route') or 'Not available'}",
        f"Estimated delivery: {shipment.get('estimated_delivery') or 'Not available'}",
        f"Delay reason: {shipment.get('delay_reason') or 'None'}",
        f"Customs status: {shipment.get('customs_status') or 'Unknown'}",
        f"Last updated: {shipment.get('last_updated') or 'Unknown'}",
    ])


def format_enterprise_shipment_context(ent: Dict[str, Any]) -> str:
    """Serialize all verified relational fields of an enterprise booking for grounded hybrid RAG."""
    ai_feat = ent.get("ai_features") or {}
    ai_inf = ent.get("ai_inference") or {}
    alerts = ent.get("alerts") or []
    alert_summary = "; ".join(
        f"[{a.get('severity', 'Info')}] {a.get('alert_type', 'Alert')} ({a.get('alert_status', '')}): {a.get('recommended_action', '')}"
        for a in alerts[:3]
    ) or "None"

    delay_txt = (
        f"Delayed (+{ent.get('delay_days', 0)} days beyond expected)"
        if ent.get("is_delayed")
        else f"Delivered ({ent.get('derived_status', 'Delivered')})"
    )

    lines = [
        f"Booking Reference: {ent['booking_id']} (UUID: {ent['shipment_id']})",
        f"Derived Status (from Shipment_Delivery_History): {delay_txt}",
        f"Customer: {ent.get('customer_name')} ({ent.get('customer_type')}, {ent.get('industry')}, {ent.get('customer_city')}, {ent.get('customer_country')})",
        f"Product / Cargo: {ent.get('product_name')} | Category: {ent.get('product_category')} | HS Code: {ent.get('hs_code')} | Supplier: {ent.get('supplier_name')}",
        f"Cargo Flags: Hazardous={ent.get('product_hazardous')}, Perishable={ent.get('product_perishable')}, Temp-Controlled={ent.get('temperature_controlled')}, Fragile={ent.get('fragile')}, Insurance={ent.get('insurance')}",
        f"Mode & Type: {ent.get('shipping_mode')} ({ent.get('shipment_type')}), Priority={ent.get('priority')}, Weight={ent.get('weight_kg')} kg, Volume={ent.get('volume_cbm')} CBM, Declared Value=${ent.get('declared_value')}",
        f"Carrier: {ent.get('carrier_name')} ({ent.get('carrier_type')}, Rating={ent.get('carrier_rating')}/5.0, Fleet={ent.get('fleet_size')}, HQ={ent.get('carrier_hq')})",
        f"Vehicle: {ent.get('vehicle_number')} ({ent.get('vehicle_type')}, Maintenance={ent.get('maintenance_status')}, Fuel={ent.get('fuel_type')})",
        f"Origin Warehouse: {ent.get('warehouse_name')} ({ent.get('warehouse_city')}, Type={ent.get('warehouse_type')}, Utilization={ent.get('current_utilization')}%)",
        f"Route: {ent.get('origin_city')}, {ent.get('origin_country')} ({ent.get('origin_port')}) -> {ent.get('destination_city')}, {ent.get('destination_country')} ({ent.get('destination_port')})",
        f"Route Risk Metrics: Distance={ent.get('distance_km')} km, Avg Transit={ent.get('average_transit_days')} days, Risk={ent.get('route_risk')}, Traffic Index={ent.get('traffic_index')}",
        f"Weather Forecast ({ent.get('weather_city')}, {ent.get('forecast_date')}): {ent.get('weather_condition')}, Temp={ent.get('temperature')}C, Wind={ent.get('wind_speed')} km/h, Rainfall={ent.get('rainfall')} mm, Visibility={ent.get('visibility')} km",
        f"Customs: Required={ent.get('customs_required')}, Documentation Complete={ent.get('documentation_complete')}, Inspection Required={ent.get('inspection_required')}, Cargo Class={ent.get('cargo_type')}, Dest Country={ent.get('customs_destination_country')}",
        f"Schedule & Delivery History: Booked={ent.get('booking_date')}, Shipped={ent.get('ship_date')}, Expected={ent.get('expected_delivery_date')}, Actual={ent.get('actual_delivery_date')}, Attempts={ent.get('delivery_attempts')}",
        "Incoterm Field: Not stored on this shipment booking record.",
    ]
    if ai_feat or ai_inf:
        lines.append(
            f"AI Risk Telemetry: Route Delay Rate={ai_feat.get('route_delay_rate', 'N/A')}%, "
            f"Carrier Reliability={ai_feat.get('carrier_reliability_score', 'N/A')}, "
            f"Weather Severity={ai_feat.get('weather_severity_score', 'N/A')}, "
            f"Predicted Delay Prob={ai_inf.get('delay_probability', 'N/A')} ({ai_inf.get('risk_category', 'N/A')})"
        )
    lines.append(f"Monitoring Alerts: {alert_summary}")
    return "\n".join(lines)


def format_context(ctx: RetrievedContext) -> str:
    """Convert RetrievedContext into a structured text block for the LLM."""
    sections: list[str] = []

    if ctx.shipment:
        sections.append("SHIPMENT RECORD:\n" + format_shipment(ctx.shipment))

    if ctx.shipment_list is not None:
        if ctx.shipment_list:
            lines = [f"SHIPMENT LIST ({len(ctx.shipment_list)} total, filter: {ctx.filter_description}):"]
            for s in ctx.shipment_list:
                line = (
                    f"  - {s['shipment_id']}: {s['status']} from {s['origin']} "
                    f"to {s['destination']}, eta: {s.get('estimated_delivery') or 'N/A'}"
                )
                if s.get("delay_reason"):
                    line += f" (delayed: {s['delay_reason']})"
                lines.append(line)
            sections.append("\n".join(lines))
        else:
            sections.append(f"SHIPMENT LIST: No shipments found matching {ctx.filter_description}.")

    if ctx.knowledge_articles:
        lines = ["KNOWLEDGE BASE:"]
        for a in ctx.knowledge_articles:
            doc_id = a.get("doc_id", "DOC")
            title = a.get("section_title", "")
            content = a.get("content", "")
            lines.append(f"[{doc_id}] {title}\n{content}")
        sections.append("\n\n".join(lines))

    return "\n\n".join(sections)
