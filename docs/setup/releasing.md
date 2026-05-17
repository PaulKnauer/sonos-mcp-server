# Releasing SoniqMCP

Use these commands from the repository root to cut a new release.

## Patch release

```bash
make release-bump-patch
git add pyproject.toml
git commit -m "Release v0.1.1"
git push origin main
make release-tag
git push origin v0.1.1
```

## Minor release

```bash
make release-bump-minor
git add pyproject.toml
git commit -m "Release v0.2.0"
git push origin main
make release-tag
git push origin v0.2.0
```

## Major release

```bash
make release-bump-major
git add pyproject.toml
git commit -m "Release v1.0.0"
git push origin main
make release-tag
git push origin v1.0.0
```

## Optional manual GitHub Release

If the tag already exists and you need to create the GitHub Release entry manually:

```bash
make release-gh
```

## Optional auth validation (v0.6.0+)

Before cutting a release that includes optional auth changes, run these checks to confirm auth wiring, smoke behavior, and docs accuracy:

```bash
make test-auth      # auth unit tests: verifiers, server wiring, no-op/stdio guards
make smoke-auth     # static HTTP auth smoke: missing/wrong/correct token against a live subprocess
uv run pytest -q tests/unit/test_integration_docs.py  # docs and setup guidance drift checks
make lint
make type-check
```

The auth and docs validation commands require no external services, OIDC providers, or Sonos hardware. `make smoke-auth` runs against a local subprocess only.

For broader coverage before a release cut:

```bash
make coverage       # full test suite including smoke tests
make ci             # lint + type-check + coverage + audit + build-check
```

If Helm is available locally, also run:

```bash
make helm-lint
uv run pytest -q tests/smoke/helm/test_helm_smoke.py
```

---

## Notes

- `make release-tag` creates an annotated tag from the current `pyproject.toml` version.
- Pushing a `v*.*.*` tag triggers `.github/workflows/publish.yml`.
- The publish workflow creates PyPI and GHCR artifacts, then creates the GitHub Release with generated notes.
