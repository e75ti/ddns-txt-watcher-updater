#!/usr/bin/env bash
set -euo pipefail

SECRETS_FILE="/app/porkbun_secrets.py"

esc() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }

write_secrets() {
  cat > "$SECRETS_FILE" <<EOF
PORKBUN_APIKEY = "$(esc "${1:-}")"
PORKBUN_SECRETAPIKEY = "$(esc "${2:-}")"
PORKBUN_DOMAIN = "$(esc "${3:-}")"
PORKBUN_SUBDOMAIN = "$(esc "${4:-}")"
EOF
  chmod 600 "$SECRETS_FILE"
}

# 1) if file exists, just run
if [ -f "$SECRETS_FILE" ]; then
  exec python /app/check_ip.py
fi

# 2) prefer env vars if any present
if [ -n "${PORKBUN_APIKEY:-}" ] || [ -n "${PORKBUN_SECRETAPIKEY:-}" ] || [ -n "${PORKBUN_DOMAIN:-}" ]; then
  write_secrets "${PORKBUN_APIKEY:-}" "${PORKBUN_SECRETAPIKEY:-}" "${PORKBUN_DOMAIN:-}" "${PORKBUN_SUBDOMAIN:-__ddnsinfo}"
  exec python /app/check_ip.py
fi

# 3) interactive prompt if running attached to a TTY
if [ -t 0 ]; then
  echo "No porkbun_secrets.py and no env vars found — enter values (leave blank to skip)"
  read -rp "PORKBUN_APIKEY: " PORKBUN_APIKEY
  read -rp "PORKBUN_SECRETAPIKEY: " PORKBUN_SECRETAPIKEY
  read -rp "PORKBUN_DOMAIN: " PORKBUN_DOMAIN
  read -rp "PORKBUN_SUBDOMAIN (default __ddnsinfo): " PORKBUN_SUBDOMAIN
  PORKBUN_SUBDOMAIN=${PORKBUN_SUBDOMAIN:-__ddnsinfo}
  write_secrets "${PORKBUN_APIKEY}" "${PORKBUN_SECRETAPIKEY}" "${PORKBUN_DOMAIN}" "${PORKBUN_SUBDOMAIN}"
  exec python /app/check_ip.py
fi

# 4) non-interactive: instruct user and exit
cat >&2 <<EOF
No porkbun_secrets.py and no env vars provided. Provide secrets by one of:
  - pass env vars: -e PORKBUN_APIKEY=... -e PORKBUN_SECRETAPIKEY=... -e PORKBUN_DOMAIN=...
  - use --env-file ./secrets.env
  - mount a gitignored porkbun_secrets.py to /app/porkbun_secrets.py
Run interactively to be prompted: docker run -it ...
EOF
exit 1