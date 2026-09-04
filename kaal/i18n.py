"""i18n — Hindi (default) / English / Chinese UI strings.
`t(key)` se lo, seedha Hindi hardcode mat karo (naya UI text yahi add karo).
Language: config/tui.json `language` (hi|en|zh), `/lang` se badlo.
Missing key → Hindi fallback → key khud. Kabhi crash nahi.
"""
import os

LANGS = ("hi", "en", "zh")

STRINGS = {
    "quit_bye": {
        "hi": "Kaal band. Phir milenge.",
        "en": "Kaal closed. See you again.",
        "zh": "Kaal 已关闭，再见。"},
    "quit_short": {
        "hi": "Kaal band.",
        "en": "Kaal closed.",
        "zh": "Kaal 已关闭。"},
    "task_cancelled": {
        "hi": "Task roka (Ctrl+C) — partial state memory/backups me safe.",
        "en": "Task stopped (Ctrl+C) — partial state safe in memory/backups.",
        "zh": "任务已停止（Ctrl+C）——部分状态已保存在 memory/backups。"},
    "budget_title": {
        "hi": " Budget",
        "en": " Budget",
        "zh": " 预算"},
    "result_title": {
        "hi": " Result",
        "en": " Result",
        "zh": " 结果"},
    "tasks_title": {
        "hi": " Tasks",
        "en": " Tasks",
        "zh": " 任务"},
    "memory_empty": {
        "hi": "Memory khaali — pehla task karo.",
        "en": "Memory empty — run your first task.",
        "zh": "记忆为空——先运行一个任务。"},
    "no_sessions": {
        "hi": "Koi session nahi — pehla task chalao.",
        "en": "No sessions — run a task first.",
        "zh": "暂无会话——先运行一个任务。"},
    "lang_set": {
        "hi": "Language: {lang}",
        "en": "Language: {lang}",
        "zh": "语言：{lang}"},
    "lang_use": {
        "hi": "Use: /lang hi|en|zh",
        "en": "Use: /lang hi|en|zh",
        "zh": "用法：/lang hi|en|zh"},
}

def _tui_file():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..",
                                        "config", "tui.json"))

def get_lang():
    try:
        import json
        with open(_tui_file(), encoding="utf-8") as f:
            lang = (json.load(f) or {}).get("language", "hi")
        return lang if lang in LANGS else "hi"
    except Exception:
        return "hi"

def set_lang(code):
    code = str(code or "").lower()
    if code not in LANGS:
        return f"Use: /lang {'|'.join(LANGS)}"
    try:
        import json
        p = _tui_file()
        d = {}
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f) or {}
        except Exception:
            pass
        d["language"] = code
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2)
    except Exception:
        pass
    return t("lang_set", lang=code)

def t(key, **kw):
    """Translate. Missing → Hindi → key. Format params via kw."""
    try:
        s = STRINGS.get(key, {}).get(get_lang(), "")
        if not s:
            s = STRINGS.get(key, {}).get("hi", key)
        return s.format(**kw) if kw else s
    except Exception:
        return key
