#!/usr/bin/env python3
"""
Generate a lightweight Jenkins-friendly HTML test summary from JUnit XML files.

Outputs:
- reports/html/index.html
- reports/artifacts/test-summary.json
- reports/artifacts/test-summary.txt
- reports/artifacts/build-description.txt
- reports/artifacts/test-metrics.csv
"""

from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def _safe_int(value: str | None) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _safe_float(value: str | None) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _collect_suite_totals(xml_path: Path) -> dict:
    root = ET.parse(xml_path).getroot()
    suites = [root] if root.tag == "testsuite" else root.findall(".//testsuite")

    tests = failures = errors = skipped = 0
    duration = 0.0

    for suite in suites:
        tests += _safe_int(suite.get("tests"))
        failures += _safe_int(suite.get("failures"))
        errors += _safe_int(suite.get("errors"))
        skipped += _safe_int(suite.get("skipped"))
        duration += _safe_float(suite.get("time"))

    failed = failures + errors
    passed = max(tests - failed - skipped, 0)

    return {
        "suite": xml_path.stem,
        "tests": tests,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "duration_seconds": round(duration, 3),
    }


def _bar_width(value: int, total: int) -> str:
    if total <= 0:
        return "0%"
    return f"{(value / total) * 100:.2f}%"


def _format_duration(seconds: float) -> str:
    return f"{seconds:.2f}s"


def _render_html(summary: dict, job_name: str, build_number: str, build_url: str) -> str:
    total = summary["total"]
    suites = summary["suites"]
    overall_total = max(total["tests"], 1)

    suite_rows = "\n".join(
        f"""
        <tr>
          <td>{html.escape(suite["suite"])}</td>
          <td>{suite["tests"]}</td>
          <td class="pass">{suite["passed"]}</td>
          <td class="fail">{suite["failed"]}</td>
          <td class="skip">{suite["skipped"]}</td>
          <td>{_format_duration(suite["duration_seconds"])}</td>
        </tr>
        """
        for suite in suites
    )

    metadata = []
    if job_name:
        metadata.append(f"<strong>Job:</strong> {html.escape(job_name)}")
    if build_number:
        metadata.append(f"<strong>Build:</strong> #{html.escape(build_number)}")
    if build_url:
        metadata.append(
            f'<strong>Build URL:</strong> <a href="{html.escape(build_url)}">{html.escape(build_url)}</a>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>S3 Test Summary</title>
  <style>
    :root {{
      --bg: #f5f4ee;
      --card: #fffdf8;
      --ink: #1f2a37;
      --muted: #5f6b7a;
      --line: #ddd6c8;
      --pass: #2f855a;
      --fail: #c53030;
      --skip: #b7791f;
      --accent: #1d4ed8;
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: linear-gradient(180deg, #f8f7f1 0%, #efe8da 100%);
      color: var(--ink);
    }}
    .wrap {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    .hero {{
      background: radial-gradient(circle at top left, #fffefb 0%, #f7f0df 48%, #efe3c4 100%);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 28px;
      box-shadow: 0 12px 30px rgba(55, 65, 81, 0.08);
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: 32px;
      line-height: 1.1;
    }}
    p {{
      margin: 0;
      color: var(--muted);
    }}
    .meta {{
      margin-top: 16px;
      display: grid;
      gap: 6px;
      font-size: 14px;
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 16px;
      margin-top: 22px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 18px;
    }}
    .card .label {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin-bottom: 8px;
    }}
    .card .value {{
      font-size: 30px;
      font-weight: 700;
    }}
    .chart-card {{
      margin-top: 20px;
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 20px;
    }}
    .stacked-bar {{
      display: flex;
      height: 28px;
      border-radius: 999px;
      overflow: hidden;
      background: #e9e2d3;
      border: 1px solid #d8cfbd;
      margin: 14px 0 12px;
    }}
    .stacked-bar div {{
      height: 100%;
    }}
    .pass-bg {{
      background: var(--pass);
    }}
    .fail-bg {{
      background: var(--fail);
    }}
    .skip-bg {{
      background: var(--skip);
    }}
    .legend {{
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      color: var(--muted);
      font-size: 14px;
    }}
    .legend span::before {{
      content: "";
      width: 12px;
      height: 12px;
      display: inline-block;
      border-radius: 999px;
      margin-right: 8px;
      vertical-align: -1px;
    }}
    .legend .pass::before {{
      background: var(--pass);
    }}
    .legend .fail::before {{
      background: var(--fail);
    }}
    .legend .skip::before {{
      background: var(--skip);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 16px;
      overflow: hidden;
    }}
    thead {{
      background: #f0eadb;
    }}
    th, td {{
      padding: 14px 16px;
      text-align: left;
      border-bottom: 1px solid #ebe3d2;
    }}
    tbody tr:last-child td {{
      border-bottom: 0;
    }}
    .pass {{
      color: var(--pass);
      font-weight: 600;
    }}
    .fail {{
      color: var(--fail);
      font-weight: 600;
    }}
    .skip {{
      color: var(--skip);
      font-weight: 600;
    }}
    .note {{
      margin-top: 16px;
      font-size: 13px;
      color: var(--muted);
    }}
    a {{
      color: var(--accent);
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>S3 Test Summary</h1>
      <p>JUnit XML parsed into a build-friendly summary report for Jenkins. Failed counts include both failures and test errors.</p>
      <div class="meta">
        {'<br>'.join(metadata) if metadata else '<span>No build metadata was provided.</span>'}
      </div>
      <div class="cards">
        <div class="card">
          <div class="label">Total Tests</div>
          <div class="value">{total["tests"]}</div>
        </div>
        <div class="card">
          <div class="label">Passed</div>
          <div class="value pass">{total["passed"]}</div>
        </div>
        <div class="card">
          <div class="label">Failed</div>
          <div class="value fail">{total["failed"]}</div>
        </div>
        <div class="card">
          <div class="label">Skipped</div>
          <div class="value skip">{total["skipped"]}</div>
        </div>
        <div class="card">
          <div class="label">Duration</div>
          <div class="value">{_format_duration(total["duration_seconds"])}</div>
        </div>
      </div>
    </section>

    <section class="chart-card">
      <h2>Current Build Distribution</h2>
      <div class="stacked-bar" aria-label="Stacked chart of pass fail skip counts">
        <div class="pass-bg" style="width: {_bar_width(total["passed"], overall_total)}"></div>
        <div class="fail-bg" style="width: {_bar_width(total["failed"], overall_total)}"></div>
        <div class="skip-bg" style="width: {_bar_width(total["skipped"], overall_total)}"></div>
      </div>
      <div class="legend">
        <span class="pass">Passed: {total["passed"]}</span>
        <span class="fail">Failed: {total["failed"]}</span>
        <span class="skip">Skipped: {total["skipped"]}</span>
      </div>
      <div class="note">This stacked bar acts as a quick chart for the current build. Jenkins' native JUnit view will also show test trends across builds.</div>
    </section>

    <table>
      <thead>
        <tr>
          <th>Suite</th>
          <th>Tests</th>
          <th>Passed</th>
          <th>Failed</th>
          <th>Skipped</th>
          <th>Duration</th>
        </tr>
      </thead>
      <tbody>
        {suite_rows}
      </tbody>
    </table>
  </div>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--html-dir", required=True)
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--job-name", default="")
    parser.add_argument("--build-number", default="")
    parser.add_argument("--build-url", default="")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    html_dir = Path(args.html_dir)
    artifact_dir = Path(args.artifact_dir)

    html_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    suites = []
    for xml_file in sorted(input_dir.glob("*.xml")):
        suites.append(_collect_suite_totals(xml_file))

    total_tests = sum(item["tests"] for item in suites)
    total_passed = sum(item["passed"] for item in suites)
    total_failed = sum(item["failed"] for item in suites)
    total_skipped = sum(item["skipped"] for item in suites)
    total_duration = round(sum(item["duration_seconds"] for item in suites), 3)

    summary = {
        "total": {
            "tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "skipped": total_skipped,
            "duration_seconds": total_duration,
        },
        "suites": suites,
    }

    (artifact_dir / "test-summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    lines = [
        f"Total tests: {total_tests}",
        f"Passed: {total_passed}",
        f"Failed: {total_failed}",
        f"Skipped: {total_skipped}",
        f"Duration: {_format_duration(total_duration)}",
        "",
        "By suite:",
    ]
    for suite in suites:
        lines.append(
            "- {suite}: tests={tests}, passed={passed}, failed={failed}, skipped={skipped}, duration={duration}".format(
                suite=suite["suite"],
                tests=suite["tests"],
                passed=suite["passed"],
                failed=suite["failed"],
                skipped=suite["skipped"],
                duration=_format_duration(suite["duration_seconds"]),
            )
        )

    (artifact_dir / "test-summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    build_description = (
        f"Pass {total_passed} | Fail {total_failed} | Skip {total_skipped}"
    )
    (artifact_dir / "build-description.txt").write_text(
        build_description + "\n",
        encoding="utf-8",
    )

    with (artifact_dir / "test-metrics.csv").open("w", newline="", encoding="utf-8") as file_handle:
        writer = csv.writer(file_handle)
        writer.writerow(["suite", "tests", "passed", "failed", "skipped", "duration_seconds"])
        for suite in suites:
            writer.writerow(
                [
                    suite["suite"],
                    suite["tests"],
                    suite["passed"],
                    suite["failed"],
                    suite["skipped"],
                    suite["duration_seconds"],
                ]
            )

    (html_dir / "index.html").write_text(
        _render_html(summary, args.job_name, args.build_number, args.build_url),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
