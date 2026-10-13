# Contributing to Agent X-Ray

Thanks for helping make agent environments easier to evaluate before training or release.

## Development setup

```bash
uv sync --frozen --no-editable
uv run --no-sync pytest -q
uv run --no-sync ruff check xray environments/support_preflight tests
```

## Good contributions

- a minimal trajectory that reproduces an environment defect;
- a deterministic analyzer with a clear false-positive boundary;
- a runtime adapter that preserves provenance;
- a regression test for an existing finding;
- documentation that makes evidence and limitations easier to audit.

Please keep pull requests focused. Explain the behavioral contract, include a test where
practical, and report what was actually verified.

## Data and security

All examples must comply with the [Public Data Policy](docs/PUBLIC_DATA_POLICY.md). Do not
submit employer, client, customer, or other private material. Never include credentials or
full unredacted provider traces.

For vulnerabilities, follow [SECURITY.md](SECURITY.md) rather than opening a public issue.
