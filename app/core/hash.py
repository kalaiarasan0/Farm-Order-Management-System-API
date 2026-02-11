import hmac
import hashlib
from app.config import settings

def hash_value(value: str) -> str:
    if value is None:
        return None

    return hmac.new(
        key=settings.SECRET_KEY.encode(),
        msg=value.lower().encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
