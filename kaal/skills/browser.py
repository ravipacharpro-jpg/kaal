"""Browser skill — Playwright MCP agar available, warna light text fetch (Termux-safe)."""
import re, shutil, urllib.request

def playwright_available():
    return shutil.which("npx") is not None

def fetch_text(url, max_chars=1500):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    # Playwright MCP full automation Phase-6 me (npx server spawn); abhi detect + light fetch
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "kaal/0.1"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read(200000).decode("utf-8", "replace")
    except Exception as e:
        return f"Fetch fail: {e}"[:200]
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()[:max_chars]
    tag = " [playwright ready]" if playwright_available() else " [light-fetch]"
    out = text if text else "Page khaali mili"
    return (out + tag)[:max_chars + 20]
