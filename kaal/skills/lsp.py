"""Minimal LSP client — stdlib only, zero-dep, platform-safe.
Server binary chahiye (PC: pyright-langserver/node; Termux: usually nahi).
Binary nahi to clean 'n/a' — crash nahi. Full IDE features nahi,
sirf: initialize → didOpen → publishDiagnostics → shutdown.
"""
import json, shutil, subprocess

def available(server_cmd="pyright-langserver"):
    """Server binary mili?"""
    return shutil.which(server_cmd.split()[0]) is not None

def _encode(msg):
    body = json.dumps(msg).encode()
    return b"Content-Length: %d\r\n\r\n" % len(body) + body

def _read_msg(proc, timeout=20):
    import select
    end = __import__("time").time() + timeout
    headers = {}
    buf = b""
    while __import__("time").time() < end:
        r, _, _ = select.select([proc.stdout], [], [], max(0.1, end - __import__("time").time()))
        if not r:
            continue
        chunk = proc.stdout.read(1)
        if not chunk:
            break
        buf += chunk
        if buf.endswith(b"\r\n\r\n"):
            break
    for line in buf.decode("utf-8", "replace").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    try:
        n = int(headers.get("content-length", "0"))
    except ValueError:
        return None
    data = b""
    while len(data) < n and __import__("time").time() < end:
        r, _, _ = select.select([proc.stdout], [], [], max(0.1, end - __import__("time").time()))
        if r:
            data += proc.stdout.read(n - len(data))
    try:
        return json.loads(data.decode("utf-8", "replace") or "null")
    except Exception:
        return None

class LSPClient:
    """Tiny JSON-RPC stdio client. `with` me use karo (auto-shutdown)."""

    def __init__(self, server_cmd):
        self.cmd = server_cmd.split()
        self.proc = None
        self._id = 0

    def __enter__(self):
        # bufsize=0 (unbuffered): select()+read(1) sahi chale.
        # Buffered pipe me pehla read sab khinch leta, select phir block karta.
        self.proc = subprocess.Popen(self.cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, bufsize=0)
        return self

    def __exit__(self, *a):
        try:
            self.notify("exit", None)
            self.proc.kill()
        except Exception:
            pass
        return False

    def _send(self, msg):
        self.proc.stdin.write(_encode(msg))
        self.proc.stdin.flush()

    def request(self, method, params, timeout=20):
        self._id += 1
        rid = self._id
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        end = __import__("time").time() + timeout
        while __import__("time").time() < end:
            m = _read_msg(self.proc, timeout=max(1, int(end - __import__("time").time())))
            if isinstance(m, dict) and m.get("id") == rid:
                return m.get("result"), m.get("error")
        return None, "timeout"

    def notify(self, method, params):
        try:
            self._send({"jsonrpc": "2.0", "method": method, "params": params})
        except Exception:
            pass

    def collect_diagnostics(self, timeout=15):
        """publishDiagnostics notifications jama karo. Returns [diag]."""
        import time as _t
        out = []
        end = _t.time() + timeout
        while _t.time() < end:
            m = _read_msg(self.proc, timeout=max(1, int(end - _t.time())))
            if not isinstance(m, dict):
                continue
            if m.get("method") == "textDocument/publishDiagnostics":
                out.extend(((m.get("params") or {}).get("diagnostics") or []))
                break
        return out

def diagnose(filepath, server_cmd="pyright-langserver --stdio", root=".", timeout=25):
    """File ke LSP diagnostics lao. Server nahi to 'n/a ...' string."""
    import os
    if os.name == "nt":
        return "n/a (Windows pipes pe select() nahi — Linux/macOS/Termux pe chalao)"
    if not available(server_cmd):
        return "n/a (LSP server nahi — PC pe pyright install karo)"
    fp = os.path.abspath(filepath)
    if not os.path.isfile(fp):
        return "n/a (file nahi mili)"
    try:
        with open(fp, encoding="utf-8", errors="replace") as f:
            text = f.read(200000)
    except OSError as e:
        return f"n/a ({e})"[:120]
    uri = "file://" + fp
    root_uri = "file://" + os.path.abspath(root)
    try:
        with LSPClient(server_cmd) as c:
            c.request("initialize", {"processId": None, "rootUri": root_uri,
                                     "capabilities": {}}, timeout=timeout)
            c.notify("initialized", {})
            c.notify("textDocument/didOpen", {"textDocument": {
                "uri": uri, "languageId": "python", "version": 1, "text": text}})
            diags = c.collect_diagnostics(timeout=timeout)
            c.request("shutdown", None, timeout=10)
        if not diags:
            return "LSP: koi diagnostic nahi (clean)"
        lines = [f"L{d.get('range', {}).get('start', {}).get('line', '?')}: "
                 f"{d.get('message', '')[:120]}" for d in diags[:10]]
        return f"LSP: {len(diags)} diagnostic(s)\n" + "\n".join(lines)
    except Exception as e:
        return f"LSP fail: {e}"[:200]
