import os
import time
from urllib.request import urlopen
from typing import Optional

import porkbun_api
from ipcrypt import load_key, encrypt_text, DEFAULT_KEY_FILE

# try to load local secrets file (gitignored). env vars take precedence.
try:
    from porkbun_secrets import PORKBUN_APIKEY as _PB_APIKEY, PORKBUN_SECRETAPIKEY as _PB_SECRET, PORKBUN_DOMAIN as _PB_DOMAIN, PORKBUN_SUBDOMAIN as _PB_SUBDOMAIN  # type: ignore
except Exception:
    _PB_APIKEY = _PB_SECRET = _PB_DOMAIN = _PB_SUBDOMAIN = None

# Set your API credentials via env or in code
# resolve order: env -> porkbun_secrets -> empty
PORKBUN_APIKEY = os.environ.get("PORKBUN_APIKEY") or _PB_APIKEY or ""
PORKBUN_SECRETAPIKEY = os.environ.get("PORKBUN_SECRETAPIKEY") or _PB_SECRET or ""

LAST_IP_FILE = os.environ.get("LAST_IP_FILE", "./data/last_ip")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "1800"))  # 30 minutes
IP_SOURCE = os.environ.get("IP_SOURCE", "https://api.ipify.org")
PORKBUN_DOMAIN = os.environ.get("PORKBUN_DOMAIN") or _PB_DOMAIN or ""
PORKBUN_SUBDOMAIN = os.environ.get("PORKBUN_SUBDOMAIN") or _PB_SUBDOMAIN or "_privddns"
KEY_FILE = os.environ.get("KEY_FILE", DEFAULT_KEY_FILE)


def get_public_ip(source: str = IP_SOURCE, timeout: int = 10) -> str:
    with urlopen(source, timeout=timeout) as r:
        return r.read().decode().strip()


def read_last_ip(path: str) -> str:
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def write_last_ip(path: str, ip: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(ip)


def update_txt_token(domain: str, subdomain: str, token: str, apikey: Optional[str] = None, secret: Optional[str] = None) -> None:
    porkbun_api.update(domain=domain, rtype="TXT", content=token, subdomain=subdomain, apikey=apikey or "", secretapikey=secret or "")  # type: ignore[arg-type]


def main():
    if not PORKBUN_DOMAIN:
        print("PORKBUN_DOMAIN environment variable not set; exiting.")
        return

    while True:
        try:
            ip = get_public_ip()
        except Exception as e:
            print("Error fetching public IP:", e)
            time.sleep(CHECK_INTERVAL)
            continue

        last = read_last_ip(LAST_IP_FILE)
        if ip != last:
            print("IP changed:", last or "<none>", "->", ip)
            try:
                key = load_key(KEY_FILE)
                token = encrypt_text(key, ip)
            except Exception as e:
                print("Encryption/key error:", e)
                time.sleep(CHECK_INTERVAL)
                continue

            try:
                # update TXT record on Porkbun (subdomain relative to domain)
                update_txt_token(PORKBUN_DOMAIN, PORKBUN_SUBDOMAIN, token, PORKBUN_APIKEY, PORKBUN_SECRETAPIKEY)
            except Exception as e:
                print("Porkbun update failed:", e)
                # don't write last_ip on failure
                time.sleep(CHECK_INTERVAL)
                continue

            # success: persist ip
            write_last_ip(LAST_IP_FILE, ip)
            print("Updated TXT and saved last IP.")
        else:
            print("IP unchanged:", ip)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()