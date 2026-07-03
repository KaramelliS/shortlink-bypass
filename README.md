# ShortLink Bypass

Universal multi-service shortlink bypass tool — no browser, no ads, just curl + Python.

Bypass link shorteners by reverse-engineering their internal API flows. No external APIs, no captchas, no browser automation needed for supported services.

## Features

- **No browser needed** — pure HTTP(S) requests via curl
- **No API keys** — self-contained, all logic is local
- **Batch mode** — process multiple links at once
- **70+ services** — 40 native handlers + 30 fallback-tracked services
- **Zero dependencies** — only needs `curl` and Python 3.8+

## Supported Services

### ✅ Native Handlers (fully working)

| Category | Services |
|----------|----------|
| **Token-based** | aylink.co, ay.live, cpmlink.co, cpmlink.pro |
| **GraphQL** | linkvertise.com, link-target.net, link-center.net, link-hub.net, direct-link.net |
| **Redirect-follow** | adf.ly, adfoc.us, shorte.st, ouo.io, ouo.press, bit.ly, tinyurl.com, cutt.ly, is.gd, v.gd, rebrand.ly, t.co, rb.gy, tiny.one, short.link, ow.ly, buff.ly, shorturl.at, shrinkearn.com, shrinkme.io, linkbucks.com, bc.vc, soo.gd, mcaf.ee, clck.ru, 0x0.st, gg.gg, tiny.cc, youtu.be, fb.me, lnkd.in |

### 🔄 Fallback-tracked (need browser/API — PRs welcome)

work.ink, workink.click, boost.ink, mboost.me, rekonise.com, lootlabs.com, lootlinks.com, loot-link.com, sub2unlock.com, sub2unlock.net, sub2unlock.io, sub2get.com, sub4unlock.com, sub4unlock.pro, subfinal.com, social-unlock.com, socialwolvez.com, lockr.social, just2earn.com, gplinks.in, gplinks.co, try2link.com, shareus.in, droplink.co, tnlink.in, xpshort.com, ez4short.com, rocklinks.net, gtlinks.me, pkin.me

## Installation

```bash
git clone https://github.com/KaramelliS/shortlink-bypass.git
cd shortlink-bypass
chmod +x bypass.py
```

Requirements: `curl` (any modern version), Python 3.8+.

For Linkvertise support, the `requests` library is needed:
```bash
# Most systems have it pre-installed. If not:
pip install requests
```

## Usage

```bash
# Single URL
python3 bypass.py https://ay.live/EXAMPLE

# Multiple URLs
python3 bypass.py https://ay.live/EXAMPLE1 https://cpmlink.co/EXAMPLE2

# Batch mode (one URL per line)
python3 bypass.py --batch links.txt

# List all supported services
python3 bypass.py --list-services

# Pipe output
python3 bypass.py https://ay.live/EXAMPLE >> resolved.txt
```

### Output format

Each bypassed URL is printed on its own line:

```
https://cloud.mail.ru/public/XXXX/YYYYY
```

Failed URLs are printed to stderr with the `[-]` prefix:
```
[-] Failed: https://example.com/badlink
```

## How It Works

### Aylink / CPMLink
These services use a JavaScript-based token flow:
1. Fetch landing page → extract `_a`, `_t`, `_d` tokens + CSRF + visitor token
2. POST to `/get/tk` with extracted tokens → get session key
3. POST to `/links/go2` with fake browser signal → get destination URL
4. Follow `bildirim.online` intermediate redirect → final `cloud.mail.ru` URL

### Linkvertise
Uses the internal GraphQL API:
1. `getDetailPageContent` mutation → get access token
2. `completeDetailPageContent` mutation → get post token
3. `getDetailPageTarget` mutation → get final URL

### Simple Shorteners
Follows HTTP redirect chains with browser-like headers. Works for adf.ly, bit.ly, tinyurl, cutt.ly, is.gd, and 30+ similar services.

## Adding New Services

To add a new service, create a function in `bypass.py` and add it to the `DOMAIN_HANDLERS` dict:

```python
def bypass_myservice(url):
    # Your bypass logic here
    return destination_url

DOMAIN_HANDLERS["myservice.com"] = bypass_myservice
```

## License

MIT

## Author

[KaramelliS](https://github.com/KaramelliS)
