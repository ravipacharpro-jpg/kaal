"""Browser skill — light text fetch, summary only (Termux-safe, no selenium)."""
import re, urllib.request

def fetch_text(url, max_chars=1500):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "kaal/0.1"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read(200000).decode("utf-8", "replace")
    except Exception as e:
        return f"Fetch fail: {e}"[:200]
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()[:max_chars]
    return text if text else "Page khaali mili"
