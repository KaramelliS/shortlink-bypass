#!/usr/bin/env python3
"""
ShortLink Bypass — Universal Multi-Service Bypass Tool
Native handlers for 90+ shortlink services. No browser, no ads.

Usage:
    python3 bypass.py <shortlink_url> [shortlink_url2 ...]
    python3 bypass.py --batch file.txt
    python3 bypass.py --list-services

GitHub: https://github.com/KaramelliS/shortlink-bypass
"""

import subprocess, json, re, sys, tempfile, os, urllib.parse, time

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
MOBILE_UA = "Mozilla/5.0 (Linux; Android 11; 2201116PI) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36"

# ── helpers ──────────────────────────────────────────────────────────

def curl(args, cookie=None, timeout=30):
    cmd = ["curl", "-s", "-L"]
    if cookie:
        cmd += ["-c", cookie, "-b", cookie]
    r = subprocess.run(cmd + args, capture_output=True, text=True, timeout=timeout)
    return r.stdout, r.stderr

def clean_url(url):
    url = url.strip().strip('"').strip("'")
    return url

def follow_bildirim(final, cookie, ref):
    if "bildirim.online" in final:
        html2, _ = curl([final, "-H", f"User-Agent: {UA}", "-H", f"Referer: {ref}"], cookie)
        m = re.search(r"url\s*=\s*'([^']+)'", html2)
        if m:
            final = m.group(1)
    return final

def extract_form_inputs(html):
    """Extract all input name/value pairs from a form, or just all inputs"""
    data = {}
    for m in re.finditer(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"', html):
        data[m.group(1)] = m.group(2)
    for m in re.finditer(r'<input[^>]*value="([^"]*)"[^>]*name="([^"]*)"', html):
        data[m.group(2)] = m.group(1)
    return data

def go_link_post(cookie, domain, slug, data, ref=None, timeout=15, skip_sleep=False):
    """POST to /links/go and return URL from JSON"""
    if not skip_sleep:
        time.sleep(0.5)
    hdrs = [
        "-H", f"User-Agent: {UA}",
        "-H", "X-Requested-With: XMLHttpRequest",
        "-H", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
    ]
    if ref:
        hdrs += ["-H", f"Referer: {ref}"]

    body = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in data.items())
    raw, _ = curl([
        f"{domain.rstrip('/')}/links/go",
    ] + hdrs + ["--data", body], cookie, timeout)
    try:
        return json.loads(raw).get("url", "")
    except json.JSONDecodeError:
        return None

def try_import_requests():
    global requests
    try:
        import requests as _r
        requests = _r
        return True
    except ImportError:
        requests = None
        return False

# ═══════════════════════════════════════════════════════════════════
# native handlers — aylink / cpmlink
# ═══════════════════════════════════════════════════════════════════

def bypass_aylink(url):
    print(f"[*] aylink: {url}", file=sys.stderr)
    slug = url.rstrip("/").split("/")[-1]
    if "ay.live" in url:
        out, _ = curl([url, "-o", "/dev/null", "-w", "%{url_effective}", "-H", f"User-Agent: {UA}"])
        slug = out.strip().rstrip("/").split("/")[-1]

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

    tk_raw, _ = c([
        "https://aylink.co/get/tk",
        "-H", f"User-Agent: {UA}", "-H", f"Referer: {ref}",
        "-H", "X-Requested-With: XMLHttpRequest",
        "-H", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
        "-H", "Accept: application/json, text/javascript, */*; q=0.01",
        "-H", "Origin: https://aylink.co",
        "--data-urlencode", f"_a={_a}", "--data-urlencode", f"_t={_t}", "--data-urlencode", f"_d={_d}",
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
        "https://aylink.co/links/go2",
        "-H", f"User-Agent: {UA}", "-H", f"Referer: {ref}",
        "-H", "X-Requested-With: XMLHttpRequest",
        "-H", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
        "-H", "Accept: application/json, text/javascript, */*; q=0.01",
        "-H", "Origin: https://aylink.co",
        "--data-urlencode", f"alias={slug}", "--data-urlencode", f"csrf={csrf_val}",
        "--data-urlencode", f"tkn={tk_val}", "--data-urlencode", f"visitor_token={tok_val}",
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

# ═══════════════════════════════════════════════════════════════════
# native handler — linkvertise (GraphQL)
# ═══════════════════════════════════════════════════════════════════

LINKVERTISE_GRAPHQL = "https://publisher.linkvertise.com/graphql"
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
    if not try_import_requests():
        return None
    parsed = urllib.parse.urlparse(url)
    path = [p for p in parsed.path.strip("/").split("/") if p]
    if len(path) < 2: return None
    user_id, post_id = path[0], path[1]

    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Origin": "https://linkvertise.com", "Referer": "https://linkvertise.com"})
    post_data = {"userIdAndUrl": {"user_id": user_id, "url": post_id}}
    additional = {"taboola": {"user_id": "fallbackUserId", "url": url}}

    try:
        r1 = session.post(LINKVERTISE_GRAPHQL, json={
            "operationName": "getDetailPageContent", "variables": {
                "linkIdentificationInput": post_data, "origin": "sharing", "additional_data": additional,
            }, "query": GDPC_QUERY,
        }, timeout=20)
        r1.raise_for_status()
        d1 = r1.json()
        if "errors" in d1: return None
        access_token = d1["data"]["getDetailPageContent"]["access_token"]

        r2 = session.post(LINKVERTISE_GRAPHQL, json={
            "operationName": "completeDetailPageContent", "variables": {
                "linkIdentificationInput": post_data,
                "completeDetailPageContentInput": {"access_token": access_token},
            }, "query": CDPC_QUERY,
        }, timeout=20)
        r2.raise_for_status()
        d2 = r2.json()
        if "errors" in d2: return None
        post_token = d2["data"]["completeDetailPageContent"]["TARGET"]

        r3 = session.post(LINKVERTISE_GRAPHQL, json={
            "operationName": "getDetailPageTarget", "variables": {
                "linkIdentificationInput": post_data, "token": post_token,
            }, "query": GDPT_QUERY,
        }, timeout=20)
        r3.raise_for_status()
        d3 = r3.json()
        if "errors" in d3: return None
        return d3["data"]["getDetailPageTarget"]["url"]
    except Exception as e:
        print(f"[!] linkvertise: {e}", file=sys.stderr)
        return None

# ═══════════════════════════════════════════════════════════════════
# generic go-link form bypass (Type 1 — Indian shorteners)
# ═══════════════════════════════════════════════════════════════════

# Type 1 config: {domain_prefix: [form_domain, sleep_secs]}
TYPE1_CONFIG = {
    "tekcrypt.in/tek/": ["https://tekcrypt.in/tek/", 5],
    "link.short2url.in/": ["https://technemo.xyz/blog/", 5],
    "go.rocklinks.net/": ["https://dwnld.povathemes.com/", 5],
    "rocklinks.net/": ["https://dwnld.povathemes.com/", 5],
    "gtlinks.me/": ["https://gtlinks.me/", 5],
    "loan.kinemaster.cc/": ["https://loan.kinemaster.cc/", 5],
    "theforyou.in/": ["https://www.theforyou.in/", 5],
    "safeurl.sirigan.my.id/": ["https://safeurl.sirigan.my.id/", 5],
    "thinfi.com/": ["https://thinfi.com/", 5],
    "hypershort.com/": ["https://hypershort.com/", 5],
    "shortly.xyz/": ["https://www.shortly.xyz/", 5],
    "za.uy/": ["https://za.uy/", 5],
    # These may share the same backend pattern
    "bitlyearn.in/": ["https://bitlyearn.in/", 7],
}

# Type 2 config: {domain_prefix: [form_domain, referer_domain, sleep_secs]}
TYPE2_CONFIG = {
    "droplink.co/": ["https://droplink.co/", "https://yoshare.net", 4],
    "earn4link.in/": ["https://m.open2get.in/", "https://ezeviral.com/", 3],
    "tnlink.in/": ["https://gadgets.usanewstoday.club/", "https://usanewstoday.club/", 5],
    "ez4short.com/": ["https://ez4short.com/", "https://techmody.io/", 5],
    "xpshort.com/": ["https://push.bdnewsx.com/", "https://veganho.co/", 5],
    "vearnl.in/": ["https://go.urlearn.xyz/", "https://v.modmakers.xyz/", 5],
    "adrinolinks.in/": ["https://adrinolinks.in/", "https://wikitraveltips.com/", 5],
    "techymozo.com/": ["https://push.bdnewsx.com/", "https://veganho.co/", 5],
    "linkbnao.com/": ["https://go.linkbnao.com/", "https://doibihar.org/", 5],
    "linksxyz.in/": ["https://blogshangrila.com/insurance/", "https://cypherroot.com/", 5],
    "short-jambo.com/": ["https://short-jambo.com/", "https://aghtas.com/", 5],
    "ads.droplink.co.in/": ["https://go.droplink.co.in/", "https://go.droplink.co.in/", 5],
    "linkpays.in/": ["https://m.techpoints.xyz//", "https://www.filmypoints.in/", 5],
    "pi-l.ink/": ["https://go.pilinks.net/", "https://poketoonworld.com/", 5],
    "link.tnlink.in/": ["https://gadgets.usanewstoday.club/", "https://usanewstoday.club/", 5],
    "open2get.in/": ["https://m.open2get.in/", "https://ezeviral.com/", 3],
    "mdiskshortner.link/": ["https://mdiskshortner.link/", "https://mdiskshortner.link/", 5],
    "pdiskshortener.com/": ["https://pdiskshortener.com/", "https://pdiskshortener.com/", 5],
    "go.earnl.xyz/": ["https://go.earnl.xyz/", "https://v.earnl.xyz/", 5],
    "g.rewayatcafe.com/": ["https://course.rewayatcafe.com/", "https://course.rewayatcafe.com/", 5],
    "indianshortner.in/": ["https://indianshortner.com/", "https://indianshortner.com/", 5],
    "m.easysky.in/": ["https://techy.veganab.co/", "https://techy.veganab.co/", 5],
    "earn.moneykamalo.com/": ["https://go.moneykamalo.com//", "https://go.moneykamalo.com/", 5],
    "open.crazyblog.in/": ["https://hr.vikashmewada.com/", "https://hr.vikashmewada.com/", 5],
    "link.tnvalue.in/": ["https://internet.webhostingtips.club/", "https://internet.webhostingtips.club/", 5],
    "shortingly.me/": ["https://go.techyjeeshan.xyz/", "https://go.techyjeeshan.xyz/", 5],
    "dulink.in/": ["https://tekcrypt.in/tek/", "https://tekcrypt.in/tek/", 10],
    "bindaaslinks.com/": ["https://www.techishant.in/blog/", "https://www.techishant.in/blog/", 5],
    "ser2.crazyblog.in/": ["https://ser3.crazyblog.in/", "https://ser3.crazyblog.in/", 5],
    "bitshorten.com/": ["https://bitshorten.com/", "https://bitshorten.com/", 5],
    "rocklink.in/": ["https://rocklink.in/", "https://rocklink.in/", 5],
    "link.short2url.in/": ["https://technemo.xyz/blog/", "https://technemo.xyz/blog/", 5],
}

def bypass_type1(url):
    """Type 1: form with id=go-link, POST to /links/go"""
    print(f"[*] type1: {url}", file=sys.stderr)
    domain = urllib.parse.urlparse(url).netloc.lower()
    slug = url.rstrip("/").split("/")[-1]

    form_domain = sleep = None
    for key, cfg in {**TYPE1_CONFIG, **TYPE2_CONFIG}.items():
        if key in url.replace("http://", "https://"):
            form_domain = cfg[0]
            sleep = cfg[-1]
            break
    if not form_domain:
        form_domain = f"https://{domain}/"
        sleep = 7

    cookie = tempfile.mktemp()
    def c(args): return curl(args, cookie)

    ref = form_domain + slug
    html, _ = c([ref, "-H", f"User-Agent: {UA}", "-H", f"Referer: {form_domain}"])

    data = extract_form_inputs(html)
    if not data:
        os.remove(cookie)
        return None

    time.sleep(sleep)
    raw, _ = c([
        f"{form_domain.rstrip('/')}/links/go",
        "-H", f"User-Agent: {UA}",
        "-H", "X-Requested-With: XMLHttpRequest",
        "-H", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
        "-H", f"Referer: {ref}",
        "--data", "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in data.items()),
    ], cookie, 15)
    try:
        final = json.loads(raw).get("url", "")
        os.remove(cookie)
        return final if final else None
    except json.JSONDecodeError:
        os.remove(cookie)
        return None

# ═══════════════════════════════════════════════════════════════════
# specific shortener handlers
# ═══════════════════════════════════════════════════════════════════

def bypass_try2link(url):
    """try2link.com — timestamp param + form flow"""
    print(f"[*] try2link: {url}", file=sys.stderr)
    cookie = tempfile.mktemp()
    url = url.rstrip("/")
    try:
        params = f"?d={int(time.time()) + 240}"
        html, _ = curl([url + params, "-H", f"User-Agent: {UA}", "-H", "Referer: https://newforex.online/"], cookie)
        data = extract_form_inputs(html)
        if not data:
            os.remove(cookie)
            return None
        time.sleep(7)
        raw, _ = curl([
            "https://try2link.com/links/go",
            "-H", f"User-Agent: {UA}",
            "-H", "Host: try2link.com",
            "-H", "X-Requested-With: XMLHttpRequest",
            "-H", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
            "-H", f"Referer: {url}",
            "-H", "Origin: https://try2link.com",
            "--data", "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in data.items()),
        ], cookie, 15)
        os.remove(cookie)
        d = json.loads(raw)
        return d.get("url")
    except Exception:
        try:
            os.remove(cookie)
        except: pass
        return None

def bypass_gplinks(url):
    """gplinks.co / gplinks.in — redirect -> vid param -> form flow"""
    print(f"[*] gplinks: {url}", file=sys.stderr)
    cookie = tempfile.mktemp()
    url = url.rstrip("/")
    try:
        out, _ = curl([url, "-o", "/dev/null", "-w", "%{redirect_url}", "-H", f"User-Agent: {UA}"], cookie)
        vid = out.split("=")[-1].strip() if "=" in out else ""
        url2 = f"{url}/?{vid}" if vid else url

        html, _ = curl([url2, "-H", f"User-Agent: {UA}", "-H", "Referer: https://mynewsmedia.co/"], cookie)
        data = extract_form_inputs(html)
        if not data:
            os.remove(cookie)
            return None
        time.sleep(8)
        raw, _ = curl([
            "https://gplinks.co/links/go",
            "-H", f"User-Agent: {UA}",
            "-H", "X-Requested-With: XMLHttpRequest",
            "-H", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
            "-H", f"Referer: {url2}",
            "--data", "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in data.items()),
        ], cookie, 15)
        os.remove(cookie)
        d = json.loads(raw)
        return d.get("url")
    except Exception:
        try:
            os.remove(cookie)
        except: pass
        return None

def bypass_pkin(url):
    """pkin.me — mobile UA + go.paisakamalo.in form flow"""
    print(f"[*] pkin: {url}", file=sys.stderr)
    cookie = tempfile.mktemp()
    slug = url.rstrip("/").split("/")[-1]
    domain = "https://go.paisakamalo.in/"
    try:
        html, _ = curl([domain + slug, "-H", f"User-Agent: {MOBILE_UA}", "-H", "Referer: https://techkeshri.com/"], cookie)
        data = extract_form_inputs(html)
        if not data:
            os.remove(cookie)
            return None
        time.sleep(5)
        raw, _ = curl([
            f"{domain}links/go",
            "-H", f"User-Agent: {MOBILE_UA}",
            "-H", "X-Requested-With: XMLHttpRequest",
            "-H", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
            "-H", f"Referer: {domain + slug}",
            "--data", "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in data.items()),
        ], cookie, 15)
        os.remove(cookie)
        d = json.loads(raw)
        return d.get("url")
    except Exception:
        try:
            os.remove(cookie)
        except: pass
        return None

def bypass_shareus(url):
    """shareus.in — Firebase Cloud Function"""
    print(f"[*] shareus: {url}", file=sys.stderr)
    token = url.split("=")[-1]
    try:
        out, _ = curl([f"https://us-central1-my-apps-server.cloudfunctions.net/r?shortid={token}", "-H", f"User-Agent: {UA}"])
        return out.strip()
    except Exception:
        return None

def bypass_shortly(url):
    """shortly.xyz — form-based"""
    return bypass_type1(url)

# ── redirect followers ───────────────────────────────────────────

def bypass_redirect(url):
    print(f"[*] redirect: {url}", file=sys.stderr)
    try:
        out, _ = curl([url, "-o", "/dev/null", "-w", "%{url_effective}", "-H", f"User-Agent: {UA}"])
        final = out.strip()
        if final and final != url:
            return final
    except: pass
    return None

def bypass_ouo(url):
    print(f"[*] ouo: {url}", file=sys.stderr)
    try:
        html, _ = curl([url, "-H", f"User-Agent: {UA}"])
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
    except: pass
    return bypass_redirect(url)

# ═══════════════════════════════════════════════════════════════════
# domain → handler registry
# ═══════════════════════════════════════════════════════════════════

DOMAIN_HANDLERS = {
    # Native token-based
    "aylink.co": bypass_aylink,
    "ay.live": bypass_aylink,
    "cpmlink.co": bypass_cpmlink,
    "cpmlink.pro": bypass_cpmlink,
    "linkvertise.com": bypass_linkvertise,
    "link-target.net": bypass_linkvertise,
    "link-center.net": bypass_linkvertise,
    "link-hub.net": bypass_linkvertise,
    "direct-link.net": bypass_linkvertise,
    # Specific handlers
    "try2link.com": bypass_try2link,
    "gplinks.co": bypass_gplinks,
    "gplinks.in": bypass_gplinks,
    "pkin.me": bypass_pkin,
    "shareus.in": bypass_shareus,
    "shortly.xyz": bypass_shortly,
    # Redirect followers
    "adf.ly": bypass_redirect,
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
    "tiny.cc": bypass_redirect,
    "youtu.be": bypass_redirect,
    "fb.me": bypass_redirect,
    "lnkd.in": bypass_redirect,
    "shorturl.ac": bypass_redirect,
    "shorte.st": bypass_redirect,
    "festyy.com": bypass_redirect,
    "gestyy.com": bypass_redirect,
    "ceesty.com": bypass_redirect,
    "corneey.com": bypass_redirect,
    "destyy.com": bypass_redirect,
}

# Type 1/2 services will be auto-detected at runtime
TYPE_SERVICE_DOMAINS = set()
for k in TYPE1_CONFIG: TYPE_SERVICE_DOMAINS.add(k.rstrip("/").split("/")[0] if "/" in k else k)
for k in TYPE2_CONFIG: TYPE_SERVICE_DOMAINS.add(k.rstrip("/").split("/")[0] if "/" in k else k)

# Fallback-only list
FALLBACK_ONLY = [
    "work.ink", "workink.click", "boost.ink", "mboost.me", "rekonise.com",
    "lootlabs.com", "lootlinks.com", "loot-link.com",
    "sub2unlock.com", "sub2unlock.net", "sub2unlock.io",
    "sub2get.com", "sub4unlock.com", "sub4unlock.pro", "subfinal.com",
    "social-unlock.com", "socialwolvez.com", "lockr.social",
    "just2earn.com",
]

def get_handler(url):
    domain = urllib.parse.urlparse(url).netloc.lower()
    for key, handler in DOMAIN_HANDLERS.items():
        if key in domain:
            return handler, "native"
    # Check type1/type2 services
    for svc in TYPE_SERVICE_DOMAINS:
        if svc in domain:
            return bypass_type1, "type1"
    for svc in FALLBACK_ONLY:
        if svc in domain:
            return None, "fallback_only"
    return bypass_redirect, "generic"

# ── main ─────────────────────────────────────────────────────────

LIST_SERVICES_FLAG = "--list-services"

def bypass(url):
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
        native = sorted(DOMAIN_HANDLERS.keys())
        type_svc = sorted(TYPE_SERVICE_DOMAINS)
        fallback = sorted(FALLBACK_ONLY)
        print("=== Native Handlers ===")
        for d in native: print(f"  {d}")
        print(f"\n=== Type-1/2 Form-based (auto-detected) ===")
        for d in type_svc: print(f"  {d}")
        print(f"\n=== Fallback Only (need native impl) ===")
        for d in fallback: print(f"  {d}")
        all_native = set(native) | set(type_svc)
        print(f"\nTotal: {len(all_native)} native + {len(fallback)} fallback = {len(all_native)+len(fallback)} services")
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
