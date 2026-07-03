#!/usr/bin/env python3
"""
ShortLink Bypass — Universal Multi-Service Bypass Tool
Supports: aylink.co, ay.live, cpmlink.co, cpmlink.pro, linkvertise.com,
          adf.ly, shorte.st, ouo.io, ouo.press, bit.ly, tinyurl.com,
          cutt.ly, is.gd, v.gd, rebrand.ly, t.co, and many more.

Native handlers (no external deps): aylink, cpmlink, linkvertise
Redirect followers: 30+ basic shorteners
Fallback: external APIs for complex social unlock services

Usage:
    python3 bypass.py <shortlink_url> [shortlink_url2 ...]
    python3 bypass.py --batch file.txt

GitHub: https://github.com/KaramelliS/shortlink-bypass
"""

import subprocess, json, re, sys, tempfile, os, urllib.parse, time

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

# ── helpers ──────────────────────────────────────────────────────────

def curl(args, cookie=None, timeout=20):
    """Run curl with optional cookie jar. Returns (stdout, stderr)."""
    cmd = ["curl", "-s", "-L"]
    if cookie:
        cmd += ["-c", cookie, "-b", cookie]
    r = subprocess.run(cmd + args, capture_output=True, text=True, timeout=timeout)
    return r.stdout, r.stderr

def clean_url(url):
    url = url.strip().strip('"').strip("'")
    return url

def follow_bildirim(final, cookie, ref):
    """Follow bildirim.online intermediate → cloud.mail.ru"""
    if "bildirim.online" in final:
        html2, _ = curl([final, "-H", f"User-Agent: {UA}", "-H", f"Referer: {ref}"], cookie)
        m = re.search(r"url\s*=\s*'([^']+)'", html2)
        if m:
            final = m.group(1)
    return final

# ── aylink.co / ay.live ─────────────────────────────────────────────

def bypass_aylink(url):
    print(f"[*] aylink: {url}", file=sys.stderr)
    slug = url.rstrip("/").split("/")[-1]

    if "ay.live" in url:
        out, _ = curl([url, "-o", "/dev/null", "-w", "%{url_effective}", "-H", f"User-Agent: {UA}"])
        slug = out.strip().rstrip("/").split("/")[-1]
        print(f"[*] resolved slug: {slug}", file=sys.stderr)

    cookie = tempfile.mktemp()
    def c(args): return curl(args, cookie)

    html, _ = c([f"https://aylink.co/{slug}", "-H", f"User-Agent: {UA}"])

    _a = re.search(r"_a\s*=\s*'([^']+)'", html)
    _t = re.search(r"_t\s*=\s*'([^']+)'", html)
    _d = re.search(r"_d\s*=\s*'([^']+)'", html)
    csrf = re.search(r'csrf"\s*value="([^"]+)"', html)
    tok = re.search(r"\['token'\]\s*=\s*'([^']+)'", html)
    if not all([_a, _t, _d, csrf, tok]):
        os.remove(cookie)
        return None

    _a, _t, _d = _a.group(1), _t.group(1), _d.group(1)
    csrf_val, tok_val = csrf.group(1), tok.group(1)
    ref = f"https://aylink.co/{slug}"

    # get tk
    tk_raw, _ = c([
        "https://aylink.co/get/tk",
        "-H", f"User-Agent: {UA}", "-H", f"Referer: {ref}",
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
        "t": int(time.time()), "d": 5,
        "m": {"move": 5, "click": 1, "scroll": 1, "key": 0, "touch": 0, "focus": 1},
        "f": {"webdriver": False, "headless": False, "noPlugins": False, "mobile": False},
    })

    go2_raw, _ = c([
        "https://aylink.co/links/go2",
        "-H", f"User-Agent: {UA}", "-H", f"Referer: {ref}",
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

    final = follow_bildirim(final, cookie, ref)
    os.remove(cookie)
    return final

# ── cpmlink.co / cpmlink.pro ────────────────────────────────────────

def bypass_cpmlink(url):
    print(f"[*] cpmlink: {url}", file=sys.stderr)
    cookie = tempfile.mktemp()
    def c(args): return curl(args, cookie)

    html, _ = c([url, "-H", f"User-Agent: {UA}"])

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

    tk_raw, _ = c([
        "https://cpmlink.pro/get/tk",
        "-H", f"User-Agent: {UA}", "-H", f"Referer: {ref}",
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

    signal = json.dumps({
        "t": int(time.time()), "d": 5,
        "m": {"move": 5, "click": 1, "scroll": 1, "key": 0, "touch": 0, "focus": 1},
        "f": {"webdriver": False, "headless": False, "noPlugins": False, "mobile": False},
    })

    go2_raw, _ = c([
        "https://cpmlink.pro/links/go2",
        "-H", f"User-Agent: {UA}", "-H", f"Referer: {ref}",
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

    final = follow_bildirim(final, cookie, ref)
    os.remove(cookie)
    return final

# ── linkvertise.com ──────────────────────────────────────────────────

LINKVERTISE_GRAPHQL = "https://publisher.linkvertise.com/graphql"

# minified GraphQL queries
GDPC_QUERY = ("mutation getDetailPageContent($linkIdentificationInput: PublicLinkIdentificationInput!,"
              "$origin: String, $additional_data: CustomAdOfferProviderAdditionalData!) {"
              "getDetailPageContent(linkIdentificationInput: $linkIdentificationInput,"
              "origin: $origin, additional_data: $additional_data) { access_token }}")

CDPC_QUERY = ("mutation completeDetailPageContent($linkIdentificationInput: PublicLinkIdentificationInput!,"
              "$completeDetailPageContentInput: CompleteDetailPageContentInput!) {"
              "completeDetailPageContent(linkIdentificationInput: $linkIdentificationInput,"
              "completeDetailPageContentInput: $completeDetailPageContentInput) { TARGET }}")

GDPT_QUERY = ("mutation getDetailPageTarget($linkIdentificationInput: PublicLinkIdentificationInput!,"
              "$token: String!) {"
              "getDetailPageTarget(linkIdentificationInput: $linkIdentificationInput,"
              "token: $token) { url }}")


def bypass_linkvertise(url):
    print(f"[*] linkvertise: {url}", file=sys.stderr)
    import requests as req

    parsed = urllib.parse.urlparse(url)
    path = [p for p in parsed.path.strip("/").split("/") if p]
    if len(path) < 2:
        return None
    user_id, post_id = path[0], path[1]

    session = req.Session()
    session.headers.update({
        "User-Agent": UA,
        "Origin": "https://linkvertise.com",
        "Referer": "https://linkvertise.com",
    })

    post_data = {"userIdAndUrl": {"user_id": user_id, "url": post_id}}
    additional = {"taboola": {"user_id": "fallbackUserId", "url": url}}

    # 1) get access token
    r1 = session.post(LINKVERTISE_GRAPHQL, json={
        "operationName": "getDetailPageContent",
        "variables": {
            "linkIdentificationInput": post_data,
            "origin": "sharing",
            "additional_data": additional,
        },
        "query": GDPC_QUERY,
    }, timeout=20)
    r1.raise_for_status()
    d1 = r1.json()
    if "errors" in d1:
        print(f"[!] linkvertise err (access): {d1['errors']}", file=sys.stderr)
        return None
    access_token = d1["data"]["getDetailPageContent"]["access_token"]

    # 2) complete → get post token
    r2 = session.post(LINKVERTISE_GRAPHQL, json={
        "operationName": "completeDetailPageContent",
        "variables": {
            "linkIdentificationInput": post_data,
            "completeDetailPageContentInput": {"access_token": access_token},
        },
        "query": CDPC_QUERY,
    }, timeout=20)
    r2.raise_for_status()
    d2 = r2.json()
    if "errors" in d2:
        print(f"[!] linkvertise err (complete): {d2['errors']}", file=sys.stderr)
        return None
    post_token = d2["data"]["completeDetailPageContent"]["TARGET"]

    # 3) get final URL
    r3 = session.post(LINKVERTISE_GRAPHQL, json={
        "operationName": "getDetailPageTarget",
        "variables": {
            "linkIdentificationInput": post_data,
            "token": post_token,
        },
        "query": GDPT_QUERY,
    }, timeout=20)
    r3.raise_for_status()
    d3 = r3.json()
    if "errors" in d3:
        print(f"[!] linkvertise err (url): {d3['errors']}", file=sys.stderr)
        return None
    return d3["data"]["getDetailPageTarget"]["url"]

# ── redirect followers (simple shorteners) ───────────────────────────

def bypass_redirect(url):
    """Generic redirect follower"""
    print(f"[*] redirect: {url}", file=sys.stderr)
    try:
        out, _ = curl([url, "-o", "/dev/null", "-w", "%{url_effective}", "-H", f"User-Agent: {UA}"])
        final = out.strip()
        if final and final != url:
            return final
    except:
        pass
    return None

def bypass_adfly(url):
    print(f"[*] adfly: {url}", file=sys.stderr)
    try:
        out, _ = curl([url, "-o", "/dev/null", "-w", "%{url_effective}",
                       "-H", f"User-Agent: {UA}", "-e", "https://adf.ly/"])
        final = out.strip()
        if final and final != url:
            return final
    except:
        pass
    return None

def bypass_ouo(url):
    print(f"[*] ouo: {url}", file=sys.stderr)
    try:
        html, _ = curl([url, "-H", f"User-Agent: {UA}"])
        # Look for redirect patterns
        m = re.search(r'window\.location\s*=\s*"([^"]+)"', html)
        if m:
            final = m.group(1)
            if final.startswith("/"):
                base = urllib.parse.urlparse(url)
                final = f"{base.scheme}://{base.netloc}{final}"
            return final
        m = re.search(r'<meta[^>]*url=([^"\s>]+)', html, re.I)
        if m:
            return urllib.parse.unquote(m.group(1))
    except:
        pass
    return bypass_redirect(url)

# ── domain → handler registry ────────────────────────────────────────

DOMAIN_HANDLERS = {
    # Native (token-based) handlers
    "aylink.co": bypass_aylink,
    "ay.live": bypass_aylink,
    "cpmlink.co": bypass_cpmlink,
    "cpmlink.pro": bypass_cpmlink,
    "linkvertise.com": bypass_linkvertise,
    "link-target.net": bypass_linkvertise,
    "link-center.net": bypass_linkvertise,
    "link-hub.net": bypass_linkvertise,
    "direct-link.net": bypass_linkvertise,
    # Simple redirect followers
    "adf.ly": bypass_adfly,
    "adfoc.us": bypass_redirect,
    "shorte.st": bypass_redirect,
    "ouo.io": bypass_ouo,
    "ouo.press": bypass_ouo,
    "bit.ly": bypass_redirect,
    "tinyurl.com": bypass_redirect,
    "cutt.ly": bypass_redirect,
    "is.gd": bypass_redirect,
    "v.gd": bypass_redirect,
    "rebrand.ly": bypass_redirect,
    "t.co": bypass_redirect,
    "rb.gy": bypass_redirect,
    "tiny.one": bypass_redirect,
    "short.link": bypass_redirect,
    "ow.ly": bypass_redirect,
    "buff.ly": bypass_redirect,
    "shorturl.at": bypass_redirect,
    "shrinkearn.com": bypass_redirect,
    "shrinkme.io": bypass_redirect,
    "linkbucks.com": bypass_redirect,
    "bc.vc": bypass_redirect,
    "soo.gd": bypass_redirect,
    "mcaf.ee": bypass_redirect,
    "clck.ru": bypass_redirect,
    "0x0.st": bypass_redirect,
    "gg.gg": bypass_redirect,
    "shorte.st": bypass_redirect,
    "tiny.cc": bypass_redirect,
    "youtu.be": bypass_redirect,
    "fb.me": bypass_redirect,
    "lnkd.in": bypass_redirect,
}

# Services that need external API or browser (listed for --list-services)
FALLBACK_ONLY = [
    "work.ink", "workink.click", "boost.ink", "mboost.me", "rekonise.com",
    "lootlabs.com", "lootlinks.com", "loot-link.com",
    "sub2unlock.com", "sub2unlock.net", "sub2unlock.io",
    "sub2get.com", "sub4unlock.com", "sub4unlock.pro", "subfinal.com",
    "social-unlock.com", "socialwolvez.com", "lockr.social",
    "just2earn.com", "gplinks.in", "gplinks.co",
    "try2link.com", "shareus.in", "droplink.co",
    "tnlink.in", "xpshort.com", "ez4short.com",
    "rocklinks.net", "gtlinks.me", "pkin.me",
]

def get_handler(url):
    """Find handler for URL. Returns (handler_func, handler_type) or (None, reason)."""
    domain = urllib.parse.urlparse(url).netloc.lower()
    # exact match or substring
    for key, handler in DOMAIN_HANDLERS.items():
        if key in domain:
            return handler, "native"
    for svc in FALLBACK_ONLY:
        if svc in domain:
            return None, "fallback_only"
    return bypass_redirect, "generic"

# ── main ─────────────────────────────────────────────────────────────

LIST_SERVICES_FLAG = "--list-services"

def bypass(url):
    """Try to bypass a single URL"""
    url = clean_url(url)
    if not url.startswith("http"):
        url = "https://" + url

    handler, htype = get_handler(url)
    if handler:
        try:
            result = handler(url)
            if result:
                return result.strip()
        except Exception as e:
            print(f"[!] {type(e).__name__}: {e}", file=sys.stderr)
    return None

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <shortlink_url> [shortlink_url2 ...]", file=sys.stderr)
        print(f"       {sys.argv[0]} --batch <file>", file=sys.stderr)
        print(f"       {sys.argv[0]} --list-services", file=sys.stderr)
        sys.exit(1)

    if LIST_SERVICES_FLAG in sys.argv:
        native = sorted(k for k, v in DOMAIN_HANDLERS.items())
        fallback = sorted(FALLBACK_ONLY)
        print("=== Native Handlers ===")
        for d in native:
            print(f"  {d}")
        print(f"\n=== Fallback Only (no native handler yet) ===")
        for d in fallback:
            print(f"  {d}")
        print(f"\nTotal: {len(native)} native + {len(fallback)} fallback = {len(native)+len(fallback)} services")
        sys.exit(0)

    urls = []
    if sys.argv[1] == "--batch" and len(sys.argv) > 2:
        with open(sys.argv[2]) as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    else:
        urls = [a for a in sys.argv[1:] if not a.startswith("--")]

    for url in urls:
        result = bypass(url)
        if result:
            print(result)
        else:
            print(f"[-] Failed: {url}", file=sys.stderr)

if __name__ == "__main__":
    main()
