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

## Notes

- `make release-tag` creates an annotated tag from the current `pyproject.toml` version.
- Pushing a `v*.*.*` tag triggers `.github/workflows/publish.yml`.
- The publish workflow creates PyPI and GHCR artifacts, then creates the GitHub Release with generated notes.
