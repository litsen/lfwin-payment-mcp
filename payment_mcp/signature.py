import hashlib
from urllib.parse import unquote


def build_signing_payload(data: dict[str, object], sign_key: str) -> str:
    normalized = {}
    for key, value in data.items():
        if key == "sign" or value is None:
            continue
        raw = str(value)
        if key == "notify_url":
            raw = unquote(raw)
        normalized[key] = raw

    pairs = [f"{key}={normalized[key]}" for key in sorted(normalized.keys())]
    return f"{'&'.join(pairs)}&signkey={sign_key}"


def md5_sign(data: dict[str, object], sign_key: str) -> str:
    payload = build_signing_payload(data, sign_key)
    return hashlib.md5(payload.encode("utf-8")).hexdigest()
