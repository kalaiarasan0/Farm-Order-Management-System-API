from cryptography.fernet import Fernet
from app.config import settings


# import os

# load_dotenv()
# key = os.getenv('FERNET_KEY')

# print(key)

if not settings.FERNET_KEY:
    raise ValueError("FERNET_KEY not found in environment variables")

fernet = Fernet(settings.FERNET_KEY.encode())

def encrypt(data: str) -> str:
    if data is None:
        return None
    return fernet.encrypt(data.encode()).decode()

def decrypt(data: str) -> str:
    if data is None:
        return None
    return fernet.decrypt(data.encode()).decode()
