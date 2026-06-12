import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter()

@router.get("", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("", response_model=UserResponse)
def update_profile(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/image", response_model=UserResponse)
async def upload_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File provided is not an image")

    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}.{file_extension}"
    file_path = os.path.join("uploads", "profile_images", unique_filename)

    # Delete old image if exists
    if current_user.profile_image and current_user.profile_image.startswith("/uploads/profile_images/"):
        old_filename = current_user.profile_image.split("/")[-1]
        old_file_path = os.path.join("uploads", "profile_images", old_filename)
        if os.path.exists(old_file_path):
            os.remove(old_file_path)

    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    image_url = f"/uploads/profile_images/{unique_filename}"
    current_user.profile_image = image_url
    
    db.commit()
    db.refresh(current_user)
    
    return current_user
