#!/usr/bin/env python3
"""
ShortLink Bypass — ay.live / aylink.co / cpmlink.co / cpmlink.pro
Usage:
    python3 bypass.py <shortlink_url>
"""

import subprocess, json, re, sys, tempfile, os, urllib.parse

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

# ── helpers ──────────────────────────────────────────────────────────

def curl(args, cookie=None):
    """Run curl with optional cookie jar. Returns (stdout, stderr)."""
    cmd = ["curl", "-s", "-L"]
    if cookie:
        cmd += ["-c", cookie, "-b", cookie]
    r = subprocess.run(cmd + args, capture_output=True, text=True, timeout=20)
    return r.stdout, r.stderr


# ── aylink.co / ay.live ─────────────────────────────────────────────

def bypass_aylink(url):
    """Bypass aylink.co or ay.live shortlinks."""
    print(f"[*] aylink: {url}", file=sys.stderr)
    slug = url.rstrip("/").split("/")[-1]

    # ay.live redirects to aylink.co/{slug}
    if "ay.live" in url:
        out, _ = curl([
            url, "-o", "/dev/null", "-w", "%{url_effective}",
            "-H", f"User-Agent: {UA}"
        ])
        slug = out.strip().rstrip("/").split("/")[-1]
        print(f"[*] resolved slug: {slug}", file=sys.stderr)

    cookie = tempfile.mktemp()

    def c(args):
        return curl(args, cookie)

    # fetch landing page
    html, _ = c([
        f"https://aylink.co/{slug}",
        "-H", f"User-Agent: {UA}"
    ])

    # extract tokens
    _a = re.search(r"_a\s*=\s*'([^']+)'", html)
    _t = re.search(r"_t\s*=\s*'([^']+)'", html)
    _d = re.search(r"_d\s*=\s*'([^']+)'", html)
    csrf = re.search(r'csrf"\s*value="([^"]+)"', html)
    tok = re.search(r"\['token'\]\s*=\s*'([^']+)'", html)
    if not all([_a, _t, _d, csrf, tok]):
        os.remove(cookie)
        return None

    _a, _t, _d = _a.group(1), _t.group(1), _d.group(1)
    csrf_val = csrf.group(1)
    tok_val = tok.group(1)
    ref = f"https://aylink.co/{slug}"

    # get tk
    tk_raw, _ = c([
        "https://aylink.co/get/tk",
        "-H", f"User-Agent: {UA}",
        "-H", f"Referer: {ref}",
        "-H", "X-Requested-With: XMLHttpRequest",
        "-H", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
        "-H", "Accept: application/json, text/javascript, */*; q=0.01",
        "-H", "Origin: https://aylink.co",
        "--data-urlencode", f"_a={_a}",
        "--data-urlencode", f"_t={_t}",
        "--data-urlencode", f"_d={_d}",
    ])
    try:
        tk_val = json.loads(tk_raw)["th"]
    except (KeyError, json.JSONDecodeError):
        os.remove(cookie)
        return None

    # hit /links/go2
    signal = json.dumps({
        "t": 1719154800, "d": 5,
        "m": {"move": 5, "click": 1, "scroll": 1, "key": 0, "touch": 0, "focus": 1},
        "f": {"webdriver": False, "headless": False, "noPlugins": False, "mobile": False},
    })

    go2_raw, _ = c([
        "https://aylink.co/links/go2",
        "-H", f"User-Agent: {UA}",
        "-H", f"Referer: {ref}",
        "-H", "X-Requested-With: XMLHttpRequest",
        "-H", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
        "-H", "Accept: application/json, text/javascript, */*; q=0.01",
        "-H", "Origin: https://aylink.co",
        "--data-urlencode", f"alias={slug}",
        "--data-urlencode", f"csrf={csrf_val}",
        "--data-urlencode", f"tkn={tk_val}",
        "--data-urlencode", f"visitor_token={tok_val}",
        "--data-urlencode", f"signal={signal}",
    ])

    try:
        final = json.loads(go2_raw).get("url", "")
    except json.JSONDecodeError:
        os.remove(cookie)
        return None

    # follow bildirim.online → cloud.mail.ru
    if "bildirim.online" in final:
        html2, _ = c([final, "-H", f"User-Agent: {UA}", "-H", f"Referer: {ref}"])
        m = re.search(r"url\s*=\s*'([^']+)'", html2)
        if m:
            final = m.group(1)

    os.remove(cookie)
    return final


# ── cpmlink.co / cpmlink.pro ────────────────────────────────────────

def bypass_cpmlink(url):
    """Bypass cpmlink.co or cpmlink.pro shortlinks."""
    print(f"[*] cpmlink: {url}", file=sys.stderr)
    cookie = tempfile.mktemp()

    def c(args):
        return curl(args, cookie)

    # fetch landing page
    html, _ = c([url, "-H", f"User-Agent: {UA}"])

    # extract tokens
    _a = re.search(r"_a\s*=\s*'([^']+)'", html)
    _t = re.search(r"_t\s*=\s*'([^']+)'", html)
    _d = re.search(r"_d\s*=\s*'([^']+)'", html)
    csrf = re.search(r'csrf"\s*value="([^"]+)"', html)
    vtoken = re.search(r"app\['token'\]\s*=\s*'([^']+)'", html)
    alias = re.search(r"app\['alias'\]\s*=\s*'([^']+)'", html)
    if not all([_a, _t, _d, csrf, vtoken, alias]):
        os.remove(cookie)
        return None

    _a, _t, _d = _a.group(1), _t.group(1), _d.group(1)
    csrf_val, vtoken_val = csrf.group(1), vtoken.group(1)
    slug = alias.group(1)
    ref = f"https://cpmlink.pro/{slug}"

    # get tk
    tk_raw, _ = c([
        "https://cpmlink.pro/get/tk",
        "-H", f"User-Agent: {UA}",
        "-H", f"Referer: {ref}",
        "-H", "X-Requested-With: XMLHttpRequest",
        "-H", "Accept: application/json, text/javascript, */*; q=0.01",
        "-H", "Origin: https://cpmlink.pro",
        "--data", f"_a={_a}&_t={_t}&_d={_d}",
    ])
    try:
        tk_val = json.loads(tk_raw)["th"]
    except (KeyError, json.JSONDecodeError):
        os.remove(cookie)
        return None

    # hit /links/go2
    signal = json.dumps({
        "t": 1719154800, "d": 5,
        "m": {"move": 5, "click": 1, "scroll": 1, "key": 0, "touch": 0, "focus": 1},
        "f": {"webdriver": False, "headless": False, "noPlugins": False, "mobile": False},
    })

    go2_raw, _ = c([
        "https://cpmlink.pro/links/go2",
        "-H", f"User-Agent: {UA}",
        "-H", f"Referer: {ref}",
        "-H", "X-Requested-With: XMLHttpRequest",
        "-H", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
        "-H", "Accept: application/json, text/javascript, */*; q=0.01",
        "-H", "Origin: https://cpmlink.pro",
        "--data", f"alias={slug}&csrf={csrf_val}&tkn={tk_val}&visitor_token={vtoken_val}&signal={urllib.parse.quote(signal)}",
    ])

    try:
        final = json.loads(go2_raw).get("url", "")
    except json.JSONDecodeError:
        os.remove(cookie)
        return None

    # follow bildirim.online → cloud.mail.ru
    if "bildirim.online" in final:
        html2, _ = c([final, "-H", f"User-Agent: {UA}", "-H", f"Referer: {ref}"])
        m = re.search(r"url\s*=\s*'([^']+)'", html2)
        if m:
            final = m.group(1)

    os.remove(cookie)
    return final


# ── main ─────────────────────────────────────────────────────────────

DOMAINS = {
    "aylink.co": bypass_aylink,
    "ay.live": bypass_aylink,
    "cpmlink.co": bypass_cpmlink,
    "cpmlink.pro": bypass_cpmlink,
}


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <shortlink_url> [shortlink_url2 ...]", file=sys.stderr)
        sys.exit(1)

    for arg in sys.argv[1:]:
        url = arg.strip()
        domain = urllib.parse.urlparse(url).netloc.lower()
        handler = DOMAINS.get(domain)

        if not handler:
            # try matching substrings
            for key, h in DOMAINS.items():
                if key in url:
                    handler = h
                    break
        if not handler:
            print(f"[-] Unsupported domain: {domain}", file=sys.stderr)
            print(url)
            continue

        result = handler(url)
        if result:
            print(result)
        else:
            print(f"[-] Failed to bypass: {url}", file=sys.stderr)


if __name__ == "__main__":
    main()
