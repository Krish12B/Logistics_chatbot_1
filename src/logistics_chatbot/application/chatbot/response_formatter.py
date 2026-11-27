"""Markdown response formatting and verified source attribution helpers."""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

from logistics_chatbot.core.constants import DOCUMENT_DISPLAY_MAP, STATUS_EMOJI_MAP
from logistics_chatbot.domain.entities.models import ChatResult
from logistics_chatbot.utils.helpers import format_display_date


def map_source_display(source_id: str) -> str:
    """Map raw internal document IDs into human-readable titles while preserving IDs."""
    sid = str(source_id).strip()
    if sid.startswith("Enterprise "):
        return sid
    if sid.startswith("SHP-") or ("shipment" in sid.lower() and "pdf" not in sid.lower()):
        clean_id = re.search(r"SHP-\d+", sid)
        shp_str = clean_id.group(0) if clean_id else sid
        return f"Shipment Database Record ({shp_str})"
    if sid.startswith("EMP-") or "employee" in sid.lower():
        clean_id = re.search(r"EMP-\d+", sid)
        emp_str = clean_id.group(0) if clean_id else sid
        return f"Employee Directory Roster ({emp_str})"
    if sid in DOCUMENT_DISPLAY_MAP:
        return DOCUMENT_DISPLAY_MAP[sid]
    if "CUSTOMS" in sid or sid in ("PL-0010", "GL-0069", "DC-0030", "DC-0029"):
        return f"Customs & Regulatory Policy ({sid})"
    if "DELAY" in sid or sid in ("LC-0003",):
        return f"Shipment Delay & Exception Policy ({sid})"
    if "STATUS" in sid or sid.startswith("SS-"):
        return f"Logistics Tracking & Status Guide ({sid})"
    if "PHARMA" in sid or "531F90" in sid:
        return f"Cold-Chain Pharmaceutical Policy ({sid})"
    if sid.startswith("DC-"):
        return f"Documentation Standard Operating Procedure ({sid})"
    if sid.startswith("CM-"):
        return f"Commodity Handling Guidelines ({sid})"
    if sid.startswith("GL-"):
        return f"Logistics Terminology & Glossary ({sid})"
    if sid.startswith("LW-") or sid.startswith("SP-"):
        return f"Logistics Workflow & Order Lifecycle ({sid})"
    if sid.startswith("DOC-"):
        return f"Uploaded Knowledge Document ({sid})"
    if sid.startswith("FAQ-"):
        return f"Standard Operating Procedure ({sid})"
    return f"Verified Knowledge Document ({sid})"


def clean_citation_brackets(text: str) -> str:
    """Remove raw bracket tokens like [DOC-XXXX] or [FAQ-XXXX] from the prose body."""
    cleaned = re.sub(r"\s*\(\[[A-Za-z0-9_\-]+\]\)", "", text)
    cleaned = re.sub(r"\s*\[[A-Za-z0-9_\-]+\]", "", cleaned)
    cleaned = re.sub(r" {2,}", " ", cleaned)
    return cleaned.strip()


def build_shipment_status_report(shipment: dict, query_lower: str) -> str:
    """Construct concise shipment tracking report: status header, overview table, and progress."""
    sid = shipment["shipment_id"]
    status_raw = shipment.get("status") or "In Transit"
    status_emoji = STATUS_EMOJI_MAP.get(status_raw.lower(), f"🔵 {status_raw}")
    curr_loc = shipment.get("current_location") or "In Transit"
    origin = shipment.get("origin") or "Origin"
    dest = shipment.get("destination") or "Destination"
    eta = format_display_date(shipment.get("estimated_delivery"))
    updated = format_display_date(shipment.get("last_updated"))
    route = shipment.get("route") or f"{origin} -> {dest}"
    delay_reason = shipment.get("delay_reason")
    customs_status = shipment.get("customs_status")

    stops = [s.strip() for s in route.split("->")]
    origin_name = stops[0] if stops else origin
    dest_name = stops[-1] if stops else dest
    is_location_query = any(w in query_lower for w in ("location", "where is", "where's", "where"))

    if is_location_query:
        header = f"# 📍 Shipment Location – {sid}\n\n**Current Location:** 📍 {curr_loc}\n**Current Status:** {status_emoji}"
    else:
        header = f"# 📦 Shipment Status – {sid}\n\n**Current Status:** {status_emoji}"

    overview_rows = [
        f"| Shipment ID | {sid} |",
        f"| Current Location | {curr_loc} |",
        f"| Origin | {origin} |",
        f"| Destination | {dest} |",
        f"| Estimated Delivery | {eta} |",
        f"| Last Updated | {updated} |",
    ]
    if customs_status:
        overview_rows.append(f"| Customs Status | {customs_status} |")
    if delay_reason:
        overview_rows.append(f"| Delay Reason | {delay_reason} |")

    overview = (
        "### 1. Shipment Overview\n\n"
        "| Field | Details |\n"
        "|---|---|\n"
        + "\n".join(overview_rows)
    )

    progress_lines = [
        "- Origin processing: Completed",
        f"- Departure from {origin_name}: Completed",
    ]

    curr_idx = -1
    for idx, stop in enumerate(stops):
        if curr_loc.lower() in stop.lower() or stop.lower() in curr_loc.lower():
            curr_idx = idx
            break

    if len(stops) > 2:
        for idx, stop in enumerate(stops[1:-1], start=1):
            if "delivered" in status_raw.lower():
                progress_lines.append(f"- Transit through {stop}: Completed")
            elif curr_idx != -1 and idx < curr_idx:
                progress_lines.append(f"- Transit through {stop}: Completed")
            elif curr_idx == idx:
                if delay_reason:
                    progress_lines.append(f"- Transit through {stop}: Delayed ({delay_reason})")
                elif "customs" in status_raw.lower():
                    progress_lines.append(f"- Transit through {stop}: On Hold (Customs Inspection)")
                elif "out for delivery" in status_raw.lower():
                    progress_lines.append(f"- Transit through {stop}: In Progress (Out for Delivery)")
                else:
                    progress_lines.append(f"- Transit through {stop}: In Progress")
            else:
                progress_lines.append(f"- Transit through {stop}: Pending")
    elif curr_loc and curr_loc not in (origin_name, dest_name):
        if "delivered" in status_raw.lower():
            progress_lines.append(f"- Transit through {curr_loc}: Completed")
        elif "out for delivery" in status_raw.lower():
            progress_lines.append(f"- Transit through {curr_loc}: In Progress (Out for Delivery)")
        elif delay_reason:
            progress_lines.append(f"- Transit through {curr_loc}: Delayed ({delay_reason})")
        else:
            progress_lines.append(f"- Transit through {curr_loc}: In Progress")

    if "delivered" in status_raw.lower():
        progress_lines.append(f"- Arrival at {dest_name}: Completed")
        progress_lines.append("- Final delivery: Completed")
    else:
        progress_lines.append(f"- Arrival at {dest_name}: Pending")
        progress_lines.append("- Final delivery: Pending")

    return f"{header}\n\n{overview}\n\n### 2. Shipment Progress\n\n" + "\n".join(progress_lines)


def build_operational_status_report(ops: Dict[str, Any]) -> str:
    """Construct structured OPERATIONAL RECORD card."""
    doc_id = ops.get("doc_id", "N/A")
    category = ops.get("category", "operational_case").replace("_", " ").title()
    title = ops.get("section_title") or f"Operational Case {doc_id}"
    status = ops.get("status", "Active")
    origin = ops.get("origin", "N/A")
    destination = ops.get("destination", "N/A")
    assigned = ops.get("assigned_employee", "Operations Coordinator (Dispatch Desk)")
    dept = ops.get("responsible_department", category)
    last_updated = ops.get("last_updated", "N/A")
    risk = ops.get("risk_factors", "Standard monitoring")
    content = ops.get("content", "")

    status_lower = status.lower()
    if "awaiting" in status_lower or "pending" in status_lower:
        status_badge = f"🟡 {status}"
    elif "transit" in status_lower or "active" in status_lower:
        status_badge = f"🟢 {status}"
    elif "delay" in status_lower or "hold" in status_lower or "exception" in status_lower:
        status_badge = f"🔴 {status}"
    else:
        status_badge = f"⚪ {status}"

    location_str = f"{origin} → {destination}"
    if origin != "N/A":
        location_str += f" (Current Facility: {origin} Hub)"

    report = (
        f"# 📋 OPERATIONAL RECORD\n\n"
        f"**Case Title:** {title}\n\n"
        f"- **Record ID:** `{doc_id}`\n"
        f"- **Current Status:** {status_badge}\n"
        f"- **Responsible Department:** {dept}\n"
        f"- **Assigned Employee:** {assigned}\n"
        f"- **Current Location:** {location_str}\n"
        f"- **Last Updated:** {last_updated}\n"
    )

    details = []
    if risk and risk != "N/A":
        details.append(f"**Key Risk Identified:** {risk}.")

    if "coordinator should" in content.lower():
        m = re.search(r"(The coordinator should [^.]+\.)", content, re.IGNORECASE)
        if m:
            details.append(f"**Protocol:** {m.group(1)}")
    elif content:
        first_sentence = content.split(".")[0].strip()
        if first_sentence:
            details.append(f"{first_sentence}.")

    if details:
        report += f"- **Additional Details:** {' '.join(details)}\n"
    return report


def build_employee_profile_report(emp: Dict[str, Any]) -> str:
    """Format an employee database record into a structured Markdown card."""
    return (
        f"# 👤 Employee Profile – {emp['employee_id']}\n\n"
        f"**Personnel Record:** {emp['full_name']} ({emp['job_title']})\n\n"
        f"### 1. Operations Overview\n\n"
        f"| Field | Details |\n"
        f"|---|---|\n"
        f"| Employee ID | {emp['employee_id']} |\n"
        f"| Full Name | {emp['full_name']} |\n"
        f"| Department | {emp['department']} |\n"
        f"| Job Title | {emp['job_title']} |\n"
        f"| Assigned Hub | {emp['assigned_hub']} |\n"
        f"| Shift Rotation | {emp['shift']} |\n"
        f"| Certification | {emp.get('certification') or 'Standard Operations Certified'} |\n"
        f"| Operational Status | {emp.get('status', 'Active')} |\n\n"
        f"### 2. Contact & Internal Routing\n\n"
        f"- **Corporate Email:** `{emp['email']}`\n"
        f"- **VoIP Extension:** `{emp.get('phone_extension', 'x4000')}`\n"
        f"- **Dispatch Desk:** Reachable through {emp['assigned_hub']} operations center."
    )


def build_shipment_aggregate_report(
    query: str,
    counts: dict[str, int],
    status_filter: Optional[str] = None,
    location_filter: Optional[str] = None,
    origin_filter: Optional[str] = None,
    destination_filter: Optional[str] = None,
    corridor_origin_count: Optional[int] = None,
    corridor_destination_count: Optional[int] = None,
) -> ChatResult:
    """Construct an authoritative aggregate shipment metrics report grounded strictly in DB counts."""
    q = query.lower()
    total = sum(counts.values())

    if not status_filter:
        if "in transit" in q:
            status_filter = "In Transit"
        elif "delivered" in q:
            status_filter = "Delivered"
        elif "delayed" in q:
            status_filter = "Delayed"
        elif "customs" in q or "on hold" in q:
            status_filter = "On Hold - Customs"
        elif "out for delivery" in q:
            status_filter = "Out for Delivery"
        elif "pending" in q:
            status_filter = "Pending"

    status_emojis = {
        "In Transit": "🟡 In Transit",
        "Delivered": "🟢 Delivered",
        "Delayed": "🔴 Delayed",
        "On Hold - Customs": "🟠 On Hold - Customs",
        "Out for Delivery": "🚚 Out for Delivery",
        "Pending": "⚪ Pending",
        "Cancelled": "⚫ Cancelled",
    }

    has_scope = bool(location_filter or origin_filter or destination_filter)

    if has_scope:
        scope_parts = []
        if status_filter:
            scope_parts.append(f"in **{status_filter}** status")
        if origin_filter and destination_filter:
            scope_parts.append(f"from **{origin_filter}** to **{destination_filter}**")
        elif origin_filter:
            scope_parts.append(f"originating from **{origin_filter}**")
        elif destination_filter:
            scope_parts.append(f"bound for **{destination_filter}**")
        elif location_filter:
            scope_parts.append(f"located in **{location_filter}**")
        scope_desc = " ".join(scope_parts)

        title_loc = (
            f"{origin_filter} -> {destination_filter}"
            if (origin_filter and destination_filter)
            else (origin_filter or destination_filter or location_filter or "Filtered Scope")
        )

        corridor_prefix = f"Corridor Reference Totals ({status_filter}) for {location_filter}" if status_filter else f"Corridor Reference Totals for {location_filter}"

        if total == 0:
            corridor_note = ""
            if location_filter and (corridor_origin_count or corridor_destination_count):
                corridor_note = (
                    f"\n\n*({corridor_prefix}: "
                    f"**{corridor_origin_count or 0:,}** originating from {location_filter} · "
                    f"**{corridor_destination_count or 0:,}** bound for {location_filter}.)*"
                )
            body = (
                f"# 📊 Real-Time Shipment Count – {title_loc}\n\n"
                f"There are currently **0 shipments** {scope_desc} recorded in the FleetHarbor tracking database."
                f"{corridor_note}"
            )
            return ChatResult(
                response=body,
                sources=["Shipment Database Registry (Filtered Query: 0 Matches)"],
                response_type="shipment_aggregate",
                shipment_id=None,
                structured_data={
                    "status_counts": counts,
                    "total": 0,
                    "filter": status_filter,
                    "location": location_filter,
                    "origin": origin_filter,
                    "destination": destination_filter,
                },
            )

        ordered_keys = ["In Transit", "Delivered", "Delayed", "On Hold - Customs", "Out for Delivery"]
        table_rows = []
        for k in ordered_keys:
            if k in counts and counts[k] > 0:
                cnt = counts[k]
                pct = (cnt / total) * 100.0
                label = status_emojis.get(k, k)
                table_rows.append(f"| {label} | **{cnt:,}** | {pct:.1f}% |")
        for k, cnt in counts.items():
            if k not in ordered_keys and cnt > 0:
                pct = (cnt / total) * 100.0
                table_rows.append(f"| {status_emojis.get(k, k)} | **{cnt:,}** | {pct:.1f}% |")
        table_rows.append(f"| **Total Matching Shipments** | **{total:,}** | **100.0%** |")
        table_md = "| Lifecycle Status | Matching Shipments | Share |\n|---|---|---|\n" + "\n".join(table_rows)

        corridor_line = ""
        if location_filter and corridor_origin_count is not None and corridor_destination_count is not None:
            corridor_line = (
                f"\n- **{corridor_prefix}:** "
                f"**{corridor_origin_count:,}** originating from {location_filter} · "
                f"**{corridor_destination_count:,}** bound for {location_filter}\n"
            )

        body = (
            f"# 📊 Real-Time Shipment Count – {title_loc}\n\n"
            f"There are currently **{total:,} shipments** {scope_desc} in the FleetHarbor tracking database.\n\n"
            f"### Status Breakdown\n\n{table_md}\n"
            f"{corridor_line}\n"
            f"To inspect a specific shipment in this group, ask by its tracking ID (e.g. `Status of SHP-10001`)."
        )
        return ChatResult(
            response=body,
            sources=[f"Shipment Database Registry ({total:,} Matching Shipments)"],
            response_type="shipment_aggregate",
            shipment_id=None,
            structured_data={
                "status_counts": counts,
                "total": total,
                "filter": status_filter,
                "location": location_filter,
                "origin": origin_filter,
                "destination": destination_filter,
                "corridor_origin_count": corridor_origin_count,
                "corridor_destination_count": corridor_destination_count,
            },
        )

    ordered_keys = ["In Transit", "Delivered", "Delayed", "On Hold - Customs", "Out for Delivery"]
    table_rows = []
    for k in ordered_keys:
        if k in counts:
            cnt = counts[k]
            pct = (cnt / total) * 100.0 if total else 0
            label = status_emojis.get(k, k)
            if status_filter and k.lower() == status_filter.lower():
                table_rows.append(f"| **{label}** | **{cnt:,}** | **{pct:.1f}%** |")
            else:
                table_rows.append(f"| {label} | {cnt:,} | {pct:.1f}% |")

    for k, cnt in counts.items():
        if k not in ordered_keys:
            pct = (cnt / total) * 100.0 if total else 0
            table_rows.append(f"| {status_emojis.get(k, k)} | {cnt:,} | {pct:.1f}% |")

    table_rows.append(f"| **Total Active Freight** | **{total:,}** | **100.0%** |")
    table_md = "| Lifecycle Status | Active Shipments | Network Share |\n|---|---|---|\n" + "\n".join(table_rows)

    if status_filter:
        target_count = counts.get(status_filter, 0)
        if target_count == 0:
            for k, v in counts.items():
                if status_filter.lower() in k.lower():
                    target_count = v
                    status_filter = k
                    break
        pct = (target_count / total) * 100.0 if total else 0
        emoji_label = status_emojis.get(status_filter, status_filter)
        body = (
            f"# 📊 Real-Time Shipment Status Count\n\n"
            f"There are currently **{target_count:,} shipments** in **{emoji_label}** status ({pct:.1f}% of active freight) across FleetHarbor's logistics network.\n\n"
            f"### Operational Network Snapshot\n\n{table_md}\n\n"
            f"To inspect any specific consignment, query its tracking number (e.g., `SHP-10001` through `SHP-20000`)."
        )
    else:
        body = (
            f"# 📊 Total Shipments Overview & Network Status\n\n"
            f"FleetHarbor AI is currently tracking **{total:,} total real-time shipments** across our global logistics network.\n\n"
            f"### Current Network Distribution\n\n{table_md}\n\n"
            f"To query a specific shipment, type its identifier (e.g. `What is the status of SHP-10001?`)."
        )

    return ChatResult(
        response=body,
        sources=[f"Shipment Database Registry ({total:,} Real-Time Shipments)"],
        response_type="shipment_aggregate",
        shipment_id=None,
        structured_data={"status_counts": counts, "total": total, "filter": status_filter},
    )


def build_employee_aggregate_report(emp_data: dict[str, Any]) -> ChatResult:
    """Construct an authoritative employee directory workforce distribution report."""
    total = emp_data.get("total", 0)
    hub_count = emp_data.get("hub_count")
    dept_counts = emp_data.get("by_department", {})
    dept_icons = {
        "Warehouse Operations": "📦 Warehouse Operations",
        "Fleet & Linehaul Dispatch": "🚛 Fleet & Linehaul Dispatch",
        "Customs & Trade Compliance": "📋 Customs & Trade Compliance",
        "Logistics Coordination": "🌐 Logistics Coordination",
        "Safety & Maintenance": "🔧 Safety & Maintenance",
    }
    table_rows = []
    for dept, count in dept_counts.items():
        icon_label = dept_icons.get(dept, f"👥 {dept}")
        pct = (count / total) * 100.0 if total else 0
        table_rows.append(f"| {icon_label} | **{count}** | {pct:.1f}% |")
    table_rows.append(f"| **Total Logistics Workforce** | **{total}** | **100.0%** |")
    table_md = "| Department / Operations Division | Active Staff | Share |\n|---|---|---|\n" + "\n".join(table_rows)

    hub_phrase = f"across **{hub_count} logistics hub locations**" if hub_count else "across FleetHarbor's logistics network"
    body = (
        f"# 👥 FleetHarbor Personnel & Workforce Directory\n\n"
        f"FleetHarbor employs **{total} active logistics professionals** {hub_phrase}.\n\n"
        f"### Operations Staffing Breakdown\n\n{table_md}\n\n"
        f"To look up a specific team member, query their Employee ID (e.g., `Look up EMP-20001`)."
    )
    return ChatResult(
        response=body,
        sources=[f"Employee Directory Roster ({total} Personnel)"],
        response_type="employee_aggregate",
        shipment_id=None,
        structured_data=emp_data,
    )


def build_employee_location_count_report(emp_loc_data: dict[str, Any]) -> ChatResult:
    """Construct a factual location-filtered employee count card from SQLite roster data."""
    loc = emp_loc_data.get("location") or "Specified Hub"
    total = int(emp_loc_data.get("total", 0))
    by_dept = emp_loc_data.get("by_department") or {}

    if total == 0:
        body = (
            f"# 👥 Employee Workforce Count – {loc}\n\n"
            f"There are currently **0 employees** assigned to hubs matching **{loc}** in the FleetHarbor personnel directory."
        )
        return ChatResult(
            response=body,
            sources=["Employee Directory Roster (0 Matches)"],
            response_type="employee_aggregate",
            shipment_id=None,
            structured_data=emp_loc_data,
        )

    rows = [
        f"| {dept} | **{cnt}** | {(cnt / total) * 100.0:.1f}% |"
        for dept, cnt in by_dept.items()
    ]
    rows.append(f"| **Total Assigned Staff** | **{total}** | **100.0%** |")
    table_md = "| Department | Employees | Share |\n|---|---|---|\n" + "\n".join(rows)
    body = (
        f"# 👥 Employee Workforce Count – {loc}\n\n"
        f"There are currently **{total} active employees** assigned to hubs matching **{loc}**.\n\n"
        f"{table_md}"
    )
    return ChatResult(
        response=body,
        sources=[f"Employee Directory Roster ({total} Personnel in {loc})"],
        response_type="employee_aggregate",
        shipment_id=None,
        structured_data=emp_loc_data,
    )


def build_enterprise_shipment_report(ent: Dict[str, Any], query_lower: str) -> str:
    """Build structured, concise Markdown report for enterprise booking queries."""
    bid = ent["booking_id"]
    is_delayed = ent.get("is_delayed", False)
    status_str = f"🔴 Delayed (+{ent.get('delay_days', 0)} days)" if is_delayed else "🟢 Delivered"

    if any(w in query_lower for w in ("carrier", "who is carrying", "airline", "shipping line")) and "overview" not in query_lower:
        return (
            f"### Shipment Information – `{bid}`\n"
            f"- **Booking Reference:** `{bid}`\n"
            f"- **Assigned Carrier:** **{ent.get('carrier_name')}** (`{ent.get('carrier_type')}` carrier)\n"
            f"- **Carrier Rating:** {ent.get('carrier_rating')}/5.0 ({ent.get('years_of_service')} years of service, fleet size {ent.get('fleet_size'):,}, HQ: {ent.get('carrier_hq')})\n"
            f"- **Assigned Vehicle:** `{ent.get('vehicle_number')}` ({ent.get('vehicle_type')}, {ent.get('maintenance_status')} condition)\n"
            f"- **Derived Shipment Status:** {status_str}"
        )

    if ("destination" in query_lower or "where is it going" in query_lower) and "origin" not in query_lower:
        return (
            f"### Shipment Information – `{bid}`\n"
            f"- **Booking Reference:** `{bid}`\n"
            f"- **Destination:** **{ent.get('destination_city')}, {ent.get('destination_country')}** (Port/Gateway: {ent.get('destination_port')})\n"
            f"- **Origin:** {ent.get('origin_city')}, {ent.get('origin_country')} ({ent.get('origin_port')})\n"
            f"- **Expected Delivery:** {ent.get('expected_delivery_date')} | **Actual Delivery:** {ent.get('actual_delivery_date')} ({status_str})"
        )

    if "weather" in query_lower and "status" not in query_lower:
        return (
            f"### Operational Weather Context – `{bid}`\n"
            f"- **Monitored City:** {ent.get('weather_city')} (Forecast: {ent.get('forecast_date')})\n"
            f"- **Condition:** **{ent.get('weather_condition')}**\n"
            f"- **Metrics:** Temp {ent.get('temperature')}°C | Rainfall {ent.get('rainfall')} mm | Wind {ent.get('wind_speed')} km/h | Humidity {ent.get('humidity')}% | Visibility {ent.get('visibility')} km\n"
            f"- **Derived Delivery Status:** {status_str}"
        )

    if any(w in query_lower for w in ("warehouse", "storage facility")):
        return (
            f"### Operational Warehouse Information – `{bid}`\n"
            f"- **Warehouse:** **{ent.get('warehouse_name')}** ({ent.get('warehouse_type')} facility)\n"
            f"- **Location:** {ent.get('warehouse_city')}, {ent.get('warehouse_state')}\n"
            f"- **Capacity / Utilization:** {ent.get('warehouse_capacity'):,} units ({ent.get('current_utilization')}% utilized)"
        )

    if "delivery history" in query_lower or "attempts" in query_lower:
        return (
            f"### Operational Delivery History – `{bid}`\n"
            f"- **Derived Delivery Status:** {status_str} *(computed from `shipment_delivery_history`)*\n"
            f"- **Expected Delivery Date:** {ent.get('expected_delivery_date')}\n"
            f"- **Actual Delivery Date:** {ent.get('actual_delivery_date')}\n"
            f"- **Delivery Attempts:** {ent.get('delivery_attempts')}\n"
            f"- **Delay Beyond Expected:** {ent.get('delay_days', 0)} day(s)"
        )

    customs_flag = "Required" if ent.get("customs_required") else "Not Required"
    docs_flag = "Complete" if ent.get("documentation_complete") else "Incomplete"
    insp_flag = "Required" if ent.get("inspection_required") else "Not Required"
    ai_inf = ent.get("ai_inference") or {}
    alerts = ent.get("alerts") or []

    alert_lines = (
        "\n".join(
            f"- **{a.get('severity', 'Info')} — {a.get('alert_type')} ({a.get('alert_status')}):** {a.get('recommended_action')}"
            for a in alerts[:3]
        )
        if alerts
        else "- No open monitoring alerts logged."
    )

    return (
        f"# 📦 Shipment Report – `{bid}`\n\n"
        f"### Shipment Information\n"
        f"- **Booking Reference:** `{bid}`\n"
        f"- **Shipment Status:** {status_str} *(derived from delivery history)*\n"
        f"- **Customer:** {ent.get('customer_name')} ({ent.get('customer_type')} · {ent.get('industry')})\n"
        f"- **Origin:** {ent.get('origin_city')}, {ent.get('origin_country')} ({ent.get('origin_port')})\n"
        f"- **Destination:** {ent.get('destination_city')}, {ent.get('destination_country')} ({ent.get('destination_port')})\n"
        f"- **Carrier:** {ent.get('carrier_name')} ({ent.get('carrier_type')}, Rating {ent.get('carrier_rating')}/5.0)\n"
        f"- **Product / Cargo:** {ent.get('product_name')} (`{ent.get('product_category')}`, HS `{ent.get('hs_code')}`, {ent.get('weight_kg')} kg, ${ent.get('declared_value'):,.2f})\n"
        f"- **Expected Delivery:** {ent.get('expected_delivery_date')}\n"
        f"- **Actual Delivery:** {ent.get('actual_delivery_date')} ({ent.get('delivery_attempts')} attempt(s))\n\n"
        f"### Operational Information\n"
        f"- **Route & Risk:** {ent.get('distance_km')} km (~{ent.get('average_transit_days')} days avg) · Route Risk: **{ent.get('route_risk')}** (Traffic Index: {ent.get('traffic_index')})\n"
        f"- **Warehouse:** {ent.get('warehouse_name')} ({ent.get('warehouse_type')}, {ent.get('current_utilization')}% utilized)\n"
        f"- **Weather Forecast:** {ent.get('weather_city')} — {ent.get('weather_condition')} ({ent.get('temperature')}°C, Wind {ent.get('wind_speed')} km/h)\n"
        f"- **Customs Status:** Customs {customs_flag} · Documentation: **{docs_flag}** · Inspection: {insp_flag}\n"
        f"- **AI Delay Risk Assessment:** Probability `{ai_inf.get('delay_probability', 'N/A')}` (`{ai_inf.get('risk_category', 'N/A')}` risk)\n"
        f"{alert_lines}\n\n"
        f"### Summary\n"
        f"Shipment `{bid}` ({ent.get('shipping_mode')} {ent.get('shipment_type')}, Priority: {ent.get('priority')}) is **{ent.get('derived_status')}** via {ent.get('carrier_name')} from {ent.get('origin_city')} to {ent.get('destination_city')}."
    )


def format_enterprise_entity_card(etype: str, r: Dict[str, Any]) -> ChatResult:
    """Format standalone customer, carrier, warehouse, or route dimension records."""
    if etype == "customer":
        body = (
            f"### Customer Account Details\n"
            f"- **Customer Name:** {r['customer_name']} (`{r['customer_id']}`)\n"
            f"- **Type / Industry:** {r['customer_type']} · {r['industry']}\n"
            f"- **Location:** {r['city']}, {r['state']}, {r['country']}\n"
            f"- **Status:** {r['customer_status']} (Registered: {r['registration_date']})"
        )
        src = f"Enterprise Customers Database ({r['customer_name']})"
    elif etype == "carrier":
        body = (
            f"### Carrier Details\n"
            f"- **Carrier Name:** {r['carrier_name']} (`{r['carrier_id']}`)\n"
            f"- **Mode / Type:** {r['carrier_type']}\n"
            f"- **Rating:** {r['average_rating']}/5.0\n"
            f"- **Fleet Size:** {r['fleet_size']} · **Experience:** {r['years_of_service']} years\n"
            f"- **Headquarters:** {r['headquarters']}"
        )
        src = f"Enterprise Carriers Database ({r['carrier_name']})"
    elif etype == "warehouse":
        body = (
            f"### Warehouse Information\n"
            f"- **Warehouse:** {r['warehouse_name']} (`{r['warehouse_id']}`)\n"
            f"- **Facility Type:** {r['warehouse_type']}\n"
            f"- **Location:** {r['city']}, {r['state']}\n"
            f"- **Capacity / Utilization:** {r['warehouse_capacity']:,} ({r['current_utilization']}% utilized)"
        )
        src = f"Enterprise Warehouses Database ({r['warehouse_name']})"
    else:
        body = (
            f"### Route Information\n"
            f"- **Corridor:** {r['origin_city']}, {r['origin_country']} ({r['origin_port']}) → "
            f"{r['destination_city']}, {r['destination_country']} ({r['destination_port']})\n"
            f"- **Distance:** {r['distance_km']} km | **Avg Transit:** {r['average_transit_days']} days\n"
            f"- **Route Risk:** {r['route_risk']} | **Traffic Index:** {r['traffic_index']}"
        )
        src = f"Enterprise Routes Database ({r['origin_city']} -> {r['destination_city']})"

    return ChatResult(response=body, sources=[src], response_type=f"enterprise_{etype}", structured_data=r)
