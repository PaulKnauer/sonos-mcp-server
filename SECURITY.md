# Security Policy

## Supported Versions

SoniqMCP is in active development. Security fixes are applied to the latest released version only. Operators should update to the latest version when security issues are addressed.

## Deployment Posture

SoniqMCP defaults to no built-in authentication (`auth_mode=none`) and is designed for local or trusted home-network deployment. Optional HTTP authentication is available: `auth_mode=static` (shared bearer token) or `auth_mode=oidc` (OIDC JWT validation). Stdio deployments always ignore auth settings regardless of configuration. See [docs/setup/authentication.md](docs/setup/authentication.md) for the full auth guide.

Supported deployment targets:

- **Local stdio** — same-machine AI client (Claude Desktop) only; no network exposure, auth is always a no-op
- **Docker HTTP** — Linux home-lab server on a trusted home network; optional auth available
- **Helm / k3s HTTP** — self-hosted cluster on a trusted home network; optional auth available via chart values

**Remote or internet-facing exposure is not supported by default.** If you expose the MCP endpoint beyond a trusted home network, add boundary protection at the deployment edge using one or more of: reverse proxy with authentication, ingress authentication (e.g., OAuth2 proxy, `nginx.ingress.kubernetes.io/auth-*` annotations), network ACLs, or VPN-only access. Built-in auth is a credential layer, not a substitute for network isolation.

See [docs/setup/operations.md](docs/setup/operations.md) for the full operator guidance on supported exposure boundaries, release artifacts, and upgrade expectations.

## Threat Model

For a detailed analysis of assets, threat actors, attack surfaces, STRIDE threat scenarios, and recommended mitigations, see [docs/security/threat-model.md](docs/security/threat-model.md).

## Scope

**In scope for security reports:**

- Authentication bypass or privilege escalation via the MCP tool surface
- Input that allows unauthorised Sonos control beyond the connected household
- Secrets, credentials, or private host details leaked in log output or tool responses
- Dependency vulnerabilities with a direct exploitable path in the default deployment

**Out of scope:**

- Attacks that require physical access to the Sonos network or the machine running SoniqMCP
- Issues that require the operator to deliberately misconfigure boundary protection (e.g., exposing the MCP endpoint publicly without adding authentication)
- Denial-of-service via network flooding
- Vulnerabilities in Sonos devices themselves

## Reporting a Vulnerability

Use [GitHub private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) to submit a report privately:

1. Go to the repository **Security** tab
2. Click **Report a vulnerability**
3. Describe the issue, affected component, and reproduction steps

Do not open a public GitHub issue for security vulnerabilities.

## Coordinated Disclosure

After a report is received:

- We aim to acknowledge receipt within 5 business days
- We will confirm and reproduce the issue
- Fixes will be released as soon as practical
- We will coordinate with reporters on disclosure timing before publishing details publicly
