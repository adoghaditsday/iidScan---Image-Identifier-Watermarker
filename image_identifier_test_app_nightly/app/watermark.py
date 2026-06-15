import base64
import hashlib
import json
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from PIL import Image

from .config import MAGIC_HEADER

TERMINATOR = "<END_GSG3_ID>"


def generate_identifier() -> str:
    return "GSG3-IMG-" + secrets.token_hex(8).upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_payload(identifier_code: str, signature_name: str = "", signature_note: str = "") -> Dict[str, Any]:
    return {
        "magic": MAGIC_HEADER,
        "identifier_code": identifier_code,
        "created_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "signature_name": signature_name,
        "signature_note": signature_note,
    }


def _payload_to_bits(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + TERMINATOR
    encoded = base64.b64encode(raw.encode("utf-8"))
    return "".join(f"{byte:08b}" for byte in encoded)


def _bits_to_payload(bits: str) -> Optional[Dict[str, Any]]:
    usable_len = len(bits) - (len(bits) % 8)
    if usable_len <= 0:
        return None

    try:
        data = bytes(int(bits[i:i+8], 2) for i in range(0, usable_len, 8))
        decoded = base64.b64decode(data, validate=False).decode("utf-8", errors="ignore")
    except Exception:
        return None

    if TERMINATOR not in decoded:
        return None

    json_text = decoded.split(TERMINATOR, 1)[0]
    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError:
        return None

    if payload.get("magic") != MAGIC_HEADER:
        return None
    return payload


def embed_identifier(input_path: Path, output_path: Path, payload: Dict[str, Any]) -> None:
    image = Image.open(input_path).convert("RGBA")
    pixels = list(image.getdata())
    bits = _payload_to_bits(payload)

    if len(bits) > len(pixels) * 3:
        raise ValueError("Image is too small to hold identifier payload.")

    new_pixels = []
    bit_index = 0

    for pixel in pixels:
        r, g, b, a = pixel
        channels = [r, g, b]
        for c in range(3):
            if bit_index < len(bits):
                channels[c] = (channels[c] & ~1) | int(bits[bit_index])
                bit_index += 1
        new_pixels.append((channels[0], channels[1], channels[2], a))

    marked = Image.new("RGBA", image.size)
    marked.putdata(new_pixels)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    marked.save(output_path, format="PNG")


def extract_identifier(image_path: Path, max_bits: int = 20000) -> Optional[Dict[str, Any]]:
    image = Image.open(image_path).convert("RGBA")
    pixels = list(image.getdata())
    bits = []

    for r, g, b, _a in pixels:
        bits.append(str(r & 1))
        bits.append(str(g & 1))
        bits.append(str(b & 1))
        if len(bits) >= max_bits:
            break

    return _bits_to_payload("".join(bits))
