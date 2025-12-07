import requests
from typing import Optional, Tuple
from os import getenv

APIKEY = ""
SECRETAPIKEY = ""

PINGURI = "https://api.porkbun.com/api/json/v3/ping"
V4ONLYPINGURI = "https://api-ipv4.porkbun.com/api/json/v3/ping"

NSUPDATEURI = "https://api.porkbun.com/api/json/v3/domain/updateNS/{domain}"
CREATEURI = "https://api.porkbun.com/api/json/v3/dns/create/{domain}"
READURI = "https://api.porkbun.com/api/json/v3/dns/retrieveByNameType/{domain}/{type}/{subdomain}"
UPDATEURI = "https://api.porkbun.com/api/json/v3/dns/editByNameType/{domain}/{type}/{subdomain}"
DELETEURI = "https://api.porkbun.com/api/json/v3/dns/deleteByNameType/{domain}/{type}/{subdomain}"

ALLOWEDTYPES = ["A", "MX", "CNAME", "ALIAS", "TXT", "NS", "AAAA", "SRV", "TLSA", "CAA"]
ALLOWEDTYPES_PRIO = ["SRV", "MX"]

TIMEOUT = 10  # seconds for HTTP requests
session = requests.Session()


class PorkbunError(Exception):
    pass


def _json_or_error(resp: requests.Response) -> dict:
    try:
        data = resp.json()
    except ValueError:
        raise PorkbunError("Invalid JSON response from Porkbun API")
    return data


def _check_error_response(resp: requests.Response) -> None:
    data = _json_or_error(resp)
    if data.get("status") == "ERROR":
        raise PorkbunError(data.get("message", "unknown porkbun error"))


def _resolve_keys(apikey: str, secretapikey: str) -> Tuple[str, str]:
    # Priority: explicit args -> env vars -> module defaults -> error
    if apikey and secretapikey:
        return apikey, secretapikey
    env_api = getenv("PORKBUN_APIKEY", "")
    env_secret = getenv("PORKBUN_SECRETAPIKEY", "")
    if env_api and env_secret:
        return env_api, env_secret
    if APIKEY and SECRETAPIKEY:
        return APIKEY, SECRETAPIKEY
    raise PorkbunError("Porkbun API credentials not provided (args, env, or module defaults)")


def ping(apikey: str = "", secretapikey: str = "", ipv4only: bool = True) -> str:
    apikey, secretapikey = _resolve_keys(apikey, secretapikey)
    payload = {"secretapikey": secretapikey, "apikey": apikey}
    uri = V4ONLYPINGURI if ipv4only else PINGURI
    resp = session.post(uri, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    _check_error_response(resp)
    data = resp.json()
    return data.get("yourIp", "")


def nsupdate(domain: str, nslist: list, apikey: str = "", secretapikey: str = "") -> None:
    apikey, secretapikey = _resolve_keys(apikey, secretapikey)
    payload = {"secretapikey": secretapikey, "apikey": apikey, "ns": nslist}
    resp = session.post(NSUPDATEURI.format(domain=domain), json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    _check_error_response(resp)


def create(domain: str, rtype: str, content: str, apikey: str = "", secretapikey: str = "",
           subdomain: str = "", ttl: int = 600, priority: Optional[int] = None) -> None:
    if rtype not in ALLOWEDTYPES:
        raise PorkbunError(f"Type {rtype} is not supported by Porkbun client")
    apikey, secretapikey = _resolve_keys(apikey, secretapikey)
    payload = {"secretapikey": secretapikey, "apikey": apikey,
               "type": rtype, "name": subdomain, "ttl": ttl, "content": content}
    if priority is not None:
        if rtype not in ALLOWEDTYPES_PRIO:
            raise PorkbunError(f"Type {rtype} does not support priority")
        payload["prio"] = priority
    resp = session.post(CREATEURI.format(domain=domain), json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    _check_error_response(resp)


def read(domain: str, rtype: str, subdomain: str = "", apikey: str = "", secretapikey: str = "") -> list:
    if rtype not in ALLOWEDTYPES:
        raise PorkbunError(f"Type {rtype} is not supported by Porkbun client")
    apikey, secretapikey = _resolve_keys(apikey, secretapikey)
    payload = {"secretapikey": secretapikey, "apikey": apikey}
    resp = session.post(READURI.format(domain=domain, type=rtype, subdomain=subdomain), json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    _check_error_response(resp)
    data = resp.json()
    return data.get("records", [])


def update(domain: str, rtype: str, content: str, subdomain: str = "", apikey: str = "", secretapikey: str = "",
           ttl: int = 600, priority: Optional[int] = None) -> None:
    if rtype not in ALLOWEDTYPES:
        raise PorkbunError(f"Type {rtype} is not supported by Porkbun client")
    apikey, secretapikey = _resolve_keys(apikey, secretapikey)
    payload = {"secretapikey": secretapikey, "apikey": apikey, "content": content, "ttl": ttl}
    if priority is not None:
        if rtype not in ALLOWEDTYPES_PRIO:
            raise PorkbunError(f"Type {rtype} does not support priority")
        payload["prio"] = priority
    resp = session.post(UPDATEURI.format(domain=domain, type=rtype, subdomain=subdomain), json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    _check_error_response(resp)


def delete(domain: str, rtype: str, subdomain: str = "", apikey: str = "", secretapikey: str = "") -> None:
    if rtype not in ALLOWEDTYPES:
        raise PorkbunError(f"Type {rtype} is not supported by Porkbun client")
    apikey, secretapikey = _resolve_keys(apikey, secretapikey)
    payload = {"secretapikey": secretapikey, "apikey": apikey}
    resp = session.post(DELETEURI.format(domain=domain, type=rtype, subdomain=subdomain), json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    _check_error_response(resp)


def ddns_update(domain: str, ip: str = "", subdomain: str = "", apikey: str = "", secretapikey: str = "", ipv4only: bool = True) -> None:
    apikey, secretapikey = _resolve_keys(apikey, secretapikey)
    if ip:
        ipaddr = ip
    else:
        ipaddr = ping(apikey=apikey, secretapikey=secretapikey, ipv4only=ipv4only)
    rtype = "A" if ipv4only or ":" not in ipaddr else "AAAA"
    update(domain, rtype, ipaddr, subdomain=subdomain, apikey=apikey, secretapikey=secretapikey)
