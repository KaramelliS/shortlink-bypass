# ShortLink Bypass 🔗

**1362 shortlink services.** One tool. No browser. No ads.

Bypass link shorteners by reverse-engineering their internal API flows, token extraction, form submission, XOR decoding, and HTTP redirect following.

```bash
python3 bypass.py https://ay.live/EXAMPLE
python3 bypass.py https://bit.ly/EXAMPLE https://tinyurl.com/EXAMPLE
python3 bypass.py --batch links.txt
python3 bypass.py --list-services   # see all 1362 services
```

## Stats

| Category | Count | Method |
|----------|------:|--------|
| 🎯 Specific native handlers | 23 | Token flow, GraphQL, XOR decode, form bypass, base64 decode |
| 📋 Form-based (Type 1/2) | 43 | Form extraction → POST `/links/go` |
| 🔗 Redirect-follow (PeterDaveHello) | **1240** | HTTP redirect chain (validated Jul 2026) |
| 🚫 IP Logger blocklist | 34 | Blocked outright |
| **✅ Total bypassable** | **1340** | |
| 🔄 Fallback (browser-based) | 31 | Social unlocks, WebSocket services |
| **🔥 GRAND TOTAL** | **1362** | (net after dedup overlaps) |

## How It Works — Architecture

The tool uses a **layered handler system** — each URL is matched against progressively more specific handlers:

```
URL → IP Logger check → Specific handler → Form handler → Known shortener → Generic redirect
```

### Layer 1: Specific Native Handlers (23 services)

| Service | Method | Technique |
|---------|--------|-----------|
| **aylink.co / ay.live** | Token flow | JS vars → `/get/tk` → `/links/go2` with fake browser signal |
| **cpmlink.co / cpmlink.pro** | Token flow | Same as aylink, different field names |
| **linkvertise.com** (+4 aliases) | GraphQL | `getDetailPageContent` → `completeDetailPageContent` → `getDetailPageTarget` |
| **adf.ly** | XOR decode | `ysmm` token: interleave → XOR → base64 → strip header |
| **boost.ink / mboost.me** | Base64 decode | Extract `kekw` attribute → base64 decode |
| **ouo.io / ouo.press** | Page scrape | Extract `window.location` or meta refresh URL |
| **try2link.com** | Form bypass | Timestamp param → form extraction → POST `/links/go` |
| **gplinks.co / gplinks.in** | Form bypass | Redirect → vid param → form extraction → POST `/links/go` |
| **pkin.me** | Form bypass | Mobile UA → form extraction → POST `/links/go` |
| **shareus.in** | API call | Firebase Cloud Function direct call |
| **anonym.to / anonymz.com / hidereferrer.com / leechall.com** | Base64 param | Extract and decode base64 from URL parameter |

### Layer 2: Form-Based (43 services)

These Indian shorteners share a common PHP backend:
1. Fetch landing page with referer
2. Extract all `<input>` values from `<form id="go-link">`
3. Sleep 5-10 seconds (anti-bot delay)
4. POST to `/links/go` with `X-Requested-With: XMLHttpRequest`
5. Parse JSON `{"url": "..."}` response

**Services:** droplink.co, tnlink.in, ez4short.com, xpshort.com, rocklinks.net, open2get.in, linkbnao.com, linkpays.in, pi-l.ink, adrinolinks.in, techymozo.com, bitshorten.com, earn4link.in, za.uy, gtlinks.me, and 28 more.

### Layer 3: Known Shorteners (1479 services)

Loaded from **PeterDaveHello/url-shorteners** — the most comprehensive public shortener domain list. The tool checks if a URL's domain is in this list and follows HTTP redirect chains. Works for virtually all standard URL shorteners.

**Examples:** bit.ly, tinyurl.com, cutt.ly, is.gd, v.gd, shorte.st, rebrand.ly, t.co, ow.ly, buff.ly, shorturl.at, clck.ru, 0x0.st, gg.gg, tiny.cc, youtu.be, fb.me, lnkd.in, festyy.com, gestyy.com, ceesty.com, corneey.com, destyy.com, t2m.io, disq.us, page.link, shortcm.li, and **1450+ more**.

### Layer 4: IP Logger Blocklist (34 domains)

Known IP logging/tracking services are detected and blocked: iplogger.com, grabify.link, 2no.co, blasze.com, and 30 more.

### Fallback (31 services)

These services require browser interaction (captcha solving, WebSocket, or social verification) and cannot be bypassed with curl alone. They're tracked for future implementation:

work.ink, boost.ink, mboost.me, rekonise.com, lootlabs.com, lootlinks.com, sub2unlock.com, sub2unlock.net, social-unlock.com, socialwolvez.com, lockr.social, just2earn.com, and 19 more.

## Installation

```bash
git clone https://github.com/KaramelliS/shortlink-bypass.git
cd shortlink-bypass
chmod +x bypass.py
```

**Requirements:** `curl` (any modern version), Python 3.8+.

For Linkvertise support: `pip install requests`

## Usage

```bash
# Single URL
python3 bypass.py https://ay.live/EXAMPLE

# Multiple URLs
python3 bypass.py https://ay.live/EXAMPLE1 https://cpmlink.co/EXAMPLE2

# Batch mode (one URL per line)
python3 bypass.py --batch links.txt

# List all 1610 supported services
python3 bypass.py --list-services

# Update shortener database from PeterDaveHello
python3 bypass.py --update-list
```

Output: each bypassed URL is printed on its own line. Failed URLs go to stderr with `[-]` prefix.

## Update Domain Database

The tool ships with 1479 known shortener domains from [PeterDaveHello/url-shorteners](https://github.com/PeterDaveHello/url-shorteners). To get the latest list:

```bash
python3 bypass.py --update-list
```

## Credits

- **PeterDaveHello/url-shorteners** — Primary domain list (1479 domains)
- **FastForward Team** — Bypass patterns and encoding algorithms
- **bypass-all-shortlinks-debloated** — Additional domain references

## License

MIT

## Author

[KaramelliS](https://github.com/KaramelliS)
