"""Vault at-rest protection — platform-gated.
`cryptography` (Fernet) mili to AES-encrypted vault (PC: `pip install cryptography`),
nahi mili (Termux) to plaintext + 0600 perms + notice. Dono format auto-detect.
Key: KAAL_VAULT_PASSWORD env, nahi to config/vault.key (0600, auto-generate).
"""
import os, json

PREFIX = "ENC1:"

def available():
    try:
        import cryptography  # noqa
        from cryptography.fernet import Fernet  # noqa
        return True
    except Exception:
        return False

def _key_bytes(password):
    import hashlib, base64
    return base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())

def _key_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "vault.key"))

def get_password():
    pw = os.environ.get("KAAL_VAULT_PASSWORD", "")
    if pw:
        return pw
    kp = _key_path()
    try:
        if os.path.isfile(kp):
            with open(kp, encoding="utf-8") as f:
                return f.read().strip()
        import secrets as _s
        pw = _s.token_urlsafe(32)
        os.makedirs(os.path.dirname(kp), exist_ok=True)
        with open(kp, "w", encoding="utf-8") as f:
            f.write(pw)
        try:
            os.chmod(kp, 0o600)
        except OSError:
            pass
        return pw
    except OSError:
        return ""

def encrypt_dict(d):
    """Returns (ok, payload_str). Lib nahi to (False, reason)."""
    if not available():
        return False, "cryptography lib nahi — plaintext + 0600"
    from cryptography.fernet import Fernet
    pw = get_password()
    if not pw:
        return False, "key nahi ban payi"
    tok = Fernet(_key_bytes(pw)).encrypt(json.dumps(d).encode())
    return True, PREFIX + tok.decode()

def decrypt_payload(payload):
    """ENC1: payload ko dict me kholo. Plaintext JSON bhi accept (legacy)."""
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str) and payload.startswith(PREFIX):
        if not available():
            return {}
        from cryptography.fernet import Fernet
        try:
            raw = Fernet(_key_bytes(get_password())).decrypt(payload[len(PREFIX):].encode())
            d = json.loads(raw)
            return d if isinstance(d, dict) else {}
        except Exception:
            return {}
    return {}
