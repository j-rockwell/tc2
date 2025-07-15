from datetime import datetime, timedelta, timezone
from json import dumps
import jwt

def make_token(value: str, passkey: str, ttl: int) -> str:
    iat = datetime.now(tz=timezone.utc)
    exp = datetime.now(tz=timezone.utc) + timedelta(seconds=float(ttl))
    return jwt.encode({"id": value}, passkey, algorithm="HS256", headers={"exp": dumps(exp, default=str), "iat": dumps(iat, default=str)})