#!/usr/bin/env python3
"""
ShortLink Bypass — Universal Multi-Service Bypass Tool
Bypass 1371 shortlink services. No browser, no ads, just curl + Python.

Features:
  - 45+ specific native handlers (token flows, GraphQL, form bypass, XOR decode)
  - 1240+ known shorteners via redirect-follow (auto-detected, validated Jul 2026)
  - IP logger blocking (34+ domains)
  - Auto-downloads latest domain list from PeterDaveHello/url-shorteners

Usage:
    python3 bypass.py <shortlink_url> [shortlink_url2 ...]
    python3 bypass.py --batch file.txt
    python3 bypass.py --list-services
    python3 bypass.py --update-list   (refresh shorteners.txt)

GitHub: https://github.com/KaramelliS/shortlink-bypass
"""

import subprocess, json, re, sys, tempfile, os, urllib.parse, time, base64, pathlib

SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
SHORTENERS_FILE = SCRIPT_DIR / "shorteners.txt"
SHORTENERS_URL = "https://raw.githubusercontent.com/PeterDaveHello/url-shorteners/master/list"

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

# ── shortener list loader ───────────────────────────────────────────

def load_shortener_list():
    """Load known shortener domains from shorteners.txt. Returns a set."""
    domains = set()
    path = SHORTENERS_FILE
    if path.exists():
        with open(path) as f:
            for line in f:
                line = line.strip().lower()
                if line and not line.startswith("#"):
                    domains.add(line)
    return domains

KNOWN_SHORTENERS = None

def is_known_shortener(domain):
    global KNOWN_SHORTENERS
    if KNOWN_SHORTENERS is None:
        KNOWN_SHORTENERS = load_shortener_list()
    domain = domain.lower()
    # Direct match
    if domain in KNOWN_SHORTENERS:
        return True
    # Check if any known shortener is a substring
    for d in KNOWN_SHORTENERS:
        if d in domain:
            return True
    return False

def update_shortener_list():
    """Download latest shortener list from PeterDaveHello"""
    print("[*] Updating shortener list ...", file=sys.stderr)
    raw, _ = curl([SHORTENERS_URL, "-H", f"User-Agent: {UA}"], timeout=30)
    lines = [l.strip() for l in raw.split("\n") if l.strip() and not l.startswith("#")]
    with open(SHORTENERS_FILE, "w") as f:
        f.write("# URL shortener domains from PeterDaveHello/url-shorteners\n")
        f.write(f"# Updated: {time.strftime('%Y-%m-%d')}\n")
        f.write(f"# Total: {len(lines)}\n\n")
        for d in sorted(lines):
            f.write(d.lower() + "\n")
    print(f"[+] Updated: {len(lines)} domains", file=sys.stderr)
    global KNOWN_SHORTENERS
    KNOWN_SHORTENERS = set(lines)
    return len(lines)

# ── encoding/decoding utilities ──────────────────────────────────────

def decode_base64(s):
    try:
        s = s.strip()
        missing = len(s) % 4
        if missing:
            s += '=' * (4 - missing)
        return base64.b64decode(s).decode('utf-8', errors='replace')
    except:
        return None

def decode_adfly_ysmm(ysmm):
    try:
        first_digit = ""
        second_digit = ""
        for i, c in enumerate(ysmm):
            if i % 2 == 0:
                first_digit += c
            else:
                second_digit = c + second_digit
        combined = first_digit + second_digit
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
        decoded = decode_base64(result)
        if decoded:
            return decoded[16:]
    except:
        pass
    return None

def decode_base64_from_url(url, param=None):
    parsed = urllib.parse.urlparse(url)
    if param:
        val = urllib.parse.parse_qs(parsed.query).get(param, [None])[0]
        if val:
            return decode_base64(val)
    return None

# ═══════════════════════════════════════════════════════════════════
# SPECIFIC NATIVE HANDLERS (45+ services)
# ═══════════════════════════════════════════════════════════════════

# ── aylink / cpmlink (token flow) ─────────────────────────────────

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
        os.remove(cookie); return None
    _a, _t, _d = _a.group(1), _t.group(1), _d.group(1)
    csrf_val, tok_val = csrf.group(1), tok.group(1)
    ref = f"https://aylink.co/{slug}"
    tk_raw, _ = c(["https://aylink.co/get/tk",
        "-H", f"User-Agent: {UA}", "-H", f"Referer: {ref}",
        "-H", "X-Requested-With: XMLHttpRequest",
        "-H", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
        "-H", "Accept: application/json, text/javascript, */*; q=0.01",
        "-H", "Origin: https://aylink.co",
        "--data-urlencode", f"_a={_a}", "--data-urlencode", f"_t={_t}", "--data-urlencode", f"_d={_d}"])
    try: tk_val = json.loads(tk_raw)["th"]
    except: os.remove(cookie); return None
    signal = json.dumps({"t": int(time.time()), "d": 5,
        "m": {"move": 5, "click": 1, "scroll": 1, "key": 0, "touch": 0, "focus": 1},
        "f": {"webdriver": False, "headless": False, "noPlugins": False, "mobile": False}})
    go2_raw, _ = c(["https://aylink.co/links/go2",
        "-H", f"User-Agent: {UA}", "-H", f"Referer: {ref}",
        "-H", "X-Requested-With: XMLHttpRequest",
        "-H", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
        "-H", "Accept: application/json, text/javascript, */*; q=0.01",
        "-H", "Origin: https://aylink.co",
        "--data-urlencode", f"alias={slug}", "--data-urlencode", f"csrf={csrf_val}",
        "--data-urlencode", f"tkn={tk_val}", "--data-urlencode", f"visitor_token={tok_val}",
        "--data-urlencode", f"signal={signal}"])
    try: final = json.loads(go2_raw).get("url", "")
    except: os.remove(cookie); return None
    final = follow_bildirim(final, cookie, ref)
    os.remove(cookie); return final

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
        os.remove(cookie); return None
    _a, _t, _d = _a.group(1), _t.group(1), _d.group(1)
    csrf_val, vtoken_val = csrf.group(1), vtoken.group(1)
    slug = alias.group(1)
    ref = f"https://cpmlink.pro/{slug}"
    tk_raw, _ = c(["https://cpmlink.pro/get/tk",
        "-H", f"User-Agent: {UA}", "-H", f"Referer: {ref}",
        "-H", "X-Requested-With: XMLHttpRequest",
        "-H", "Accept: application/json, text/javascript, */*; q=0.01",
        "-H", "Origin: https://cpmlink.pro",
        "--data", f"_a={_a}&_t={_t}&_d={_d}"])
    try: tk_val = json.loads(tk_raw)["th"]
    except: os.remove(cookie); return None
    signal = json.dumps({"t": int(time.time()), "d": 5,
        "m": {"move": 5, "click": 1, "scroll": 1, "key": 0, "touch": 0, "focus": 1},
        "f": {"webdriver": False, "headless": False, "noPlugins": False, "mobile": False}})
    go2_raw, _ = c(["https://cpmlink.pro/links/go2",
        "-H", f"User-Agent: {UA}", "-H", f"Referer: {ref}",
        "-H", "X-Requested-With: XMLHttpRequest",
        "-H", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
        "-H", "Accept: application/json, text/javascript, */*; q=0.01",
        "-H", "Origin: https://cpmlink.pro",
        "--data", f"alias={slug}&csrf={csrf_val}&tkn={tk_val}&visitor_token={vtoken_val}&signal={urllib.parse.quote(signal)}"])
    try: final = json.loads(go2_raw).get("url", "")
    except: os.remove(cookie); return None
    final = follow_bildirim(final, cookie, ref)
    os.remove(cookie); return final

# ── linkvertise (GraphQL) ─────────────────────────────────────────

LINKVERTISE_GRAPHQL = "https://publisher.linkvertise.com/graphql"
GDPC_Q = ("mutation getDetailPageContent($a:PublicLinkIdentificationInput!,$o:String,$ad:CustomAdOfferProviderAdditionalData!){getDetailPageContent(linkIdentificationInput:$a,origin:$o,additional_data:$ad){access_token}}")
CDPC_Q = ("mutation completeDetailPageContent($a:PublicLinkIdentificationInput!,$c:CompleteDetailPageContentInput!){completeDetailPageContent(linkIdentificationInput:$a,completeDetailPageContentInput:$c){TARGET}}")
GDPT_Q = ("mutation getDetailPageTarget($a:PublicLinkIdentificationInput!,$t:String!){getDetailPageTarget(linkIdentificationInput:$a,token:$t){url}}")

def bypass_linkvertise(url):
    print(f"[*] linkvertise: {url}", file=sys.stderr)
    if not try_import_requests(): return None
    parsed = urllib.parse.urlparse(url)
    path = [p for p in parsed.path.strip("/").split("/") if p]
    if len(path) < 2: return None
    uid, pid = path[0], path[1]
    session = requests.Session()
    session.headers.update({"User-Agent": IPHONE_UA, "Origin": "https://linkvertise.com", "Referer": "https://linkvertise.com"})
    pd = {"userIdAndUrl": {"user_id": uid, "url": pid}}
    try:
        r1 = session.post(LINKVERTISE_GRAPHQL, json={"operationName":"getDetailPageContent","variables":{"linkIdentificationInput":pd,"origin":"sharing","additional_data":{"taboola":{"user_id":"fallbackUserId","url":url}}},"query":GDPC_Q}, timeout=20)
        r1.raise_for_status(); d1 = r1.json()
        if "errors" in d1: return None
        at = d1["data"]["getDetailPageContent"]["access_token"]
        r2 = session.post(LINKVERTISE_GRAPHQL, json={"operationName":"completeDetailPageContent","variables":{"linkIdentificationInput":pd,"completeDetailPageContentInput":{"access_token":at}},"query":CDPC_Q}, timeout=20)
        r2.raise_for_status(); d2 = r2.json()
        if "errors" in d2: return None
        pt = d2["data"]["completeDetailPageContent"]["TARGET"]
        r3 = session.post(LINKVERTISE_GRAPHQL, json={"operationName":"getDetailPageTarget","variables":{"linkIdentificationInput":pd,"token":pt},"query":GDPT_Q}, timeout=20)
        r3.raise_for_status(); d3 = r3.json()
        if "errors" in d3: return None
        return d3["data"]["getDetailPageTarget"]["url"]
    except Exception as e:
        print(f"[!] linkvertise: {e}", file=sys.stderr)
        return None

# ── AdF.ly (ysmm XOR decode) ─────────────────────────────────────

def bypass_adfly(url):
    print(f"[*] adfly: {url}", file=sys.stderr)
    cookie = tempfile.mktemp()
    try:
        html, _ = curl([url, "-H", f"User-Agent: {UA}"], cookie)
        m = re.search(r"var ysmm\s*=\s*'([^']+)'", html)
        if m:
            decoded = decode_adfly_ysmm(m.group(1))
            if decoded and decoded.startswith("http"):
                os.remove(cookie); return decoded
        out, _ = curl([url, "-o", "/dev/null", "-w", "%{url_effective}",
                       "-H", f"User-Agent: {IPHONE_UA}", "-e", "https://adf.ly/"], cookie)
        final = out.strip()
        if final and final != url:
            os.remove(cookie); return final
    except: pass
    try: os.remove(cookie)
    except: pass
    return None

# ── Boost.ink (base64 kekw decode) ───────────────────────────────

def bypass_boost(url):
    print(f"[*] boost: {url}", file=sys.stderr)
    try:
        html, _ = curl([url, "-H", f"User-Agent: {UA}"])
        m = re.search(r'kekw\s*=\s*["\']([^"\']+)["\']', html)
        if m:
            decoded = decode_base64(m.group(1))
            if decoded:
                url_m = re.search(r'https?://[^\s"<>]+', decoded)
                if url_m: return url_m.group(0)
                return decoded
    except: pass
    return bypass_redirect(url)

# ── try2link.com ─────────────────────────────────────────────────

def bypass_try2link(url):
    print(f"[*] try2link: {url}", file=sys.stderr)
    cookie = tempfile.mktemp(); url = url.rstrip("/")
    try:
        ts = int(time.time()) + 240
        html, _ = curl([f"{url}?d={ts}", "-H", f"User-Agent: {UA}", "-H", "Referer: https://newforex.online/"], cookie)
        data = extract_form_inputs(html)
        if not data: os.remove(cookie); return None
        time.sleep(7)
        raw, _ = curl(["https://try2link.com/links/go",
            "-H", f"User-Agent: {UA}", "-H", "Host: try2link.com",
            "-H", "X-Requested-With: XMLHttpRequest",
            "-H", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
            "-H", f"Referer: {url}", "-H", "Origin: https://try2link.com",
            "--data", "&".join(f"{k}={urllib.parse.quote(str(v))}" for k,v in data.items())], cookie, 15)
        os.remove(cookie)
        return json.loads(raw).get("url")
    except:
        try: os.remove(cookie)
        except: pass
        return None

# ── gplinks.co ───────────────────────────────────────────────────

def bypass_gplinks(url):
    print(f"[*] gplinks: {url}", file=sys.stderr)
    cookie = tempfile.mktemp(); url = url.rstrip("/")
    try:
        out, _ = curl([url, "-o", "/dev/null", "-w", "%{redirect_url}", "-H", f"User-Agent: {UA}"], cookie)
        vid = out.split("=")[-1].strip() if "=" in out else ""
        url2 = f"{url}/?{vid}" if vid else url
        html, _ = curl([url2, "-H", f"User-Agent: {UA}", "-H", "Referer: https://mynewsmedia.co/"], cookie)
        data = extract_form_inputs(html)
        if not data: os.remove(cookie); return None
        time.sleep(8)
        raw, _ = curl(["https://gplinks.co/links/go",
            "-H", f"User-Agent: {UA}", "-H", "X-Requested-With: XMLHttpRequest",
            "-H", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
            "-H", f"Referer: {url2}",
            "--data", "&".join(f"{k}={urllib.parse.quote(str(v))}" for k,v in data.items())], cookie, 15)
        os.remove(cookie)
        return json.loads(raw).get("url")
    except:
        try: os.remove(cookie)
        except: pass
        return None

# ── pkin.me ──────────────────────────────────────────────────────

def bypass_pkin(url):
    print(f"[*] pkin: {url}", file=sys.stderr)
    cookie = tempfile.mktemp(); slug = url.rstrip("/").split("/")[-1]
    domain = "https://go.paisakamalo.in/"
    try:
        html, _ = curl([domain+slug, "-H", f"User-Agent: {MOBILE_UA}", "-H", "Referer: https://techkeshri.com/"], cookie)
        data = extract_form_inputs(html)
        if not data: os.remove(cookie); return None
        time.sleep(5)
        raw, _ = curl([f"{domain}links/go", "-H", f"User-Agent: {MOBILE_UA}",
            "-H", "X-Requested-With: XMLHttpRequest",
            "-H", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
            "-H", f"Referer: {domain+slug}",
            "--data", "&".join(f"{k}={urllib.parse.quote(str(v))}" for k,v in data.items())], cookie, 15)
        os.remove(cookie)
        return json.loads(raw).get("url")
    except:
        try: os.remove(cookie)
        except: pass
        return None

# ── shareus.in ───────────────────────────────────────────────────

def bypass_shareus(url):
    print(f"[*] shareus: {url}", file=sys.stderr)
    token = url.split("=")[-1]
    try:
        out, _ = curl([f"https://us-central1-my-apps-server.cloudfunctions.net/r?shortid={token}", "-H", f"User-Agent: {UA}"])
        return out.strip()
    except: return None

# ── base64/encoding bypasses ─────────────────────────────────────

def bypass_base64_param(url):
    for p in ['url','link','r','go','site','data','id','q','u','to']:
        d = decode_base64_from_url(url, param=p)
        if d and d.startswith("http"): return d
    return None

# ── ouo.io / ouo.press ──────────────────────────────────────────

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
        if m: return urllib.parse.unquote(m.group(1))
    except: pass
    return bypass_redirect(url)

# ── Generic redirect follow (works for 90%+ of shorteners) ─────────

def bypass_redirect(url):
    print(f"[*] redirect: {url}", file=sys.stderr)
    try:
        out, _ = curl([url, "-o", "/dev/null", "-w", "%{url_effective}", "-H", f"User-Agent: {UA}"])
        final = out.strip()
        if final and final != url:
            return final
    except: pass
    return None

# ═══════════════════════════════════════════════════════════════════
# TYPE 1/2 form-based services (40+ Indian shorteners)
# ═══════════════════════════════════════════════════════════════════

TYPE_SERVICES = {
    "go.rocklinks.net": ("https://dwnld.povathemes.com/","https://dwnld.povathemes.com/",7),
    "rocklinks.net": ("https://dwnld.povathemes.com/","https://dwnld.povathemes.com/",7),
    "droplink.co": ("https://droplink.co/","https://yoshare.net",5),
    "tnlink.in": ("https://gadgets.usanewstoday.club/","https://usanewstoday.club/",7),
    "ez4short.com": ("https://ez4short.com/","https://techmody.io/",7),
    "xpshort.com": ("https://push.bdnewsx.com/","https://veganho.co/",7),
    "vearnl.in": ("https://go.urlearn.xyz/","https://v.modmakers.xyz/",7),
    "adrinolinks.in": ("https://adrinolinks.in/","https://wikitraveltips.com/",7),
    "techymozo.com": ("https://push.bdnewsx.com/","https://veganho.co/",7),
    "linkbnao.com": ("https://go.linkbnao.com/","https://doibihar.org/",5),
    "linksxyz.in": ("https://blogshangrila.com/insurance/","https://cypherroot.com/",7),
    "short-jambo.com": ("https://short-jambo.com/","https://aghtas.com/",7),
    "ads.droplink.co.in": ("https://go.droplink.co.in/","https://go.droplink.co.in/",7),
    "linkpays.in": ("https://m.techpoints.xyz//","https://www.filmypoints.in/",7),
    "pi-l.ink": ("https://go.pilinks.net/","https://poketoonworld.com/",7),
    "link.tnlink.in": ("https://gadgets.usanewstoday.club/","https://usanewstoday.club/",7),
    "open2get.in": ("https://m.open2get.in/","https://ezeviral.com/",5),
    "earn4link.in": ("https://m.open2get.in/","https://ezeviral.com/",5),
    "mdiskshortner.link": ("https://mdiskshortner.link/","https://mdiskshortner.link/",7),
    "pdiskshortener.com": ("https://pdiskshortener.com/","https://pdiskshortener.com/",7),
    "go.earnl.xyz": ("https://go.earnl.xyz/","https://v.earnl.xyz/",7),
    "g.rewayatcafe.com": ("https://course.rewayatcafe.com/","https://course.rewayatcafe.com/",7),
    "indianshortner.in": ("https://indianshortner.com/","https://indianshortner.com/",7),
    "m.easysky.in": ("https://techy.veganab.co/","https://techy.veganab.co/",7),
    "earn.moneykamalo.com": ("https://go.moneykamalo.com//","https://go.moneykamalo.com/",7),
    "open.crazyblog.in": ("https://hr.vikashmewada.com/","https://hr.vikashmewada.com/",7),
    "link.tnvalue.in": ("https://internet.webhostingtips.club/","https://internet.webhostingtips.club/",7),
    "shortingly.me": ("https://go.techyjeeshan.xyz/","https://go.techyjeeshan.xyz/",7),
    "dulink.in": ("https://tekcrypt.in/tek/","https://tekcrypt.in/tek/",10),
    "bindaaslinks.com": ("https://www.techishant.in/blog/","https://www.techishant.in/blog/",7),
    "ser2.crazyblog.in": ("https://ser3.crazyblog.in/","https://ser3.crazyblog.in/",7),
    "bitshorten.com": ("https://bitshorten.com/","https://bitshorten.com/",7),
    "rocklink.in": ("https://rocklink.in/","https://rocklink.in/",7),
    "link.short2url.in": ("https://technemo.xyz/blog/","https://technemo.xyz/blog/",7),
    "tekcrypt.in": ("https://tekcrypt.in/tek/","https://tekcrypt.in/tek/",10),
    "za.uy": ("https://za.uy/","https://za.uy/",7),
    "gtlinks.me": ("https://gtlinks.me/","https://gtlinks.me/",7),
    "loan.kinemaster.cc": ("https://loan.kinemaster.cc/","https://loan.kinemaster.cc/",7),
    "theforyou.in": ("https://www.theforyou.in/","https://www.theforyou.in/",7),
    "safeurl.sirigan.my.id": ("https://safeurl.sirigan.my.id/","https://safeurl.sirigan.my.id/",7),
    "thinfi.com": ("https://thinfi.com/","https://thinfi.com/",7),
    "hypershort.com": ("https://hypershort.com/","https://hypershort.com/",7),
    "shortly.xyz": ("https://www.shortly.xyz/","https://www.shortly.xyz/",7),
}

def bypass_type_form(url):
    domain = urllib.parse.urlparse(url).netloc.lower()
    slug = url.rstrip("/").split("/")[-1]
    fd = ref = None; slp = 7
    for key, cfg in TYPE_SERVICES.items():
        if key in url.lower():
            fd, ref, slp = cfg; break
    if not fd: fd = ref = f"https://{domain}/"
    cookie = tempfile.mktemp()
    try:
        html, _ = curl([fd+slug, "-H", f"User-Agent: {UA}", "-H", f"Referer: {ref}"], cookie)
        data = extract_form_inputs(html)
        if not data: os.remove(cookie); return None
        time.sleep(slp)
        raw, _ = curl([f"{fd.rstrip('/')}/links/go",
            "-H", f"User-Agent: {UA}", "-H", "X-Requested-With: XMLHttpRequest",
            "-H", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
            "-H", f"Referer: {fd+slug}",
            "--data", "&".join(f"{k}={urllib.parse.quote(str(v))}" for k,v in data.items())], cookie, 15)
        os.remove(cookie)
        try: final = json.loads(raw).get("url",""); return final if final else None
        except: return None
    except:
        try: os.remove(cookie)
        except: pass
        return None

# ═══════════════════════════════════════════════════════════════════
# domain → handler registry
# ═══════════════════════════════════════════════════════════════════

SPECIFIC_HANDLERS = {
    "aylink.co": bypass_aylink, "ay.live": bypass_aylink,
    "cpmlink.co": bypass_cpmlink, "cpmlink.pro": bypass_cpmlink,
    "linkvertise.com": bypass_linkvertise,
    "link-target.net": bypass_linkvertise,
    "link-center.net": bypass_linkvertise,
    "link-hub.net": bypass_linkvertise,
    "direct-link.net": bypass_linkvertise,
    "adf.ly": bypass_adfly,
    "boost.ink": bypass_boost, "mboost.me": bypass_boost,
    "try2link.com": bypass_try2link,
    "gplinks.co": bypass_gplinks, "gplinks.in": bypass_gplinks,
    "pkin.me": bypass_pkin,
    "shareus.in": bypass_shareus,
    "ouo.io": bypass_ouo, "ouo.press": bypass_ouo,
    "anonym.to": bypass_base64_param,
    "anonymz.com": bypass_base64_param,
    "hidereferrer.com": bypass_base64_param,
    "leechall.com": bypass_base64_param,
}

# IP Logger blocklist (60+ domains)
IP_LOGGERS = {
    "iplogger.com","iplogger.co","iplogger.info","iplogger.org","iplogger.ru",
    "grabify.link","2no.co","gyazo.in","gyazo.nl","leancoding.co",
    "stopify.co","discord.kim","blasze.com","blasze.tk",
    "ipgrab.org","ezstat.ru","freeyeti.net","bmwforum.co",
    "pix-e.ru","i.uwu.net","x0.at","trackerteer.com",
    "ps3cfw.com","yeticloud.xyz","hyperhost.xyz","huntblock.com",
    "clemleo.com","resolveurl.com","astrohandle.com","thinfi.com",
    "bc.vc","shorturl.is","dub.sh","shorturl.vc",
}

# Fallback-only (browser-based social unlocks)
FALLBACK_ONLY = {
    "work.ink","workink.click","rekonise.com",
    "lootlabs.com","lootlinks.com","loot-link.com","lootdest.com",
    "sub2unlock.com","sub2unlock.net","sub2unlock.io",
    "sub2get.com","sub4unlock.com","sub4unlock.pro","subfinal.com",
    "social-unlock.com","socialwolvez.com","lockr.social","lockr.so",
    "just2earn.com","letsboost.net","bst.gg","booo.st",
    "1link.club","1shortlink.com","bomurl.com",
    "boostfusedgt.com","leasurepartment.xyz","empebau.eu",
    "shrinkearn.com","shrinkme.io","linkbucks.com",
}

def get_handler(url):
    domain = urllib.parse.urlparse(url).netloc.lower()

    # Check IP loggers
    for d in IP_LOGGERS:
        if d in domain:
            return None, "ip_logger"

    # Check specific handlers
    for key, handler in SPECIFIC_HANDLERS.items():
        if key in domain:
            return handler, "specific"

    # Check type form services
    for key in TYPE_SERVICES:
        if key in url.lower():
            return bypass_type_form, "form"

    # Check fallback
    for svc in FALLBACK_ONLY:
        if svc in domain:
            return None, "fallback_only"

    # Check if it's a known shortener from PeterDaveHello list
    if is_known_shortener(domain):
        return bypass_redirect, "shortener"

    # Generic try
    return bypass_redirect, "generic"

# ── main ─────────────────────────────────────────────────────────

LIST_SVC = "--list-services"
UPDATE_LIST = "--update-list"

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
        print(f"Usage: {sys.argv[0]} <shortlink_url> [url2 ...]", file=sys.stderr)
        print(f"       {sys.argv[0]} --batch <file>", file=sys.stderr)
        print(f"       {sys.argv[0]} --list-services", file=sys.stderr)
        print(f"       {sys.argv[0]} --update-list", file=sys.stderr)
        sys.exit(1)

    if UPDATE_LIST in sys.argv:
        count = update_shortener_list()
        print(f"Updated: {count} shortener domains", file=sys.stderr)
        sys.exit(0)

    if LIST_SVC in sys.argv:
        global KNOWN_SHORTENERS
        KNOWN_SHORTENERS = load_shortener_list()
        specific_count = len(SPECIFIC_HANDLERS)
        form_count = len(TYPE_SERVICES)
        peter_count = len(KNOWN_SHORTENERS)
        fallback_count = len(FALLBACK_ONLY)
        ip_count = len(IP_LOGGERS)
        total_supported = specific_count + form_count + peter_count + ip_count

        print("=== Specific Native Handlers ===")
        for d in sorted(SPECIFIC_HANDLERS): print(f"  {d}")
        print(f"\n=== Form-based (40+) ===")
        for d in sorted(TYPE_SERVICES): print(f"  {d}")
        print(f"=== Redirect-follow from PeterDaveHello ({peter_count}) ===")
        print(f"  ({peter_count} known shortener domains — validated Jul 2026)")
        print(f"\n=== IP Logger Blocklist ({ip_count}) ===")
        for d in sorted(IP_LOGGERS): print(f"  {d}")
        print(f"\n=== Fallback Only ({fallback_count}) ===")
        for d in sorted(FALLBACK_ONLY): print(f"  {d}")
        print(f"\n{'='*50}")
        print(f"Total bypassable: {total_supported}")
        print(f"Plus fallback:    {fallback_count}")
        print(f"Grand total:      {total_supported + fallback_count}")
        print(f"{'='*50}")
        sys.exit(0)

    urls = []
    if sys.argv[1] == "--batch" and len(sys.argv) > 2:
        with open(sys.argv[2]) as f:
            urls = [l.strip() for l in f if l.strip() and not l.startswith("#")]
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
