"""Project-type detection — markers dekh ke stack + test/lint commands suggest.
test_run ko project-aware banata hai.
"""
import os

MARKERS = [
    ("python-pytest", ("pytest.ini", "tests/", "test_"), "python3 -m pytest -q", "python3 -m py_compile"),
    ("python", ("requirements.txt", "setup.py", "pyproject.toml"), "python3 -m pytest -q", "python3 -m py_compile"),
    ("node", ("package.json",), "npm test", "npx tsc --noEmit"),
    ("rust", ("Cargo.toml",), "cargo test", "cargo clippy"),
    ("go", ("go.mod",), "go test ./...", "go vet ./..."),
]

def detect(root="."):
    root = os.path.abspath(os.path.expanduser(root))
    try:
        names = set(os.listdir(root))
    except OSError:
        return {"type": "unknown", "test": "", "lint": ""}
    for typ, markers, test, lint in MARKERS:
        for m in markers:
            if m.endswith("/") and os.path.isdir(os.path.join(root, m[:-1])):
                return {"type": typ, "test": test, "lint": lint}
            if not m.endswith("/") and os.path.exists(os.path.join(root, m)):
                return {"type": typ, "test": test, "lint": lint}
    return {"type": "unknown", "test": "", "lint": ""}

def describe(root="."):
    d = detect(root)
    if d["type"] == "unknown":
        return "Project type pata nahi — test command batao"
    return f"Project: {d['type']} | test: {d['test']} | lint: {d['lint']}"

CTX_FILES = ("AGENTS.md", "CLAUDE.md")

def project_context(root=".", max_chars=1500):
    """AGENTS.md/CLAUDE.md project instructions padho (OpenCode-style convention).
    Nahi mili to ''. Brain system prompt me inject hoti hai."""
    root = os.path.abspath(os.path.expanduser(root))
    for name in CTX_FILES:
        p = os.path.join(root, name)
        try:
            if os.path.isfile(p) and os.path.getsize(p) < 20000:
                with open(p, encoding="utf-8", errors="replace") as f:
                    txt = f.read().strip()[:max_chars]
                if txt:
                    return f"PROJECT CONTEXT ({name} se):\n{txt}"
        except OSError:
            continue
    return ""
