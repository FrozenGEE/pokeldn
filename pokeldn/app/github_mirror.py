"""GitHub accelerators: prefix proxies for GitHub addresses, picked in Settings.

A mirror is prepended to the whole address: https://gh-proxy.com/https://github.com/...
Only GitHub hosts are rewritten; every other address is used as it is.
"""
import ssl
import time
import urllib.parse
import urllib.request

# (prefix, name). Empty is a direct connection; add a mirror here and it appears in Settings.
# The list was probed against PROBE_URL on 2026-11-08; every entry answered, the dot shows how
# quickly today. A mirror may go away, so keep several.
MIRRORS = (
    ("", "Direct"),
    ("https://gh-proxy.com/", "gh-proxy.com"),
    ("https://ghfile.geekertao.top/", "ghfile.geekertao.top"),
    ("https://gitproxy.click/", "gitproxy.click"),
    ("https://gh-proxy.org/", "gh-proxy.org"),
    ("https://ghproxy.imciel.com/", "ghproxy.imciel.com"),
    ("https://ghfast.top/", "ghfast.top"),
    ("https://ghproxy.cfd/", "ghproxy.cfd"),
    ("https://ghproxy.cn/", "ghproxy.cn"),
    ("https://gh-proxy.net/", "gh-proxy.net"),
)
_PROXIED = {"github.com", "api.github.com", "raw.githubusercontent.com",
            "codeload.github.com", "objects.githubusercontent.com"}
PROBE_URL = "https://raw.githubusercontent.com/Decryptu/pokeldn-decrypt-plugins/main/pokeldn-source.json"
FAST_MS = 1000
_prefix = ""


def select(prefix: str = "") -> None:
    """Use `prefix`; anything not in MIRRORS falls back to a direct connection."""
    global _prefix
    _prefix = prefix if any(prefix == p for p, _ in MIRRORS) else ""


def current() -> str:
    return _prefix


def apply(url: str, prefix: str | None = None) -> str:
    """`url` through the selected accelerator; non-GitHub addresses are unchanged."""
    mirror = _prefix if prefix is None else prefix
    if not mirror:
        return url
    try:
        host = urllib.parse.urlsplit(url).hostname
    except ValueError:
        return url
    if host not in _PROXIED:
        return url
    return mirror.rstrip("/") + "/" + url


def _context() -> ssl.SSLContext:
    # A frozen macOS build has no system certificate store that Python can read; certifi ships with flet.
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def probe(prefix: str = "", timeout: float = 8.0) -> tuple[str, int]:
    """("ok" | "slow" | "fail", milliseconds) for the accelerator's answer to a small GitHub file."""
    started = time.monotonic()
    try:
        request = urllib.request.Request(apply(PROBE_URL, prefix), headers={"User-Agent": "pokeldn-desktop"})
        with urllib.request.urlopen(request, timeout=timeout, context=_context()) as reply:
            reply.read(4096)
    except Exception:
        return "fail", int((time.monotonic() - started) * 1000)
    elapsed = int((time.monotonic() - started) * 1000)
    return ("ok" if elapsed < FAST_MS else "slow"), elapsed
