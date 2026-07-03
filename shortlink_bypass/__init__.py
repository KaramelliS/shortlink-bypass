"""
ShortLink Bypass — bypass 1337 URL shorteners programmatically.

Usage:
    from shortlink_bypass import bypass
    url = bypass("https://ay.live/EXAMPLE")
    print(url)  # https://cloud.mail.ru/...
"""

from .bypass import bypass, clean_url, decode_adfly_ysmm, decode_base64

__all__ = ["bypass", "clean_url", "decode_adfly_ysmm", "decode_base64", "__version__"]
__version__ = "3.1.0"
