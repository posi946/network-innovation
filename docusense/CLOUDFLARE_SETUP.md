# Cloudflare setup for DocuSense (Day 3)

1. Add `docusense.africa` to Cloudflare and point nameservers at Cloudflare.
2. Ensure `api.docusense.africa` and `docusense.africa` are **proxied** (orange cloud).
3. **WAF** → enable the OWASP Core Ruleset at Paranoia Level 1.
4. Enable **Bot Fight Mode**.
5. **Rules → Rate Limiting**: 100 requests/minute per IP on `api.docusense.africa`.
6. **SSL/TLS → Overview → Encryption Mode: Full (strict)**.
7. **Edge Certificates → Always Use HTTPS: On**.
8. **HSTS**: enable with a 6-month max-age, include subdomains.

Never expose the origin IP: keep the origin firewalled to Cloudflare ranges only.
