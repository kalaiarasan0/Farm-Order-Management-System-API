from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_user_db as get_async_user_db
from app.core import security
from app.models.user_tables import User
from app.schemas.users import (
    UserCreate,
    Token,
    UserSchema,
    ProfilePicUploadResponse,
    UserPersonalDetails,
    UserContactDetails,
    UserProfileDetails,
)
from app.config import settings
from app.services import users as user_service


router = APIRouter(tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = security.jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        unique_id: str = payload.get("unique_id")

        if username is None or unique_id is None:
            raise credentials_exception

        # Create a stateless User object
        # We use a minimal User object that satisfies the needs of the application
        # Note: This user object won't have all fields from DB, only what's in token
        # Note: This user object won't have all fields from DB, only what's in token

        # We return a User-like object that has attributes needed for current_user
        # For our crude implementation, we primarily need unique_id (and username)
        return User(
            id=0,  # Placeholder or extracted if needed, but unique_id is primary reference
            unique_id=unique_id,
            username=username,
            firstname="",  # Not available in stateless token unless added
            lastname="",
            email="",
            mobile="",
            is_active=True,
            gender=None,  # or default
        )

    except security.JWTError:
        raise credentials_exception


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@router.post("/auth/register", response_model=UserSchema)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_async_user_db)):
    user = await user_service.get_user_by_username(db, user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered",
        )
    return await user_service.create_user(db, user_in)


@router.post("/auth/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_user_db),
):
    user = await user_service.authenticate_user(
        db, form_data.username, form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Include unique_id in the token
    access_token = await security.create_access_token(
        data={"sub": user.username, "unique_id": str(user.unique_id)},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


# @router.get("/users/me", response_model=UserSchema)
# async def read_users_me(current_user: User = Depends(get_current_active_user)):
#     return current_user


@router.get("/users/me/personal-details", response_model=UserPersonalDetails)
async def read_users_me_personal_details(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_user_db),
):
    user = await user_service.get_user_by_unique_id(db, current_user.unique_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/users/me/contact-details", response_model=UserContactDetails)
async def read_users_me_contact_details(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_user_db),
):
    user = await user_service.get_user_by_unique_id(db, current_user.unique_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Decrypt or handle sensitive data if necessary, but schema handles mapping
    return user


@router.get("/users/me/profile-pic-details", response_model=UserProfileDetails)
async def read_users_me_profile_pic(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_user_db),
):
    user = await user_service.get_user_by_unique_id(db, current_user.unique_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users/me/profile-pic", response_model=ProfilePicUploadResponse)
async def upload_profile_pic(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_async_user_db),
):
    return await user_service.update_user_profile_pic(db, current_user, file)


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

    # asyncio.run(main())
