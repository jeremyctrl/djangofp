import argparse
import hashlib
import importlib.resources
import json
import sys
from typing import Any, Optional, Tuple

import requests
from bs4 import BeautifulSoup


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def key_hash(assets: dict[str, Optional[dict[str, Any]]]) -> Tuple[str, list[str]]:
    parts = []
    for key in ("base", "forms", "dashboard", "responsive"):
        asset = assets.get(key)
        if asset:
            parts.append(f"{asset['sha256']}/{asset['size']}")
        else:
            parts.append("null")
    return sha256("||".join(parts).encode()), parts


def build_asset_url(base_url: str, static_path: str, asset_name: str) -> str:
    base = base_url.rstrip("/")
    sp = static_path.strip("/")
    return f"{base}/{sp}/{asset_name}"


def discover_assets(
    base_url: str, asset_keys: Tuple[str, ...] = ("base", "forms", "dashboard", "responsive")
) -> dict[str, str]:
    admin_url = f"{base_url.rstrip('/')}/admin/login/"
    try:
        resp = requests.get(admin_url, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[-] error fetching {admin_url}: {e}")
        return {}

    soup = BeautifulSoup(resp.text, "html.parser")
    links = [link.get("href") for link in soup.find_all("link", rel="stylesheet")]

    found = {}
    for key in asset_keys:
        for link in links:
            if link and f"/{key}" in link:
                found[key] = (
                    link if link.startswith("http") else f"{base_url.rstrip('/')}{link}"
                )
                break
    return found


def fetch_asset(key: str, url: str) -> Optional[dict[str, str | int]]:
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[-] {key}: request error {e}")
        return None

    content = resp.content
    sig = {"size": len(content), "sha256": sha256(content)}
    print(f"[+] {key}: size={sig['size']} sha256={sig['sha256']}")
    return sig


def match_signatures(
    signatures: dict[str, Optional[dict[str, Any]]], db: dict[str, Any]
) -> Tuple[Any, Optional[str], Optional[str]]:
    combo_hash, _ = key_hash(signatures)
    if combo_hash in db:
        return db[combo_hash], "full", combo_hash

    partials = []
    for key, asset in signatures.items():
        if not asset:
            continue
        for db_hash, entry in db.items():
            db_asset = entry["assets"].get(key)
            if db_asset and db_asset == asset:
                partials.append((db_hash, entry, key))

    if partials:
        return partials, "partial", None

    return None, None, None


def main():
    parser = argparse.ArgumentParser(
        prog="djangofp",
        description="Simple Django static-asset version probe",
    )
    parser.add_argument("url", help="Base URL, e.g. https://example.com")
    parser.add_argument(
        "--static-path",
        default="/static/admin/css/",
        help="Static path (default: /static/admin/css/)",
    )
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.1.7")
    args = parser.parse_args()

    try:
        with importlib.resources.open_text("djangofp", "signatures.json") as f:
            db = json.load(f)
    except Exception as e:
        print(f"[-] error loading signatures.json: {e}")
        sys.exit(1)

    asset_urls = {
        key: build_asset_url(args.url, args.static_path, f"{key}.css")
        for key in ("base", "forms", "dashboard", "responsive")
    }
    signatures = {k: fetch_asset(k, u) for k, u in asset_urls.items()}

    if not any(signatures.values()):
        print("[*] static-path lookup failed, falling back to discovery mode...")
        discovered = discover_assets(args.url)
        signatures = {key: fetch_asset(key, url) for key, url in discovered.items()}

    match, match_type, combo_hash = match_signatures(signatures, db)
    if match_type == "full":
        print(f"[+] exact match: {combo_hash}")
        print("\tversions:", ", ".join(match["versions"]))
    elif match_type == "partial":
        print("[*] partial matches found:")
        for db_hash, entry, key in match:
            print(f"\t{key}: versions={', '.join(entry['versions'])}")
    else:
        print("[-] no match found")


if __name__ == "__main__":
    main()
