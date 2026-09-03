"""GitHub MCP client — repo/issues summary, token optional."""
import json, urllib.request

API = "https://api.github.com"

def _get(path, token=""):
    req = urllib.request.Request(API + path, headers={"User-Agent": "kaal/0.1",
        **({"Authorization": f"Bearer {token}"} if token else {})})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.load(r)
    except Exception as e:
        return {"error": str(e)[:150]}

def repo_info(full, token=""):
    d = _get(f"/repos/{full}", token)
    if "error" in d:
        return d["error"]
    return f"{d.get('full_name')}: ⭐{d.get('stargazers_count')} | {str(d.get('description'))[:120]}"

def list_issues(full, token=""):
    d = _get(f"/repos/{full}/issues?per_page=5", token)
    if isinstance(d, dict) and "error" in d:
        return d["error"]
    out = [f"#{i.get('number')} {i.get('title')}"[:80] for i in d[:5]]
    return " | ".join(out) if out else "Koi open issue nahi"
