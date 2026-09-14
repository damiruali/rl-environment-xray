"""Transparent product heuristic, not calibrated risk probability."""


def score(findings):
    codes = {f.code: f.severity for f in findings}
    deductions = {
        code: {"CRITICAL": 30, "WARNING": 8, "INFO": 0}[severity]
        for code, severity in codes.items()
    }
    # Never a safety claim: 100 means no configured findings in these inputs.
    health = max(0, 100 - sum(deductions.values()))
    critical = "CRITICAL" in codes.values()
    warning = "WARNING" in codes.values()
    return {
        "health": health,
        "status": "FAIL" if critical else "REVIEW" if warning else "PASS",
        "decision": "DO NOT TRAIN"
        if critical
        else "REVIEW EVIDENCE"
        if warning
        else "ELIGIBLE FOR A SMALL TRAINING EXPERIMENT",
        "deductions": deductions,
        "score_is_heuristic": True,
        "scope": "Configured diagnostics on supplied trajectories only; not safety certification.",
    }
