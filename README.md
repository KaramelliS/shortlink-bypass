<div align="center">
  <h1>🔗 ShortLink Bypass</h1>
  <p><strong>Bypass 1337 URL shorteners — no browser, no ads, just curl + Python</strong></p>

  <p>
    <a href="https://github.com/KaramelliS/shortlink-bypass/stargazers">
      <img src="https://img.shields.io/github/stars/KaramelliS/shortlink-bypass?style=flat-square&logo=github" alt="Stars">
    </a>
    <a href="https://github.com/KaramelliS/shortlink-bypass/blob/master/LICENSE">
      <img src="https://img.shields.io/github/license/KaramelliS/shortlink-bypass?style=flat-square" alt="License">
    </a>
    <a href="https://pypi.org/project/shortlink-bypass/">
      <img src="https://img.shields.io/pypi/v/shortlink-bypass?style=flat-square&logo=pypi" alt="PyPI">
    </a>
    <a href="https://github.com/KaramelliS/shortlink-bypass/actions">
      <img src="https://img.shields.io/github/actions/workflow/status/KaramelliS/shortlink-bypass/ci.yml?style=flat-square" alt="CI">
    </a>
    <a href="#">
      <img src="https://img.shields.io/badge/services-1337-blue?style=flat-square" alt="1337 services">
    </a>
    <a href="#">
      <img src="https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square&logo=python" alt="Python 3.8+">
    </a>
  </p>

  <p>
    <code>pip install shortlink-bypass</code> •
    <code>python3 -m shortlink_bypass https://ay.live/EXAMPLE</code> •
    <code>python3 -c "from shortlink_bypass import bypass; print(bypass('https://ay.live/EXAMPLE'))"</code>
  </p>
</div>

---

**ShortLink Bypass** is a **free, open-source URL shortener bypass tool** that works on **1337 services** including aylink.co, ay.live, cpmlink.co, cpmlink.pro, linkvertise.com, adf.ly, boost.ink, ouo.io, try2link.com, gplinks.co, bit.ly, tinyurl.com, cutt.ly, shorte.st, and **1240+ more**. No browser, no API keys, no captchas — just curl and Python.

## ✨ Features

- **🚀 1337 supported services** — 1306 bypassable + 31 tracked
- **🖥️ No browser needed** — pure HTTP requests via curl
- **🔑 No API keys** — self-contained, works offline
- **⚡ Batch mode** — process thousands of links in one command
- **🐍 Zero dependencies** — only curl + Python 3.8+
- **🔄 Auto-update** — `--update-list` fetches latest shorteners
- **📋 List all services** — `--list-services` shows everything

## 🚀 Quick Install

### Option 1: pip (recommended)
```bash
pip install shortlink-bypass
shortlink-bypass https://ay.live/EXAMPLE
```

### Option 2: One-liner
```bash
curl -sL https://raw.githubusercontent.com/KaramelliS/shortlink-bypass/master/bypass.py > /usr/local/bin/shortlink-bypass && chmod +x /usr/local/bin/shortlink-bypass
```

### Option 3: Clone
```bash
git clone https://github.com/KaramelliS/shortlink-bypass.git
cd shortlink-bypass
python3 bypass.py https://ay.live/EXAMPLE
```

## 📊 Supported Services

| Category | Count | Method |
|----------|------:|--------|
| 🎯 Specific native handlers | 23 | Token flow, GraphQL, XOR decode, base64 decode |
| 📋 Form-based (Type 1/2) | 43 | Form extract → POST `/links/go` |
| 🔗 Redirect-follow (validated) | **1240** | HTTP redirect chain |
| **✅ Total bypassable** | **1306** | |
| 🔄 Fallback tracked | 31 | Browser-based social unlocks |
| **🔥 GRAND TOTAL** | **1337** | |

### 🎯 Native Handlers (23)

| Service | Method |
|---------|--------|
| **aylink.co, ay.live** | JS token → `/get/tk` → `/links/go2` |
| **cpmlink.co, cpmlink.pro** | Same token flow |
| **linkvertise.com** (+ 4 aliases) | Internal GraphQL API |
| **adf.ly** | XOR decode (`ysmm` algorithm) |
| **boost.ink, mboost.me** | Base64 decode (`kekw` attribute) |
| **ouo.io, ouo.press** | Page scrape |
| **try2link.com** | Form bypass with timestamp |
| **gplinks.co, gplinks.in** | Form bypass with redirect |
| **pkin.me** | Mobile UA form bypass |
| **shareus.in** | Firebase Cloud Function |
| **anonym.to, anonymz.com** | Base64 parameter decode |
| **hidereferrer.com, leechall.com** | Base64 parameter decode |

### 📋 Form-Based (43)

droplink.co, tnlink.in, ez4short.com, xpshort.com, rocklinks.net, open2get.in, linkbnao.com, linkpays.in, pi-l.ink, adrinolinks.in, techymozo.com, bitshorten.com, earn4link.in, za.uy, gtlinks.me, and 28 more.

### 🔗 Redirect-Follow (1240)

bit.ly, tinyurl.com, cutt.ly, is.gd, v.gd, shorte.st, rebrand.ly, t.co, ow.ly, buff.ly, shorturl.at, clck.ru, 0x0.st, gg.gg, tiny.cc, youtu.be, fb.me, lnkd.in, festyy.com, gestyy.com, ceesty.com, corneey.com, destyy.com, t2m.io, disq.us, page.link, and **1215+ more** — loaded from [PeterDaveHello/url-shorteners](https://github.com/PeterDaveHello/url-shorteners), validated July 2026.

### 🔄 Fallback Tracked (31)

work.ink, rekonise.com, lootlabs.com, lootlinks.com, sub2unlock.com, social-unlock.com, socialwolvez.com, lockr.social, just2earn.com, and 22 more.

## 📖 Usage

```bash
# Single URL
python3 bypass.py https://ay.live/EXAMPLE

# Multiple URLs
python3 bypass.py https://ay.live/EXAMPLE1 https://cpmlink.co/EXAMPLE2

# Batch mode
python3 bypass.py --batch links.txt

# List all 1337 supported services
python3 bypass.py --list-services

# Update shortener database
python3 bypass.py --update-list

# Pipe output to file
python3 bypass.py https://ay.live/EXAMPLE >> resolved.txt
```

### Output

Each bypassed URL is printed on its own line:
```
https://cloud.mail.ru/public/XXXX/YYYYY
```

Failed URLs go to stderr with `[-]` prefix:
```
[-] Failed: https://example.com/badlink
```

## 🔧 How It Works

The tool uses a **layered handler architecture** — increasingly specific handlers are tried for each URL:

```
URL → Specific handler → Form handler → Known shortener → Generic redirect
```

### Token Flow (aylink/cpmlink)
1. Fetch landing page → extract `_a`, `_t`, `_d` tokens + CSRF
2. POST to `/get/tk` → get session key
3. POST to `/links/go2` with fake browser signal → get destination
4. Follow `bildirim.online` intermediate → final URL

### GraphQL (linkvertise)
1. `getDetailPageContent` → access token
2. `completeDetailPageContent` → post token
3. `getDetailPageTarget` → final URL

### XOR Decode (adf.ly)
1. Extract `ysmm` token from page
2. Interleave even/odd chars → XOR digit pairs → Base64 decode
3. Strip 16-char noise header → final URL

### Form Bypass (40+ Indian shorteners)
1. Fetch landing page with referer
2. Extract `<form id="go-link">` inputs
3. Sleep 5-10s (anti-bot delay)
4. POST to `/links/go` with `X-Requested-With` header
5. Parse JSON `{"url": "..."}` response

### Redirect Follow (1240 shorteners)
Follows HTTP 301/302/307 redirect chains with browser-like User-Agent. Works for virtually all standard URL shorteners.

## 📦 PyPI Package

```bash
pip install shortlink-bypass
```

### Use as library in your code

```python
from shortlink_bypass import bypass

# Single URL
url = bypass("https://ay.live/EXAMPLE")
print(url)  # https://cloud.mail.ru/...

# Multiple URLs
urls = [bypass(u) for u in ["https://ay.live/A", "https://bit.ly/B"]]
```

### Use as CLI

```bash
# Via pip entry point
shortlink-bypass https://ay.live/EXAMPLE

# Via python -m
python3 -m shortlink_bypass https://ay.live/EXAMPLE

# Batch
python3 -m shortlink_bypass --batch links.txt
```

## 🐳 Docker

```bash
docker run --rm karamellis/shortlink-bypass https://ay.live/EXAMPLE
```

## 📈 Domain Validation

All 1479 domains from [PeterDaveHello/url-shorteners](https://github.com/PeterDaveHello/url-shorteners) were **validated in July 2026**:
- **1240 alive** (HTTP 200) → kept in list
- **239 dead** (timeout/502/parked) → removed

Run `python3 validate_domains.py` to re-check anytime.

## 🤝 Contributing

Found a service that doesn't work? Want to add a new bypass pattern?

1. Add your handler function to `bypass.py`
2. Add the domain to `DOMAIN_HANDLERS`
3. Submit a PR

```python
def bypass_myservice(url):
    # Your bypass logic here
    return destination_url

SPECIFIC_HANDLERS["myservice.com"] = bypass_myservice
```

## 📜 License

MIT — free to use, modify, and distribute.

## ⭐ Star History

If you find this useful, [star the repo on GitHub](https://github.com/KaramelliS/shortlink-bypass) — it helps others discover it too!

## 🙏 Credits

- **PeterDaveHello** — [url-shorteners](https://github.com/PeterDaveHello/url-shorteners) domain collection
- **FastForward Team** — Bypass algorithms and patterns
- **bypass-all-shortlinks-debloated** — Additional domain references
