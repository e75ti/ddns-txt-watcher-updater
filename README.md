# ddns-txt-updater

Watch your public IP and atomically update a single DNS TXT record (e.g. `__ddnsinfo.example.com`) when your IP changes. Supports optional AES encryption of the TXT payload, Docker, and a WIP Ansible deployment + CI/CD ready layout.

## Features
- Monitor public IP and persist last-seen value
- Update a single TXT record (create/edit) via Porkbun API (other providers can be added)
- AES‑GCM encryption for TXT payloads
- Container-friendly; secrets can be provided via env / gitignored secrets file / docker mount
- WIP Ansible playbook for automated host deployment
- WIP CI/CD (GitHub Actions) examples available

## Quickstart (Docker)
1. Add secrets (preferred): create a gitignored `porkbun_secrets.py` or pass env vars.
2. Build:
```bash
docker build -t ddns-txt-updater:latest .
```
3. Run (example):
```bash
docker run -d \
  --name ddns-txt-updater \
  -v "$(pwd)/data":/data \
  -e PORKBUN_APIKEY=pk1_xxx \
  -e PORKBUN_SECRETAPIKEY=sk1_xxx \
  -e PORKBUN_DOMAIN=example.com \
  -e PORKBUN_SUBDOMAIN=__ddnsinfo \
  ddns-txt-updater:latest
```

## Configuration
- Environment variables (override defaults):
  - PORKBUN_APIKEY, PORKBUN_SECRETAPIKEY - credentials for Porkbun
  - PORKBUN_DOMAIN - your domain (required)
  - PORKBUN_SUBDOMAIN - record name (e.g. `__ddnsinfo`); empty for apex
  - LAST_IP_FILE - path to persisted IP (default `/data/last_ip` or `./data/last_ip`)
  - CHECK_INTERVAL - seconds between checks (default 300)
  - KEY_FILE - AES key file path (if using encryption)
- Secrets file (local, gitignored):
  - Add `porkbun_secrets.py` to `.gitignore`.
  - Commit `porkbun_secrets.py.template` (no secrets) as a template.


## APIs list
- Cloudflare: https://github.com/cloudflare/cloudflare-python
- Namecheap (API docs): https://www.namecheap.com/support/api/
- Google Domains (Dynamic DNS docs): https://support.google.com/domains/answer/6147083
- Porkbun: included client in this repo (see `porkbun_api.py`)

TODO: add more providers (PRs welcome).

## WIP: Ansible & Docker
- A WIP Ansible playbook is included to demonstrate automated deploy/pull/run on remote hosts.
- Dockerfile and docker-compose examples available for local/containerized use.
- CI/CD: recommended pipeline builds and pushes container to a registry, then uses Ansible (or SSH) to deploy.

## Security & best practices
- Do NOT commit API keys. Use env vars, docker secrets, or a gitignored local secrets file.
- Restrict API keys and rotate regularly.
- Use minimal privileges for keys when provider supports it.
- Test calls on a disposable/test domain before production changes.

## Contributing
- PRs welcome: add providers, improve tests, add retries/backoff, and CI workflows.
- Please open issues/PRs for provider integrations you want to see.

## Credits
- Porkbun API client and ideas adapted from m3rone/porkbun-api: https://github.com/m3rone/porkbun-api  
  Many thanks to the upstream project - check its repo and license before reusing larger portions of code.

## License
MIT (recommended)
