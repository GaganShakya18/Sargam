from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class PasswordResetRequest(BaseModel):
    email: EmailStr
    new_password: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


class ProfileUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None


class UserPreferencesUpdate(BaseModel):
    audio_quality: Optional[str] = None
    streaming_quality: Optional[str] = None
    autoplay: Optional[bool] = None
    crossfade: Optional[int] = None
    explicit_content: Optional[bool] = None
    downloads_enabled: Optional[bool] = None
    theme: Optional[str] = None
    dark_mode: Optional[bool] = None


class UserPrivacyUpdate(BaseModel):
    listening_history_enabled: Optional[bool] = None
    search_history_enabled: Optional[bool] = None
    profile_visible: Optional[bool] = None
    account_visibility: Optional[str] = None


class SearchHistoryCreate(BaseModel):
    query: str = Field(min_length=1, max_length=200)

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Search query cannot be empty")
        return normalized


class UserOut(UserBase):
    id: str
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    account_type: str = "Free"
    is_active: bool = True

    class Config:
        from_attributes = True
