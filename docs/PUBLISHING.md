# Publication readiness

This repository is the approved public Community Demo. Publishing it to GitHub does not publish
the environment to Prime Hub. No Prime login or API key was found during this build.

## Verified toolchain

Verifiers `0.3.2.dev80`, inspected source commit
`3bbac389691a1ee31f6b3ae431921b5c525f3fed`; Prime CLI `0.6.29`; Python `3.12.14`.
The repository `uv.lock` is authoritative. The standalone environment declares the exact
Verifiers version rather than importing source from the root project.

Native V1 uses Taskset discovery through `__all__`; the installed `prime env init --help`
already creates V1 (`-T` adds a toolset). It does **not** accept the older `--v1` flag.
Prime CLI emitted a fallback warning for removed `verifiers.cli.plugins`; native `eval`
and package load work. Treat this as a tooling compatibility caveat, not proof that Hub
validation will accept the archive. Actual upload/server validation remains untested.

## Local release checklist

```bash
uv sync --frozen --no-editable
uv run --no-sync pytest -q
uv run --no-sync ruff check xray environments/support_preflight tests
uv run --no-sync python -m xray demo
uv run --no-sync python -m build environments/support_preflight
```

Wheel and sdist are generated in `environments/support_preflight/dist/`.
The package only includes `support_preflight/` and its README/metadata; no model keys,
artifacts or datasets. Fixed is the default; broken is explicitly documented as a fixture.

## After login and explicit approval

Choose an owner and visibility with the user first. Then:

```bash
uv run --no-sync prime login
uv run --no-sync prime --plain env push \
  --path environments/support_preflight \
  --visibility PRIVATE
```

`--visibility PUBLIC` is a **separate public publication decision**. Push changes remote
state, so it has not been executed here. The user must also review the intentionally
broken variant before making the package broadly available for training.

Inspect after a successful upload with `prime --plain env info OWNER/support-preflight`
using the actual owner returned by the platform. No owner, URL or publication status is invented.

Status: local source/build/load readiness is tested; Hub upload readiness is conditional
on credentials, visibility approval and server-side validation. This is not a claim of publication.
