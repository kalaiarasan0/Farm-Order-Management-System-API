from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from app.config import settings
from passlib.context import CryptContext
from fastapi import HTTPException

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

async def get_password_hash(password : str) -> str:
    return pwd_context.hash(password)


async def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    except JWTError as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    print(get_password_hash("test#a&l213ai"))
    