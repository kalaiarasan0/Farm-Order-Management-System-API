import cloudinary
import cloudinary.uploader
import cloudinary.api

# from cloudinary import CloudinaryImage
from app.config import settings
from fastapi import UploadFile

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)


async def upload_file(file: UploadFile):
    result = cloudinary.uploader.upload(file.file)
    return result
