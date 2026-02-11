from datetime import datetime
from sqlalchemy import Integer, String, Boolean, DateTime, Enum, TypeDecorator
from app.db.base import UserBase
from app.schemas.enums import Gender
from sqlalchemy.orm import Mapped, mapped_column
from app.encryption.encryption import encrypt, decrypt


class EncryptedString(TypeDecorator):
    impl = String(1024)  # Ensure length is enough for encrypted output
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = encrypt(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = decrypt(value)
        return value


class User(UserBase):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    unique_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )

    # REMOVE index/unique from these. They are for storage/display only.
    firstname: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    lastname: Mapped[str] = mapped_column(EncryptedString, nullable=True)
    username: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    email: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    mobile: Mapped[str] = mapped_column(EncryptedString, nullable=False)

    # USE THESE for searching and uniqueness
    hashed_username: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_mobile: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255), index=True, nullable=False
    )
    old_password: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    password_create_at: Mapped[datetime] = mapped_column(
        DateTime, index=True, default=datetime.utcnow
    )
    gender: Mapped[Gender] = mapped_column(
        Enum(Gender, name="gender_enum"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, index=True, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, index=True, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_welcome_mail_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    is_password_change_mail_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_file_url: Mapped[str] = mapped_column(String(2048), nullable=True)
