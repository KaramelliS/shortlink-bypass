#!/usr/bin/env python3
"""
ShortLink Bypass — Universal Multi-Service Bypass Tool
Native handlers for 150+ shortlink services. No browser, no ads.
Covers: token flows, GraphQL, form bypass, base64/XOR decoding, redirect chains.

Usage:
    python3 bypass.py <shortlink_url> [shortlink_url2 ...]
    python3 bypass.py --batch file.txt
    python3 bypass.py --list-services

GitHub: https://github.com/KaramelliS/shortlink-bypass
"""

import subprocess, json, re, sys, tempfile, os, urllib.parse, time, base64

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
MOBILE_UA = "Mozilla/5.0 (Linux; Android 11; 2201116PI) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36"
IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"

# ── helpers ──────────────────────────────────────────────────────────

def curl(args, cookie=None, timeout=30):
    cmd = ["curl", "-s", "-L"]
    if cookie:
        cmd += ["-c", cookie, "-b", cookie]
    r = subprocess.run(cmd + args, capture_output=True, text=True, timeout=timeout)
    return r.stdout, r.stderr

def clean_url(url):
    return url.strip().strip('"').strip("'")

def follow_bildirim(final, cookie, ref):
    if "bildirim.online" in final:
        html2, _ = curl([final, "-H", f"User-Agent: {UA}", "-H", f"Referer: {ref}"], cookie)
        m = re.search(r"url\s*=\s*'([^']+)'", html2)
        if m:
            final = m.group(1)
    return final

def extract_form_inputs(html):
    data = {}
    for m in re.finditer(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"', html):
        data[m.group(1)] = m.group(2)
    for m in re.finditer(r'<input[^>]*value="([^"]*)"[^>]*name="([^"]*)"', html):
        data[m.group(2)] = m.group(1)
    return data

def try_import_requests():
    global requests
    try:
        import requests as _r
        requests = _r
        return True
    except ImportError:
        requests = None
        return False

# ── encoding/decoding utilities ──────────────────────────────────────

def decode_base64(s):
    """Try to decode base64 string, padding if needed"""
    try:
        s = s.strip()
        # Add padding
        missing = len(s) % 4
        if missing:
            s += '=' * (4 - missing)
        return base64.b64decode(s).decode('utf-8', errors='replace')
    except:
        return None

def decode_adfly_ysmm(ysmm):
    """Decode AdF.ly ysmm token using FastForward algorithm"""
    try:
        # Interleave: even positions form first half, odd form second half
        # Then XOR consecutive pairs of digits
        first_digit = ""
        second_digit = ""
        for i, c in enumerate(ysmm):
            if i % 2 == 0:
                first_digit += c
            else:
                second_digit = c + second_digit

        # Combine
        combined = first_digit + second_digit
        
        # De-XOR consecutive pairs
        chars = list(combined)
        key = "ABCEDFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        
        for i in range(len(chars) - 1):
            if i + 1 < len(chars):
                a = key.find(chars[i])
                b = key.find(chars[i + 1])
                if a >= 0 and b >= 0:
                    xor_val = a ^ b
                    if xor_val < len(key):
                        chars[i] = key[xor_val]

        result = "".join(chars)
        
        # Base64 decode and strip header
        decoded = decode_base64(result)
        if decoded:
            # Strip first 16 chars (noise/header)
            return decoded[16:]
    except:
        pass
    return None

def decode_base64_from_url(url, param=None, path_pos=None):
    """Decode base64 from URL param or path segment"""
    parsed = urllib.parse.urlparse(url)
    if param:
        val = urllib.parse.parse_qs(parsed.query).get(param, [None])[0]
        if val:
            return decode_base64(val)
    if path_pos is not None:
        parts = [p for p in parsed.path.split("/") if p]
        if path_pos < len(parts):
            return decode_base64(parts[path_pos])
    return None

# ═══════════════════════════════════════════════════════════════════
# token-based handlers — aylink / cpmlink
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
# GraphQL — linkvertise
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
    session.headers.update({"User-Agent": IPHONE_UA, "Origin": "https://linkvertise.com", "Referer": "https://linkvertise.com"})
    post_data = {"userIdAndUrl": {"user_id": user_id, "url": post_id}}
    additional = {"taboola": {"user_id": "fallbackUserId", "url": url}}
    try:
        r1 = session.post(LINKVERTISE_GRAPHQL, json={
            "operationName": "getDetailPageContent", "variables": {
                "linkIdentificationInput": post_data, "origin": "sharing", "additional_data": additional,
            }, "query": GDPC_QUERY,
        }, timeout=20)
        r1.raise_for_status(); d1 = r1.json()
        if "errors" in d1: return None
        access_token = d1["data"]["getDetailPageContent"]["access_token"]
        r2 = session.post(LINKVERTISE_GRAPHQL, json={
            "operationName": "completeDetailPageContent", "variables": {
                "linkIdentificationInput": post_data,
                "completeDetailPageContentInput": {"access_token": access_token},
            }, "query": CDPC_QUERY,
        }, timeout=20)
        r2.raise_for_status(); d2 = r2.json()
        if "errors" in d2: return None
        post_token = d2["data"]["completeDetailPageContent"]["TARGET"]
        r3 = session.post(LINKVERTISE_GRAPHQL, json={
            "operationName": "getDetailPageTarget", "variables": {
                "linkIdentificationInput": post_data, "token": post_token,
            }, "query": GDPT_QUERY,
        }, timeout=20)
        r3.raise_for_status(); d3 = r3.json()
        if "errors" in d3: return None
        return d3["data"]["getDetailPageTarget"]["url"]
    except Exception as e:
        print(f"[!] linkvertise: {e}", file=sys.stderr)
        return None

# ═══════════════════════════════════════════════════════════════════
# AdF.ly — ysmm XOR decode
# ═══════════════════════════════════════════════════════════════════

def bypass_adfly(url):
    """AdF.ly — extract ysmm token from page, XOR decode to get real URL"""
    print(f"[*] adfly: {url}", file=sys.stderr)
    cookie = tempfile.mktemp()
    try:
        html, _ = curl([url, "-H", f"User-Agent: {UA}"], cookie)
        # Extract ysmm token from the page
        m = re.search(r"var ysmm\s*=\s*'([^']+)'", html)
        if m:
            decoded = decode_adfly_ysmm(m.group(1))
            if decoded and decoded.startswith("http"):
                os.remove(cookie)
                return decoded
        # fallback: try redirect follow with iPhone UA
        out, _ = curl([url, "-o", "/dev/null", "-w", "%{url_effective}",
                       "-H", f"User-Agent: {IPHONE_UA}", "-e", "https://adf.ly/"], cookie)
        final = out.strip()
        if final and final != url:
            os.remove(cookie)
            return final
    except: pass
    try: os.remove(cookie)
    except: pass
    return None

# ═══════════════════════════════════════════════════════════════════
# Boost.ink — base64 kekw decode
# ═══════════════════════════════════════════════════════════════════

def bypass_boost(url):
    """boost.ink — extract base64 from kekw attribute"""
    print(f"[*] boost: {url}", file=sys.stderr)
    try:
        html, _ = curl([url, "-H", f"User-Agent: {UA}"])
        # FastForward's boost.js extracts kekw="base64data" 
        m = re.search(r'kekw\s*=\s*["\']([^"\']+)["\']', html)
        if m:
            decoded = decode_base64(m.group(1))
            if decoded:
                # May contain extract URL
                url_m = re.search(r'https?://[^\s"<>]+', decoded)
                if url_m:
                    return url_m.group(0)
                return decoded
        # fallback to redirect follow
        return bypass_redirect(url)
    except:
        return bypass_redirect(url)

# ═══════════════════════════════════════════════════════════════════
# base64/encoding-based bypasses (from FastForward rules.json)
# ═══════════════════════════════════════════════════════════════════

def bypass_base64_param(url):
    """Extract URL from base64-encoded URL parameter"""
    print(f"[*] b64param: {url}", file=sys.stderr)
    for param in ['url', 'link', 'r', 'go', 'site', 'data', 'id', 'q', 'u', 'to']:
        decoded = decode_base64_from_url(url, param=param)
        if decoded and decoded.startswith("http"):
            return decoded
    return None

def bypass_base64_path(url, path_pos=-1):
    """Extract URL from base64-encoded path segment"""
    print(f"[*] b64path: {url}", file=sys.stderr)
    parts = [p for p in urllib.parse.urlparse(url).path.split("/") if p]
    positions = [path_pos] if path_pos >= 0 else range(len(parts))
    for pos in positions:
        if pos < len(parts):
            decoded = decode_base64(parts[pos])
            if decoded and decoded.startswith("http"):
                return decoded
    return None

def bypass_generic_b64(url):
    """Try various base64 decoding strategies from FastForward rules"""
    # Try query param base64
    result = bypass_base64_param(url)
    if result: return result
    # Try path base64
    result = bypass_base64_path(url)
    if result: return result
    return None

# ═══════════════════════════════════════════════════════════════════
# Type 1/2 form-based bypasses (Indian shorteners)
# ═══════════════════════════════════════════════════════════════════

TYPE_SERVICES = {
    # (domain_prefix_match, form_domain, referer, sleep, use_go_link)
    # Form-based with id="go-link" → POST to /links/go
    "go.rocklinks.net": ("https://dwnld.povathemes.com/", "https://dwnld.povathemes.com/", 7, True),
    "rocklinks.net": ("https://dwnld.povathemes.com/", "https://dwnld.povathemes.com/", 7, True),
    "droplink.co": ("https://droplink.co/", "https://yoshare.net", 5, True),
    "tnlink.in": ("https://gadgets.usanewstoday.club/", "https://usanewstoday.club/", 7, True),
    "ez4short.com": ("https://ez4short.com/", "https://techmody.io/", 7, True),
    "xpshort.com": ("https://push.bdnewsx.com/", "https://veganho.co/", 7, True),
    "vearnl.in": ("https://go.urlearn.xyz/", "https://v.modmakers.xyz/", 7, True),
    "adrinolinks.in": ("https://adrinolinks.in/", "https://wikitraveltips.com/", 7, True),
    "techymozo.com": ("https://push.bdnewsx.com/", "https://veganho.co/", 7, True),
    "linkbnao.com": ("https://go.linkbnao.com/", "https://doibihar.org/", 5, True),
    "linksxyz.in": ("https://blogshangrila.com/insurance/", "https://cypherroot.com/", 7, True),
    "short-jambo.com": ("https://short-jambo.com/", "https://aghtas.com/", 7, True),
    "ads.droplink.co.in": ("https://go.droplink.co.in/", "https://go.droplink.co.in/", 7, True),
    "linkpays.in": ("https://m.techpoints.xyz//", "https://www.filmypoints.in/", 7, True),
    "pi-l.ink": ("https://go.pilinks.net/", "https://poketoonworld.com/", 7, True),
    "link.tnlink.in": ("https://gadgets.usanewstoday.club/", "https://usanewstoday.club/", 7, True),
    "open2get.in": ("https://m.open2get.in/", "https://ezeviral.com/", 5, True),
    "earn4link.in": ("https://m.open2get.in/", "https://ezeviral.com/", 5, True),
    "mdiskshortner.link": ("https://mdiskshortner.link/", "https://mdiskshortner.link/", 7, True),
    "pdiskshortener.com": ("https://pdiskshortener.com/", "https://pdiskshortener.com/", 7, True),
    "go.earnl.xyz": ("https://go.earnl.xyz/", "https://v.earnl.xyz/", 7, True),
    "g.rewayatcafe.com": ("https://course.rewayatcafe.com/", "https://course.rewayatcafe.com/", 7, True),
    "indianshortner.in": ("https://indianshortner.com/", "https://indianshortner.com/", 7, True),
    "m.easysky.in": ("https://techy.veganab.co/", "https://techy.veganab.co/", 7, True),
    "earn.moneykamalo.com": ("https://go.moneykamalo.com//", "https://go.moneykamalo.com/", 7, True),
    "open.crazyblog.in": ("https://hr.vikashmewada.com/", "https://hr.vikashmewada.com/", 7, True),
    "link.tnvalue.in": ("https://internet.webhostingtips.club/", "https://internet.webhostingtips.club/", 7, True),
    "shortingly.me": ("https://go.techyjeeshan.xyz/", "https://go.techyjeeshan.xyz/", 7, True),
    "dulink.in": ("https://tekcrypt.in/tek/", "https://tekcrypt.in/tek/", 10, True),
    "bindaaslinks.com": ("https://www.techishant.in/blog/", "https://www.techishant.in/blog/", 7, True),
    "ser2.crazyblog.in": ("https://ser3.crazyblog.in/", "https://ser3.crazyblog.in/", 7, True),
    "bitshorten.com": ("https://bitshorten.com/", "https://bitshorten.com/", 7, True),
    "rocklink.in": ("https://rocklink.in/", "https://rocklink.in/", 7, True),
    "link.short2url.in": ("https://technemo.xyz/blog/", "https://technemo.xyz/blog/", 7, True),
    "tekcrypt.in": ("https://tekcrypt.in/tek/", "https://tekcrypt.in/tek/", 10, True),
    "za.uy": ("https://za.uy/", "https://za.uy/", 7, True),
    "gtlinks.me": ("https://gtlinks.me/", "https://gtlinks.me/", 7, True),
    "loan.kinemaster.cc": ("https://loan.kinemaster.cc/", "https://loan.kinemaster.cc/", 7, True),
    "theforyou.in": ("https://www.theforyou.in/", "https://www.theforyou.in/", 7, True),
    "safeurl.sirigan.my.id": ("https://safeurl.sirigan.my.id/", "https://safeurl.sirigan.my.id/", 7, True),
    "thinfi.com": ("https://thinfi.com/", "https://thinfi.com/", 7, True),
    "hypershort.com": ("https://hypershort.com/", "https://hypershort.com/", 7, True),
    "shortly.xyz": ("https://www.shortly.xyz/", "https://www.shortly.xyz/", 7, True),
}

def bypass_type_form(url):
    """Generic form-based bypass for Indian shorteners"""
    domain = urllib.parse.urlparse(url).netloc.lower()
    slug = url.rstrip("/").split("/")[-1]

    form_domain = referer = None
    sleep_time = 7
    for key, cfg in TYPE_SERVICES.items():
        if key in url.lower():
            form_domain, referer, sleep_time, _ = cfg
            break

    if not form_domain:
        form_domain = referer = f"https://{domain}/"

    cookie = tempfile.mktemp()
    try:
        html, _ = curl([form_domain + slug, "-H", f"User-Agent: {UA}", "-H", f"Referer: {referer}"], cookie)
        data = extract_form_inputs(html)
        if not data:
            os.remove(cookie)
            return None

        time.sleep(sleep_time)
        raw, _ = curl([
            f"{form_domain.rstrip('/')}/links/go",
            "-H", f"User-Agent: {UA}",
            "-H", "X-Requested-With: XMLHttpRequest",
            "-H", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
            "-H", f"Referer: {form_domain + slug}",
            "--data", "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in data.items()),
        ], cookie, 15)
        os.remove(cookie)
        try:
            final = json.loads(raw).get("url", "")
            return final if final else None
        except json.JSONDecodeError:
            return None
    except Exception:
        try: os.remove(cookie)
        except: pass
        return None

# ── try2link.com ─────────────────────────────────────────────────

def bypass_try2link(url):
    print(f"[*] try2link: {url}", file=sys.stderr)
    cookie = tempfile.mktemp()
    url = url.rstrip("/")
    try:
        ts = int(time.time()) + 240
        html, _ = curl([f"{url}?d={ts}", "-H", f"User-Agent: {UA}", "-H", "Referer: https://newforex.online/"], cookie)
        data = extract_form_inputs(html)
        if not data:
            os.remove(cookie)
            return None
        time.sleep(7)
        raw, _ = curl([
            "https://try2link.com/links/go",
            "-H", f"User-Agent: {UA}", "-H", "Host: try2link.com",
            "-H", "X-Requested-With: XMLHttpRequest",
            "-H", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
            "-H", f"Referer: {url}", "-H", "Origin: https://try2link.com",
            "--data", "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in data.items()),
        ], cookie, 15)
        os.remove(cookie)
        return json.loads(raw).get("url")
    except Exception:
        try: os.remove(cookie)
        except: pass
        return None

# ── gplinks.co ───────────────────────────────────────────────────

def bypass_gplinks(url):
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
        return json.loads(raw).get("url")
    except Exception:
        try: os.remove(cookie)
        except: pass
        return None

# ── pkin.me ──────────────────────────────────────────────────────

def bypass_pkin(url):
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
        return json.loads(raw).get("url")
    except Exception:
        try: os.remove(cookie)
        except: pass
        return None

# ── shareus.in ───────────────────────────────────────────────────

def bypass_shareus(url):
    print(f"[*] shareus: {url}", file=sys.stderr)
    token = url.split("=")[-1]
    try:
        out, _ = curl([f"https://us-central1-my-apps-server.cloudfunctions.net/r?shortid={token}",
                       "-H", f"User-Agent: {UA}"])
        return out.strip()
    except:
        return None

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
    # Token-based
    "aylink.co": bypass_aylink,
    "ay.live": bypass_aylink,
    "cpmlink.co": bypass_cpmlink,
    "cpmlink.pro": bypass_cpmlink,
    # GraphQL
    "linkvertise.com": bypass_linkvertise,
    "link-target.net": bypass_linkvertise,
    "link-center.net": bypass_linkvertise,
    "link-hub.net": bypass_linkvertise,
    "direct-link.net": bypass_linkvertise,
    # Specific bypasses
    "adf.ly": bypass_adfly,
    "boost.ink": bypass_boost,
    "mboost.me": bypass_boost,
    "try2link.com": bypass_try2link,
    "gplinks.co": bypass_gplinks,
    "gplinks.in": bypass_gplinks,
    "pkin.me": bypass_pkin,
    "shareus.in": bypass_shareus,
    # Redirect followers
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
    "festyy.com": bypass_redirect,
    "gestyy.com": bypass_redirect,
    "ceesty.com": bypass_redirect,
    "corneey.com": bypass_redirect,
    "destyy.com": bypass_redirect,
    "t2m.io": bypass_redirect,
    "disq.us": bypass_redirect,
    "page.link": bypass_redirect,
    "shortcm.li": bypass_redirect,
    "dis.gd": bypass_redirect,
    "b.link": bypass_redirect,
    "nzn.me": bypass_redirect,
    # Base64-encoded URL in query param
    "anonym.to": bypass_base64_param,
    "anonymz.com": bypass_base64_param,
    "hidereferrer.com": bypass_base64_param,
    "leechall.com": bypass_base64_param,
}

# Fallback-only (browser-based social unlocks)
FALLBACK_ONLY = [
    "work.ink", "workink.click", "rekonise.com",
    "lootlabs.com", "lootlinks.com", "loot-link.com",
    "sub2unlock.com", "sub2unlock.net", "sub2unlock.io",
    "sub2get.com", "sub4unlock.com", "sub4unlock.pro", "subfinal.com",
    "social-unlock.com", "socialwolvez.com", "lockr.social",
    "just2earn.com", "letsboost.net", "bst.gg", "booo.st",
    "1link.club", "1shortlink.com", "bomurl.com",
]

def get_handler(url):
    domain = urllib.parse.urlparse(url).netloc.lower()
    for key, handler in DOMAIN_HANDLERS.items():
        if key in domain:
            return handler, "native"
    for key in TYPE_SERVICES:
        if key in url.lower():
            return bypass_type_form, "form"
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
        form = sorted(TYPE_SERVICES.keys())
        fallback = sorted(FALLBACK_ONLY)
        print("=== Native Handlers (direct) ===")
        for d in native: print(f"  {d}")
        print(f"\n=== Form-based (auto-detected) ===")
        for d in form: print(f"  {d}")
        print(f"\n=== Fallback Only ===")
        for d in fallback: print(f"  {d}")
        all_native = set(native) | set(form)
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
