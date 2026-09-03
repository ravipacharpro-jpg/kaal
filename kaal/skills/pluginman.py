"""Plugin system — community skills bina core chhue.
skills/plugins/<name>.py me TOOLS = [{name, desc, params, fn}] rakho.
Default OFF — /plugin enable <name> se on. Sirf bharosemand code enable karo.
"""
import importlib.util
import os

DIR = os.path.join(os.path.dirname(__file__), "plugins")
STATE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                     "config", "plugins.json"))

def _state():
    import json
    try:
        with open(STATE, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}

def _save(d):
    import json
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)

def list_all():
    out = []
    if not os.path.isdir(DIR):
        return out
    st = _state()
    for fn in sorted(os.listdir(DIR)):
        if fn.endswith(".py") and fn != "__init__.py":
            out.append((fn[:-3], bool(st.get(fn[:-3], False))))
    return out

def enable(name, on=True):
    st = _state()
    st[name] = bool(on)
    _save(st)
    return f"Plugin {name}: {'ON' if on else 'OFF'}"

def load_enabled():
    """Enabled plugins ke TOOLS load karo. Returns [tool dicts]."""
    tools = []
    for name, on in list_all():
        if not on:
            continue
        p = os.path.join(DIR, name + ".py")
        try:
            spec = importlib.util.spec_from_file_location(f"kaal_plugin_{name}", p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            for t in getattr(mod, "TOOLS", []):
                if isinstance(t, dict) and callable(t.get("fn")):
                    tools.append(t)
        except Exception as e:
            tools.append({"name": f"plugin-{name}-error", "desc": str(e)[:100],
                          "params": "-", "fn": lambda a: "plugin load fail"})
    return tools
