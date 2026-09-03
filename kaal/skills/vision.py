"""Vision skill — screenshot/UI photo model ko dikhao, describe/debug karwao.
Vision-supporting key/model chahiye (openrouter/openai/gemini). Fail-soft.
"""
import base64, os

MIMES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
         ".webp": "image/webp", ".gif": "image/gif"}
MAX_MB = 4

def describe(path, prompt="Is image me kya hai? UI bug ho to batao.", ask_cb=None):
    from .files import _safe
    p = _safe(path)
    if not p or not os.path.isfile(p):
        return "Image mili nahi ya unsafe path"
    ext = os.path.splitext(p)[1].lower()
    if ext not in MIMES:
        return f"Format support nahi ({ext}). png/jpg/webp do."
    if os.path.getsize(p) > MAX_MB * 1024 * 1024:
        return "Image bahut badi (4MB limit)"
    with open(p, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    try:
        from ..models.router import try_vision
        name, txt = try_vision(prompt, b64, MIMES[ext])
        if txt:
            return f" [{name}]: {txt[:800]}"
        return "Vision fail — vision model wali key chahiye (/key)"
    except Exception as e:
        return f"Vision error: {e}"[:200]
