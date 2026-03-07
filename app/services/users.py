from sqlalchemy.exc import IntegrityError
from app.models.user_tables import User
from app.schemas.users import UserCreate
from app.core import security
from uuid import uuid4
from datetime import datetime
from fastapi import HTTPException
from app.core.hash import hash_value
from sqlalchemy import select, or_
import shutil
import os
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

UPLOAD_DIR = "uploads"
UPLOAD_URL_PREFIX = "/uploads"


async def get_user_by_username(db: AsyncSession, username: str):
    stmt = select(User).where(
        or_(
            User.hashed_username == hash_value(username),
            User.hashed_email == hash_value(username),
            User.hashed_mobile == hash_value(username),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str):
    stmt = select(User.email).where(User.hashed_email == hash_value(email))
    result = await db.execute(stmt)
    return result.mappings().one_or_none()


async def get_user_by_mobile(db: AsyncSession, mobile: str):
    stmt = select(User.mobile).where(User.hashed_mobile == hash_value(mobile))
    result = await db.execute(stmt)
    return result.mappings().one_or_none()


async def get_user_by_unique_id(db: AsyncSession, unique_id: str):
    stmt = select(User).where(User.unique_id == unique_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: UserCreate):
    try:
        db_user = User(
            unique_id=uuid4(),
            firstname=user.firstname,
            lastname=user.lastname,
            username=user.username,
            email=user.email,
            mobile=user.mobile,
            hashed_username=hash_value(user.username),
            hashed_email=hash_value(user.email),
            hashed_mobile=hash_value(user.mobile),
            hashed_password=await security.get_password_hash(user.password),
            gender=user.gender,
            is_active=user.is_active,
            password_create_at=datetime.now(),
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="User with this details already exists (username, email, or mobile).",
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user_by_username(db, username)
    if not user:
        return False

    # hashed_password from DB might be bytes if using LargeBinary, or string
    hashed_password = user.hashed_password
    if isinstance(hashed_password, bytes):
        hashed_password = hashed_password.decode("utf-8")

    if not await security.verify_password(password, hashed_password):
        return False
    return user


async def update_user_profile_pic(db: AsyncSession, user: User, file: UploadFile):
    try:
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)

        ext = os.path.splitext(file.filename)[1].lower()
        filename = f"{uuid4()}{ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        current_user = await get_user_by_unique_id(db, user.unique_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")

        # ✅ Store RELATIVE URL in DB
        file_url = f"{UPLOAD_URL_PREFIX}/{filename}"

        current_user.profile_file_url = file_url
        await db.commit()
        await db.refresh(current_user)

        return {"message": "profile updated successfully", "profile_file_url": file_url}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Could not upload file: {str(e)}")


# async def main():
#     from app.db.database import AsyncUserSessionLocal

#     username = "kalai1"
#     password = "kalai1"

#     async with AsyncUserSessionLocal() as db_main:
#         try:
#             user = await authenticate_user(db_main, username, password)
#             print(user)
#             # for e in events:
#             #     print(vars(e))
#             # print("Synced events:", order)
#             # print(user)
#             # hashed_password = user.hashed_password
#             # print(hashed_password)
#         except Exception as e:
#             print(f"Error: {e}")


# if __name__ == "__main__":
#     import asyncio

#     asyncio.run(main())
