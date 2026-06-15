import base64
import hashlib
from pathlib import Path

from .config import USER_LOG_DIR
from .database import utc_now_iso


def _keystream(key: bytes, length: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < length:
        out.extend(hashlib.sha256(key + counter.to_bytes(8, "big")).digest())
        counter += 1
    return bytes(out[:length])


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    stream = _keystream(key, len(data))
    return bytes(a ^ b for a, b in zip(data, stream))


class EncodedActivityLog:
    """Simple local encoded log for test builds.

    This is intended to keep casual local browsing from reading the log file directly.
    It is not a replacement for audited production encryption.
    """

    def __init__(self, username: str, key: bytes):
        USER_LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.username = username
        self.key = key
        safe_name = "".join(ch for ch in username if ch.isalnum() or ch in ("_", "-", "."))
        self.path: Path = USER_LOG_DIR / f"{safe_name}.elog"

    def read(self) -> str:
        if not self.path.exists():
            return ""
        raw = self.path.read_text(encoding="utf-8").strip()
        if not raw:
            return ""
        try:
            decoded = base64.b64decode(raw.encode("ascii"))
            plain = _xor_bytes(decoded, self.key)
            return plain.decode("utf-8", errors="replace")
        except Exception:
            return "[Unable to decode this local log with the current sign-in key.]"

    def write(self, text: str) -> None:
        data = text.encode("utf-8")
        encoded = base64.b64encode(_xor_bytes(data, self.key)).decode("ascii")
        self.path.write_text(encoded, encoding="utf-8")

    def append(self, message: str) -> None:
        current = self.read()
        line = f"[{utc_now_iso()}] {message}\n"
        self.write(current + line)
