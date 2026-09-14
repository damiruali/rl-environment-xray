"""Produce narrative assets from measured reports; no invented success or spend."""

from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from xray.collector import write_json


def create_assets(root: Path, reports: dict, summaries: dict):
    # Explicit dated list-price estimate, NOT an invoice or claim of actual account spend.
    for summary in summaries.values():
        if summary.get("model") == "qwen/qwen3.8-27b" and summary.get("usage"):
            usage = summary["usage"]
            summary["estimated_cost_usd"] = round(
                (usage["prompt_tokens"] * 0.80 + usage["completion_tokens"] * 4.00) / 1_000_000, 6
            )
            summary["pricing_snapshot"] = {
                "date": "2026-09-11",
                "input_usd_per_million": 0.80,
                "output_usd_per_million": 4.00,
                "source": "https://console.groq.com/docs/model/qwen/qwen3.8-27b",
                "scope": "Recorded successful model calls only; excludes early failed attempts, discounts, credits, tax.",
            }
    environment = Environment(
        loader=PackageLoader("xray", "templates"), autoescape=select_autoescape(["html"])
    )
    context = {"reports": reports, "summaries": summaries}
    (root / "xray" / "index.html").write_text(
        environment.get_template("overview.html").render(**context), encoding="utf-8"
    )
    lines = [
        "# Measured experiment results",
        "",
        "No RL training. No Hub publication.",
        "",
        "| Variant | Model episodes | Business success | Mean reward | X-Ray | Health |",
        "|---|---:|---:|---:|---|---:|",
    ]
    for variant, r in reports.items():
        s = summaries.get(variant, {})
        lines.append(
            f"| {variant} | {s.get('episodes', 'not run')} | {s.get('business_successes', 'n/a')} | "
            f"{s.get('mean_reward', 'n/a')} | {r['status']} | {r['health']} |"
        )
    lines.extend(
        [
            "",
            "X-Ray here includes seven explicitly labelled scripted probes per variant.",
            "Health is a heuristic, not safety probability. Total state coverage and global reachability unknown.",
            "The final fixed training rubric is gated on full business success; milestone feedback remains a separate diagnostic signal.",
            "[Offline regrading](regrading.json) checks the final rubric on the 12 saved model trajectories: all scores unchanged, no new model calls.",
            "",
        ]
    )
    for variant, summary in summaries.items():
        lines.extend(
            [
                f"## {variant} model evaluation",
                "",
                f"Model: `{summary['model']}`.",
                f"Usage: `{summary.get('usage')}`.",
                f"Dated list-price estimate: ${summary.get('estimated_cost_usd', 'unknown')}. Provider invoice cost remains unavailable (`null`).",
                "[Pricing snapshot: Groq Qwen3.8-27B, 2026-09-11](https://console.groq.com/docs/model/qwen/qwen3.8-27b). Excludes early failed attempts and account-specific pricing.",
                "",
            ]
        )
    (root / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    write_json(root / "xray" / "experiment_summary.json", summaries)
    # Publish-ready drafts, never posted automatically. Stored in root only for the main artifact set.
    if root == Path("artifacts"):
        for language in ("RU", "EN"):
            Path(f"LINKEDIN_POST_{language}.md").write_text(
                environment.get_template(f"linkedin_{language}.md").render(**context),
                encoding="utf-8",
            )
