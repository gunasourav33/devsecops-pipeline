# DevSecOps Pipeline

Security gates integrated into the CI/CD pipeline. This isn't bolted on after the fact — it's part of the workflow from commit to deploy.

## What gets scanned

- **Gitleaks**: Catches secrets that somehow made it into the repo (API keys, certs, tokens)
- **Bandit**: Static analysis on Python code for common security patterns (hardcoded passwords, SQL injection vectors, etc.)
- **Trivy**: Container image vulnerability scan + IaC scan on Dockerfile and Terraform
- **pip-audit**: Checks Python dependencies against known CVEs

Each tool can fail the build on critical issues. Medium severity gets flagged but doesn't block.

## Trade-offs

- **Gitleaks vs other secret scanners**: Gitleaks is fast and covers most cases. Has some false positives on entropy checks but the regex patterns are solid
- **Bandit vs commercial SAST**: Bandit is free and runs in seconds. Misses complex logic flows but catches ~80% of the obvious stuff
- **Trivy vs Snyk**: Trivy is lightweight, no external APIs, no rate limiting. Snyk has better Kubernetes integration but overkill for this setup

## Pipeline triggers

- Every push to main
- Every PR to main
- Weekly scheduled run (Saturdays 03:00 UTC) to catch new CVEs in deps

## Local testing

```bash
# Container scan
trivy image --severity HIGH,CRITICAL <image>

# Filesystem/IaC scan
trivy fs --severity HIGH,CRITICAL .

# Python SAST
bandit -r app/ -ll

# Dependency audit
pip-audit
```

## Secrets config

Set `SLACK_WEBHOOK_URL` in repo secrets for failure notifications. The workflow uses `GITHUB_TOKEN` (automatic) for SARIF uploads to the Security tab.

## Known issues

- Trivy can flag false positives on base OS packages in LTS images — pin base image versions to reduce noise
- Bandit B104 (binding to 0.0.0.0) flags our dev server config — suppressed with `# nosec` where appropriate
