"""Master automated test runner for the FleetHarbor Logistics AI Chatbot.
Executes all 174 questions/turns from tests/question_bank/ against the real chatbot engine and API,
evaluates responses across 10 quality dimensions using evaluators.metrics,
captures latency, records failures, and generates:
  - tests/reports/test_results.json
  - tests/reports/test_report.html
  - tests/reports/performance_report.json
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Ensure offline speed for SentenceTransformers (avoid 25s DNS retry timeouts when running local/sandboxed)
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# Anchoring paths
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Ensure ChromaDB persist directory is absolute
from logistics_chatbot.core import config
if not Path(config.CHROMA_PERSIST_DIRECTORY).is_absolute():
    config.CHROMA_PERSIST_DIRECTORY = ROOT / config.CHROMA_PERSIST_DIRECTORY

from chatbot.bot import generate_response
from tests.evaluators.metrics import evaluate_response

QB_DIR = ROOT / "tests" / "question_bank"
REPORTS_DIR = ROOT / "tests" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def run_single_test(test_item: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
    """Execute one test case against the live chatbot engine and return evaluated metrics."""
    test_id = test_item.get("test_id", "TEST_UNK")
    category = test_item.get("category", "general")
    query = test_item.get("question", "")
    expected_intent = test_item.get("expected_intent")
    ground_truth = test_item.get("ground_truth")
    required_shipment_id = test_item.get("required_shipment_id")
    eval_criteria = test_item.get("evaluation_criteria", {})
    required_concepts = eval_criteria.get("required_concepts")

    t0 = time.perf_counter()
    response_text = ""
    sources = []
    response_type = "unknown"
    status_code = 200
    error_msg = None

    try:
        # Edge case: Empty or whitespace query
        if not query or not query.strip():
            try:
                generate_response(query, session_id=session_id)
            except Exception as exc:
                response_text = str(exc)
                response_type = "error_handled"
                status_code = 400
        # Edge case: Extremely long query
        elif len(query) > 2000:
            try:
                generate_response(query, session_id=session_id)
            except Exception as exc:
                response_text = str(exc)
                response_type = "error_handled"
                status_code = 413
        else:
            res = generate_response(query, session_id=session_id)
            response_text = getattr(res, "response", str(res))
            sources = getattr(res, "sources", [])
            response_type = getattr(res, "response_type", "general_knowledge")

    except Exception as exc:
        error_msg = str(exc)
        response_text = f"Exception occurred: {exc}"
        status_code = 500

    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    # Evaluate using metrics engine
    eval_res = evaluate_response(
        query=query,
        response_text=response_text,
        sources=sources,
        latency_ms=latency_ms,
        expected_intent=expected_intent,
        ground_truth=ground_truth,
        required_shipment_id=required_shipment_id,
        required_concepts=required_concepts,
        is_multi_turn=session_id is not None,
        status_code=status_code,
    )

    return {
        "test_id": test_id,
        "category": category,
        "query": query,
        "expected_intent": expected_intent,
        "actual_response_type": response_type,
        "latency_ms": latency_ms,
        "status_code": status_code,
        "passed": eval_res["passed"],
        "overall_score": eval_res["overall_score"],
        "scores": eval_res["scores"],
        "evaluation_notes": eval_res["notes"],
        "response_preview": response_text[:280] + ("..." if len(response_text) > 280 else ""),
        "full_response": response_text,
        "sources": sources,
        "error": error_msg,
    }


def run_all_tests() -> Dict[str, Any]:
    """Execute the full question bank test suite across all 12 categories."""
    print("=" * 75)
    print("FLEETHARBOR LOGISTICS AI CHATBOT - AUTOMATED TEST SUITE EXECUTION")
    print("=" * 75)

    all_results = []
    category_summaries = {}
    latencies = []
    passed_count = 0
    failed_count = 0

    qb_files = sorted(QB_DIR.glob("*.json"))
    if not qb_files:
        print("Error: No question bank JSON files found in", QB_DIR)
        return {}

    start_time = time.time()

    for qb_file in qb_files:
        cat_name = qb_file.stem
        with open(qb_file, "r", encoding="utf-8") as f:
            items = json.load(f)

        print(f"\n▶ Executing Category: {cat_name} ({len(items)} items)...")
        cat_passed = 0
        cat_failed = 0
        cat_latencies = []

        if cat_name == "multi_turn_conversations":
            # Multi-turn scenarios
            for scenario in items:
                scenario_id = scenario.get("test_id", "SCENARIO")
                turns = scenario.get("turns", [])
                session_id = f"test_session_{scenario_id}_{uuid.uuid4().hex[:6]}"

                for turn in turns:
                    turn_num = turn.get("turn", 1)
                    test_id = f"{scenario_id}_T{turn_num}"
                    test_item = {
                        "test_id": test_id,
                        "category": cat_name,
                        "question": turn.get("question"),
                        "expected_intent": turn.get("expected_intent"),
                    }
                    res = run_single_test(test_item, session_id=session_id)
                    all_results.append(res)
                    cat_latencies.append(res["latency_ms"])
                    latencies.append(res["latency_ms"])

                    if res["passed"]:
                        cat_passed += 1
                        passed_count += 1
                        status_symbol = "✅"
                    else:
                        cat_failed += 1
                        failed_count += 1
                        status_symbol = "❌"

                    print(f"  {status_symbol} [{test_id}] (Turn {turn_num}) {res['query'][:45]:45s} -> Score: {res['overall_score']:.1f} ({res['latency_ms']:.1f}ms)")
        else:
            # Single-turn questions
            for item in items:
                res = run_single_test(item)
                all_results.append(res)
                cat_latencies.append(res["latency_ms"])
                latencies.append(res["latency_ms"])

                if res["passed"]:
                    cat_passed += 1
                    passed_count += 1
                    status_symbol = "✅"
                else:
                    cat_failed += 1
                    failed_count += 1
                    status_symbol = "❌"

                print(f"  {status_symbol} [{res['test_id']:<10}] {res['query'][:50]:50s} -> Score: {res['overall_score']:.1f} ({res['latency_ms']:.1f}ms)")

        cat_total = cat_passed + cat_failed
        cat_pass_rate = round((cat_passed / max(1, cat_total)) * 100.0, 1)
        cat_avg_lat = round(sum(cat_latencies) / max(1, len(cat_latencies)), 2)

        category_summaries[cat_name] = {
            "total": cat_total,
            "passed": cat_passed,
            "failed": cat_failed,
            "pass_rate_pct": cat_pass_rate,
            "avg_latency_ms": cat_avg_lat,
        }

    total_time = round(time.time() - start_time, 2)
    total_tests = passed_count + failed_count
    pass_rate = round((passed_count / max(1, total_tests)) * 100.0, 1)

    latencies.sort()
    p50_lat = latencies[int(len(latencies) * 0.50)] if latencies else 0
    p90_lat = latencies[int(len(latencies) * 0.90)] if latencies else 0
    p95_lat = latencies[int(len(latencies) * 0.95)] if latencies else 0
    avg_lat = round(sum(latencies) / max(1, len(latencies)), 2) if latencies else 0

    print("\n" + "=" * 75)
    print("EXECUTION SUMMARY")
    print("=" * 75)
    print(f"Total Test Cases Executed: {total_tests}")
    print(f"Passed:                   {passed_count} ({pass_rate}%)")
    print(f"Failed:                   {failed_count}")
    print(f"Total Execution Time:     {total_time}s")
    print(f"Latency P50 / P90 / P95:  {p50_lat:.1f}ms / {p90_lat:.1f}ms / {p95_lat:.1f}ms (Mean: {avg_lat:.1f}ms)")
    print("=" * 75)

    # Save test_results.json
    results_payload = {
        "summary": {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "passed": passed_count,
            "failed": failed_count,
            "pass_rate_pct": pass_rate,
            "total_execution_time_seconds": total_time,
            "latency": {
                "mean_ms": avg_lat,
                "p50_ms": p50_lat,
                "p90_ms": p90_lat,
                "p95_ms": p95_lat,
                "min_ms": min(latencies) if latencies else 0,
                "max_ms": max(latencies) if latencies else 0,
            },
            "category_breakdown": category_summaries,
        },
        "results": all_results,
    }

    results_file = REPORTS_DIR / "test_results.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2)
    print(f"Saved test results to: {results_file}")

    # Save performance_report.json
    perf_payload = {
        "timestamp": datetime.now().isoformat(),
        "total_queries_measured": len(latencies),
        "latency_metrics_ms": {
            "mean": avg_lat,
            "p50": p50_lat,
            "p90": p90_lat,
            "p95": p95_lat,
            "min": min(latencies) if latencies else 0,
            "max": max(latencies) if latencies else 0,
        },
        "category_latency_ranking": sorted(
            [{"category": k, "avg_latency_ms": v["avg_latency_ms"]} for k, v in category_summaries.items()],
            key=lambda x: x["avg_latency_ms"]
        ),
    }
    perf_file = REPORTS_DIR / "performance_report.json"
    with open(perf_file, "w", encoding="utf-8") as f:
        json.dump(perf_payload, f, indent=2)
    print(f"Saved performance report to: {perf_file}")

    # Generate interactive HTML report
    generate_html_report(results_payload)

    return results_payload


def generate_html_report(results_payload: Dict[str, Any]):
    """Generate a modern, self-contained interactive HTML test report."""
    summary = results_payload["summary"]
    results = results_payload["results"]
    cat_breakdown = summary["category_breakdown"]

    category_cards_html = ""
    for cat, data in cat_breakdown.items():
        badge_class = "badge-success" if data["pass_rate_pct"] >= 90 else "badge-warning" if data["pass_rate_pct"] >= 70 else "badge-danger"
        category_cards_html += f"""
        <div class="card cat-card">
          <div class="cat-header">
            <h4>{cat.replace('_', ' ').title()}</h4>
            <span class="badge {badge_class}">{data['pass_rate_pct']}% Pass</span>
          </div>
          <div class="cat-body">
            <p><strong>Passed:</strong> {data['passed']} / {data['total']}</p>
            <p><strong>Avg Latency:</strong> {data['avg_latency_ms']:.1f} ms</p>
          </div>
        </div>
        """

    table_rows_html = ""
    for r in results:
        status_badge = '<span class="status-pass">PASS</span>' if r["passed"] else '<span class="status-fail">FAIL</span>'
        notes_html = "<br>".join(r["evaluation_notes"]) if r["evaluation_notes"] else "None"
        sources_html = "<br>".join(r["sources"]) if r["sources"] else "None"
        query_safe = r["query"].replace("<", "&lt;").replace(">", "&gt;")
        resp_safe = r["full_response"].replace("<", "&lt;").replace(">", "&gt;")

        table_rows_html += f"""
        <tr class="{'row-fail' if not r['passed'] else ''}">
          <td><strong>{r['test_id']}</strong></td>
          <td><span class="category-pill">{r['category']}</span></td>
          <td class="query-cell">{query_safe}</td>
          <td>{status_badge}</td>
          <td><strong>{r['overall_score']:.1f} / 5.0</strong></td>
          <td>{r['latency_ms']:.1f} ms</td>
          <td><details><summary>View Details</summary><div class="details-box"><strong>Sources:</strong> {sources_html}<br><strong>Notes:</strong> {notes_html}<br><hr><strong>Response:</strong><pre>{resp_safe}</pre></div></details></td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>FleetHarbor AI • Chatbot Quality Assurance & Evaluation Report</title>
  <style>
    :root {{
      --bg: #0F172A;
      --card-bg: #1E293B;
      --border: #334155;
      --text: #F8FAFC;
      --text-muted: #94A3B8;
      --accent: #3B82F6;
      --success: #10B981;
      --warning: #F59E0B;
      --danger: #EF4444;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); padding: 2rem; }}
    .container {{ max-width: 1400px; margin: 0 auto; }}
    header {{ margin-bottom: 2rem; border-bottom: 1px solid var(--border); padding-bottom: 1.5rem; }}
    h1 {{ font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #60A5FA, #38BDF8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .meta-bar {{ color: var(--text-muted); margin-top: 0.5rem; font-size: 0.95rem; }}
    .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
    .metric-card {{ background: var(--card-bg); padding: 1.5rem; border-radius: 12px; border: 1px solid var(--border); }}
    .metric-label {{ font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }}
    .metric-value {{ font-size: 2.2rem; font-weight: 800; margin-top: 0.4rem; }}
    .metric-value.pass {{ color: var(--success); }}
    .metric-value.fail {{ color: var(--danger); }}
    .metric-value.info {{ color: var(--accent); }}
    .categories-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; margin-bottom: 2.5rem; }}
    .cat-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 10px; padding: 1rem; }}
    .cat-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }}
    .cat-header h4 {{ font-size: 1rem; }}
    .cat-body p {{ font-size: 0.85rem; color: var(--text-muted); margin: 0.2rem 0; }}
    .badge {{ font-size: 0.75rem; padding: 0.2rem 0.6rem; border-radius: 999px; font-weight: 700; }}
    .badge-success {{ background: rgba(16, 185, 129, 0.2); color: var(--success); }}
    .badge-warning {{ background: rgba(245, 158, 11, 0.2); color: var(--warning); }}
    .badge-danger {{ background: rgba(239, 68, 68, 0.2); color: var(--danger); }}
    .table-container {{ background: var(--card-bg); border-radius: 12px; border: 1px solid var(--border); overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9rem; }}
    th, td {{ padding: 0.9rem 1rem; border-bottom: 1px solid var(--border); }}
    th {{ background: #131D31; color: var(--text-muted); font-size: 0.8rem; text-transform: uppercase; }}
    tr:hover {{ background: rgba(255, 255, 255, 0.02); }}
    .row-fail {{ background: rgba(239, 68, 68, 0.08); }}
    .status-pass {{ color: var(--success); font-weight: 800; }}
    .status-fail {{ color: var(--danger); font-weight: 800; }}
    .category-pill {{ font-size: 0.75rem; background: #334155; padding: 0.2rem 0.5rem; border-radius: 4px; }}
    .query-cell {{ max-width: 320px; }}
    details {{ cursor: pointer; }}
    summary {{ color: var(--accent); font-weight: 600; }}
    .details-box {{ background: #0B132B; padding: 0.75rem; border-radius: 6px; margin-top: 0.5rem; font-size: 0.85rem; color: #CBD5E1; }}
    pre {{ background: #030712; padding: 0.5rem; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; font-family: monospace; font-size: 0.8rem; margin-top: 0.5rem; }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>FleetHarbor AI • Chatbot Quality Assurance & Evaluation Report</h1>
      <div class="meta-bar">Generated: {summary['timestamp']} | Suite: 12 Question Categories | Total Questions Executed: {summary['total_tests']}</div>
    </header>

    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-label">Pass Rate</div>
        <div class="metric-value pass">{summary['pass_rate_pct']}%</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Total Tests Passed</div>
        <div class="metric-value pass">{summary['passed']} <span style="font-size:1rem;color:var(--text-muted)">/ {summary['total_tests']}</span></div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Failed Tests</div>
        <div class="metric-value {'fail' if summary['failed'] > 0 else 'pass'}">{summary['failed']}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Median Latency (P50)</div>
        <div class="metric-value info">{summary['latency']['p50_ms']:.1f} <span style="font-size:1rem">ms</span></div>
      </div>
    </div>

    <h2 style="margin-bottom: 1rem; font-size: 1.3rem;">Category Breakdown</h2>
    <div class="categories-grid">
      {category_cards_html}
    </div>

    <h2 style="margin-bottom: 1rem; font-size: 1.3rem;">Detailed Test Execution Results ({len(results)} items)</h2>
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Category</th>
            <th>Query</th>
            <th>Status</th>
            <th>Score</th>
            <th>Latency</th>
            <th>Details</th>
          </tr>
        </thead>
        <tbody>
          {table_rows_html}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>
"""
    html_file = REPORTS_DIR / "test_report.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated HTML test report at: {html_file}")


if __name__ == "__main__":
    run_all_tests()
