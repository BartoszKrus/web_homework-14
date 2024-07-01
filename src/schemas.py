from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict

from datetime import date
from datetime import datetime


class ContactModel(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birth_date: date
    additional_info: Optional[str] = None

class ContactCreate(ContactModel):
    pass

class ContactUpdate(ContactModel):
    pass

class ContactResponse(ContactModel):
    id: int
    owner_id: int

    model_config = ConfigDict(from_attributes=True)

class UserModel(BaseModel):
    username: str
    email: str
    password: str

class UserDb(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    avatar: str

    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    user: UserDb
    detail: str = "User successfully created"


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr