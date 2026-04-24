---
title: "PRFAQ: sonos-mcp-server — Optional Authentication"
status: "complete"
created: "2026-04-23"
updated: "2026-04-23"
stage: 5
concept_type: "open-source"
inputs:
  - "_bmad-output/planning-artifacts/oidc-authelia-integration-assessment-2026-04-22.md"
  - "_bmad-output/planning-artifacts/research/technical-oidc-fastmcp-authelia-research-2026-04-22.md"
  - "SECURITY.md"
  - "docs/security/threat-model.md"
  - "docs/setup/operations.md"
---

# SoniqMCP Adds Optional Access Control — So Your Speakers Stay Under Your Control

## For users who share a network, host a homelab, or just want the door locked: SoniqMCP now lets you decide who can touch the volume knob.

**Cape Town, April 2026** — SoniqMCP, the open-source MCP server that lets AI assistants control Sonos speakers, today added optional authentication to its HTTP transport. For the majority of users on a trusted home network, nothing changes — the default is still zero configuration. For users who share a LAN with others, run SoniqMCP in a homelab, or want a credential check before any AI agent can skip the track, it's now a three-line config change.

---

Today, anyone on the same network as SoniqMCP's HTTP endpoint can reach it — no password, no token, no questions asked. For a single person with a locked-down home router, that's fine. But for a user who shares Wi-Fi with flatmates, runs an AI automation stack, or exposes SoniqMCP through a homelab ingress, that's an open door. The existing workaround is to put a reverse proxy in front of it. That works, but it adds a dependency, requires separate configuration, and still leaves the question: which service gets in?

---

SoniqMCP v0.6.0 adds an `AUTH_MODE` setting with three options: off (the default, unchanged from today), a static Bearer token (set one secret, share it only with the agents that should have access), or full OIDC JWT validation (bring your own identity provider — Authelia, Authentik, Auth0, anything that issues standard tokens). The static token takes just a few minutes. The OIDC path wires SoniqMCP into whatever SSO stack you're already running. Both are documented. Neither is on by default.

> "SoniqMCP was always designed for your home, not a data centre. That hasn't changed. What's changed is that 'your home' now means different things to different people — shared flats, homelabs, automation pipelines. Optional auth means you can be the one who decides what has access, not whoever happens to be on the same Wi-Fi."
> — Paul Knauer, maintainer

### How It Works

You're running SoniqMCP over HTTP in Docker and you want your AI assistant to be the only thing that can call tools. You set two environment variables: `SONIQ_MCP_AUTH_MODE=static` and `SONIQ_MCP_AUTH_TOKEN=your-secret`. Restart the container. Now any request without that token gets a 401 — no reverse proxy required, no extra service to manage. Your AI assistant adds the token to its MCP client configuration once and never thinks about it again.

If you're in a homelab with Authelia already running, you register SoniqMCP as an OIDC client, set `AUTH_MODE=oidc` and three Authelia-specific env vars, and your AI agent picks up a Bearer token from Authelia the same way it does for every other service in your stack. Centralised access control, key rotation, audit log — all managed in one place.

If you're running stdio, nothing changes. Auth isn't relevant to a process-isolated transport and is silently ignored if you set it.

> "I was already gating everything else in my homelab through Authelia. Having SoniqMCP as the one open endpoint felt wrong. Now it's just another registered client — same pattern, same token flow, no special cases."
> — Homelab operator, 6-node k3s cluster

### Getting Started

**Existing deployments:** No action required. `AUTH_MODE` defaults to `none`. Your current setup is unchanged.

**Static token (a few minutes):**
```
SONIQ_MCP_AUTH_MODE=static
SONIQ_MCP_AUTH_TOKEN=<your-secret>
```

**OIDC (Authelia / Authentik / any standard provider):**
```
SONIQ_MCP_AUTH_MODE=oidc
SONIQ_MCP_OIDC_ISSUER=https://auth.your-homelab.local
SONIQ_MCP_OIDC_AUDIENCE=https://soniq.your-homelab.local
```

Full configuration reference and Authelia client registration example at `docs/setup/authentication.md`.

---

<!-- coaching-notes-stage-1 -->
## Stage 1 Coaching Notes

**Concept type:** open-source project (non-commercial). Framing adapted: "initiative/release" not "product launch", community-member quote not customer quote.

**Customer challenge:** Original framing was "homelab users who run Authelia." Web research and artifact analysis both indicated the real primary customer is broader — any HTTP deployer who shares a LAN or wants credential-based access control. OIDC is the advanced path; static token is the primary path for the majority. Press release leads with the static token story and treats OIDC as the power-user extension.

**Vision tension:** Paul himself flagged this ("I'm not convinced OIDC would be useful to end users running in their home environment"). Research confirmed: opt-in architecture with `AUTH_MODE=none` default resolves the tension. The press release deliberately avoids surfacing auth in the main install story — it exists in its own section and docs.

**Rejected framings considered:**
- "SoniqMCP gets security" — rejected: implies it was insecure before, which is dishonest for the intended use case
- "Enterprise-grade auth for your home Sonos controller" — rejected: jargon, wrong audience signal
- OIDC-first framing — rejected: positions a niche feature as the headline when static token is more broadly relevant

**Key subagent findings that shaped framing:**
- Sonos ecosystem already assumes authenticated control (HA integration requires OAuth) — SoniqMCP is the outlier, not the norm
- Threat model REC-6 already recommended optional bearer token auth — this isn't new thinking, it's catching up to the existing design intent
- VPN solves remote access but NOT shared-LAN trust boundaries — this is the genuine gap being filled
- Homelab operators running Authelia actively expect OIDC client registration as table stakes

**Assumptions challenged:**
- "Most users don't need this" → True for stdio users; less true for HTTP deployers in shared environments
- "OIDC is the right framing" → Static token is the right lead; OIDC is the extension story
- "This conflicts with the simple-install vision" → Only if auth is surfaced in the default path; opt-in architecture resolves it cleanly
<!-- /coaching-notes-stage-1 -->

---

## Customer FAQ

**Q: I already put SoniqMCP behind Nginx with basic auth. Why should I change anything?**

You shouldn't. If your reverse proxy already gates access, it's working — keep it. The static token path is an alternative for users who don't want to manage a reverse proxy at all. Both approaches are valid; this adds a choice, not a mandate.

---

**Q: I'm running stdio — will any of this affect my current setup?**

No. Auth only applies to the HTTP transport. If you're on stdio (the default for most Claude Desktop users), nothing changes. If you set an `AUTH_MODE` env var with stdio, it is silently ignored — no error, no change in behaviour.

---

**Q: If I set a static token and forget it, am I locked out of my own speakers?**

No. Recovery is: restart the container with `AUTH_MODE=none` (or remove the env var), which immediately disables auth and restores full access. Reset your token, update your MCP client config, re-enable. It's documented. You own the container.

---

**Q: I use Claude Desktop. How does it actually send the Bearer token — does that workflow exist today?**

This is an honest limitation to call out. Claude Desktop's built-in MCP client configuration does not currently have a Bearer token field. The static token path is most immediately useful for custom MCP clients, API automation, and pipelines where you control the `Authorization` header. Claude Desktop support depends on how Anthropic evolves their MCP client config schema. The OIDC path (where the client fetches a token from an identity provider) is designed for automation clients that already handle token acquisition. Home users running Claude Desktop over stdio are unaffected — the feature simply isn't relevant to them.

---

**Q: What stops someone who gets hold of my static token from controlling my speakers indefinitely? Is there expiry or rotation?**

Static tokens don't expire by design — this is intentional simplicity. If you need to rotate, change the env var and restart. That's the full rotation mechanism. If you need token expiry and audit logs, that's what the OIDC path is for. Static tokens are for users who want "something between nothing and a full identity provider."

---

**Q: The press release says "any standard OIDC provider." Has this actually been tested with anything other than Authelia?**

The OIDC validation is provider-agnostic — it validates a JWT against a JWKS endpoint using standard RS256 claims (`iss`, `aud`, `exp`). Any provider that issues standard tokens and exposes a JWKS endpoint should work. Authelia is the only provider tested in the maintainer's environment. If your provider doesn't work, open an issue.

---

**Q: What if my CA cert is misconfigured and JWKS fetching fails silently — do I just get mysterious 401s?**

No — this is a hard requirement for launch. SoniqMCP validates OIDC connectivity at startup via `run_preflight()`. If the JWKS endpoint is unreachable (bad CA cert, wrong URL, network issue), the server fails to start with a clear, actionable error message. Silent runtime failures on a misconfigured TLS chain are not acceptable.

---

**Q: Does adding optional auth mean SoniqMCP is changing direction — is this the first step toward something more complex?**

No — and the MCP specification makes this point clearly. The MCP spec (April 2026 draft) now mandates OAuth 2.1 Bearer token validation for HTTP transport servers. SoniqMCP adding optional auth is alignment with the direction the MCP ecosystem is standardising — not a departure from anything. Sonos runs over a network. That network is usually a home, but it's also schools, small offices, homelabs, and shared environments. Optional auth means home users aren't burdened with it; everyone else can opt in to spec-compliant security. The default stays zero-config. Nothing about this project changes for the people it was originally built for.

---

<!-- coaching-notes-stage-3 -->
## Stage 3 Coaching Notes

**Gaps surfaced:**
- Claude Desktop Bearer token support: real limitation — static token is most useful for custom/automation clients, not vanilla Claude Desktop on stdio. Not a launch blocker (stdio users are unaffected) but needs honest documentation.
- OIDC provider coverage: only Authelia tested; answer is transparent about this.

**Trade-off decisions:**
- Static token expiry: accepted trade-off — intentional simplicity, not an oversight. Upgrade path is OIDC.
- Claude Desktop Bearer token: accepted trade-off — scope matches current MCP client ecosystem; document honestly rather than hiding it.

**Startup validation (Q7): launch requirement** — `run_preflight()` must confirm JWKS reachability before the server starts. Clear error message required. Silent 401s on misconfigured TLS are not acceptable.

**MCP spec alignment (Q8):** The April 2026 MCP specification draft mandates OAuth 2.1 for HTTP transport servers. Optional auth in SoniqMCP is ecosystem alignment, not scope creep. This is the strongest argument for doing it.

**Sources:**
- [MCP Authorization Specification](https://modelcontextprotocol.io/specification/draft/basic/authorization)
- [The New MCP Authorization Specification — OAuth 2.1 and Resource Indicators](https://dasroot.net/posts/2026/04/mcp-authorization-specification-oauth-2-1-resource-indicators/)
- [MCP OAuth: How OAuth 2.1 Works in the Model Context Protocol](https://www.prefect.io/resources/mcp-oauth)
<!-- /coaching-notes-stage-3 -->

---

## Internal FAQ

**Q: The technical research found that the original "critical constraint" (FastMCP not exposing ASGI hooks) was wrong. What else in our assessment might be wrong?**

The research process found the error because we inspected the actual installed package rather than relying on the assessment document. The lesson isn't that our assessments are unreliable — it's that we verify against the source before writing stories. The BMAD process caught this before a single line of code was written. That's the workflow functioning correctly. The corrected architecture (one `TokenVerifier` class, ~30 lines, passed to the `FastMCP()` constructor) is simpler than the original plan, not more complex.

---

**Q: `python-jose` was originally recommended, then replaced with `PyJWT`. How stable is the dependency choice?**

`PyJWT` (actively maintained, last release 2024) is the safer long-term choice over `python-jose` (last meaningful activity 2022, known CVE history). The `cryptography` package is already a production dependency — `PyJWT` requires no extras flag and no new transitive dependencies. If `PyJWT` ever became unmaintained, the entire replacement surface is one ~30-line `TokenVerifier` class. The risk is contained.

---

**Q: The MCP spec mandates OAuth 2.1 for HTTP transport. If the spec hardens from optional to required auth, does our implementation become technical debt?**

No. The `TokenVerifier` protocol sits above the transport layer — it's FastMCP's own auth abstraction. If the MCP spec hardens auth to required for HTTP transport, the `AUTH_MODE=none` default would need to change, but the implementation doesn't. The code is aligned with the spec's direction. Shipping optional auth now means we're ahead of any enforcement, not behind it.

---

**Q: Three auth modes sounds clean in a press release. Are we underestimating the real implementation scope?**

The code branches cleanly: `none` is a no-op. `static` is a string comparison (~5 lines). `oidc` is the `TokenVerifier` class (~30 lines, PyJWT). The implementation scope is genuinely small. The documentation is the real investment — `docs/setup/authentication.md` needs to cover all three modes, an Authelia client registration walkthrough, and the CA cert pattern for self-signed TLS. That's the largest single piece of work, and it's writing, not code.

---

**Q: This spans two repos. If the Terraform work in `iot-edge-k3s` blocks, does `sonos-mcp-server` hold the release?**

No. The two repos are independently deployable. `sonos-mcp-server` ships when its own stories are complete — the OIDC validation works against any standards-compliant provider, not just Authelia. The `iot-edge-k3s` Terraform parameterisation is a personal homelab configuration task, not a release gate. Version the repos independently.

---

**Q: If JWKS fetching fails silently on a misconfigured CA cert, it becomes a support burden. What's the standard?**

Preflight validation is a confirmed launch requirement (surfaced in Stage 3). The standard: if `AUTH_MODE=oidc` and the JWKS endpoint is unreachable at startup, the server exits with a message that names the endpoint, the HTTP error or TLS failure, and the likely cause. No silent failures at request time. This is one function in `run_preflight()` and is straightforward to implement and maintain.

---

**Q: You're the sole maintainer. If OIDC users open issues with broken configs across different providers, what's the support boundary?**

This is free software, consumed on that basis. SoniqMCP's responsibility is: validate the JWT correctly against a JWKS endpoint. Provider configuration — Authelia client registration, Authentik scopes, Auth0 audience settings — is the user's domain. The Authelia path is documented thoroughly because it's the tested environment. For every other provider, community-contributed examples are welcome; there is no support SLA. As the project matures, contributors may extend coverage. In the meantime, AI-assisted development increases single-maintainer throughput substantially — the BMAD workflow itself demonstrates this. The support surface is narrower than it appears: most OIDC issues are configuration problems, not bugs.

---

<!-- coaching-notes-stage-4 -->
## Stage 4 Coaching Notes

**Feasibility risks identified:**
- Original assessment error (FastMCP ASGI constraint) was caught by the research process before implementation — the workflow is functioning as intended.
- Dependency choice (`PyJWT` over `python-jose`) is stable and low-risk; `cryptography` already present.

**Scope reality:**
- Code implementation is genuinely small (~30 lines for the OIDC path). Documentation is the largest single investment.
- Two-repo split is not a release dependency — ship `sonos-mcp-server` independently.

**Unknowns resolved:**
- FastMCP ASGI API: resolved (TokenVerifier protocol, confirmed in package).
- MCP spec alignment: confirmed — April 2026 draft mandates OAuth 2.1 for HTTP transport; optional auth now = spec-aligned.
- Support surface: explicitly scoped to free-software terms; Authelia as the documented reference path; contributors welcome.

**Strategic positioning:**
- Solo maintainer with AI-assisted development workflow. This is a structural advantage, not a constraint — feature throughput per maintainer-hour is high.
- Opt-in architecture is the load-bearing design decision: home users unaffected, broader environments supported, spec-compliant.

**No launch blockers identified.** One hard requirement confirmed: startup preflight validation for OIDC connectivity with clear error messages.
<!-- /coaching-notes-stage-4 -->

---

## The Verdict

**Concept strength: Ready to proceed to PRD.**

This concept survived the gauntlet cleanly. The thinking sharpened at every stage, the hard questions produced honest answers, and the one near-crack (Claude Desktop Bearer token support) was scoped honestly rather than hidden. There are no launch blockers.

### Forged in Steel

**The opt-in architecture.** `AUTH_MODE=none` as the default is the load-bearing design decision. It resolves the vision tension completely — home users are unaffected, the simple-install story is unchanged, and auth is genuinely optional. This held up under every angle of questioning.

**MCP spec alignment.** The April 2026 MCP draft mandates OAuth 2.1 for HTTP transport servers. SoniqMCP adding optional auth isn't a departure from the project's character — it's catching up with where the ecosystem is standardising. This is the strongest single argument for doing it.

**Technical simplicity.** The implementation is one `TokenVerifier` class (~30 lines, PyJWT, existing `cryptography` dep). The original assessment's "critical constraint" was wrong — the research process caught it before a line of code was written. The corrected approach is simpler, not more complex.

**Primary customer framing.** Shared-LAN HTTP deployers as the lead persona is correct. Static token is the primary path; OIDC is the power-user extension.

**Support boundary.** "Free software, consumed as such" is a complete and honest policy. The Authelia reference path is documented; everything else is community territory.

### Needs More Heat

**`docs/setup/authentication.md` doesn't exist yet.** The press release promises it. Three modes, Authelia walkthrough, CA cert pattern, startup error messages — this is the largest single investment in the feature. Treat it as a first-class story, not an afterthought.

**The Claude Desktop scope needs one explicit paragraph in docs.** Static token is most useful for custom clients and pipelines, not vanilla Claude Desktop on stdio. Not a bug — but undocumented, it will generate confused issues.

### Cracks in the Foundation

None. The concept is solid. The near-crack around Claude Desktop resolved into a documentation requirement, not a product gap.
