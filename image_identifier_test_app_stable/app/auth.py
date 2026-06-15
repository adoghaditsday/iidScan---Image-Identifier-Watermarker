import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Dict, Optional

from .config import ACCOUNTS_PATH, USER_LOG_DIR

PBKDF2_ITERATIONS = 180_000


def _load_accounts() -> Dict[str, dict]:
    if not ACCOUNTS_PATH.exists():
        return {}
    try:
        return json.loads(ACCOUNTS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_accounts(accounts: Dict[str, dict]) -> None:
    ACCOUNTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    ACCOUNTS_PATH.write_text(json.dumps(accounts, indent=2), encoding="utf-8")


def _hash_password(password: str, salt: bytes) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return base64.b64encode(digest).decode("ascii")


def normalize_username(username: str) -> str:
    return "".join(ch for ch in username.strip().lower() if ch.isalnum() or ch in ("_", "-", "."))


def create_account(username: str, password: str) -> tuple[bool, str]:
    username = normalize_username(username)
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    accounts = _load_accounts()
    if username in accounts:
        return False, "That username already exists."

    salt = os.urandom(16)
    accounts[username] = {
        "salt": base64.b64encode(salt).decode("ascii"),
        "password_hash": _hash_password(password, salt),
    }
    _save_accounts(accounts)
    USER_LOG_DIR.mkdir(parents=True, exist_ok=True)
    return True, "Account created. You can sign in now."


def verify_login(username: str, password: str) -> tuple[bool, str, Optional[str]]:
    username = normalize_username(username)
    accounts = _load_accounts()
    account = accounts.get(username)
    if not account:
        return False, "Account not found.", None

    salt = base64.b64decode(account["salt"])
    attempted = _hash_password(password, salt)
    if hmac.compare_digest(attempted, account["password_hash"]):
        return True, "Signed in.", username
    return False, "Incorrect password.", None


def derive_user_key(username: str, password: str) -> bytes:
    accounts = _load_accounts()
    account = accounts.get(normalize_username(username))
    if not account:
        raise ValueError("Account not found.")
    salt = base64.b64decode(account["salt"])
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt + b"log-key", PBKDF2_ITERATIONS)
