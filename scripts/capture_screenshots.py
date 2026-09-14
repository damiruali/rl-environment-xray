"""Capture actual rendered artifacts using agent-browser, no image generation."""

import json
import subprocess
from pathlib import Path


def browser(*args):
    result = subprocess.run(
        ["npx", "--yes", "agent-browser@0.37.1", "--session", "rlxray", *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=90,
    )
    print(result.stdout[:1000])


def main():
    root = Path("artifacts").resolve()
    shots = root / "screenshots"
    shots.mkdir(parents=True, exist_ok=True)
    cases = [
        ("01-local-eval.png", "index.html", "#local-eval", "Real native V1 model eval ledger"),
        (
            "02-broken-rollout.png",
            "broken_model_only.html",
            "#trajectory",
            "Actual model trajectory, not a scripted probe",
        ),
        (
            "03-positive-loop.png",
            "broken_report.html",
            "#graph",
            "Witnessed positive business-state cycle with provenance",
        ),
        ("04-xray-fail.png", "broken_report.html", None, "Broken pre-flight FAIL dashboard"),
        ("05-fixed-environment.png", "index.html", "#fix", "Broken/fixed implementation rules"),
        ("06-xray-pass.png", "fixed_report.html", None, "Fixed pre-flight scoped PASS dashboard"),
    ]
    browser("set", "viewport", "1440", "1100")
    manifest = []
    for name, page, selector, description in cases:
        source = root / "xray" / page
        browser("open", source.as_uri())
        browser("snapshot", "-i")
        if selector:
            browser("screenshot", selector, str(shots / name))
        else:
            browser("screenshot", str(shots / name))
        manifest.append(
            {
                "file": name,
                "source": str(source.relative_to(root)),
                "selector": selector,
                "description": description,
                "capture": "agent-browser 0.37.1 / Chromium; actual rendered HTML",
            }
        )
    (shots / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    browser("close")


if __name__ == "__main__":
    main()
