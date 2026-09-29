
from pydantic import EmailStr
from sqlmodel import SQLModel

from app.models.user import UserBase


class UserUpdate(SQLModel):
    username: str | None
    email: EmailStr | None
 
class AdminCreate(UserBase):
    role:str = "admin"

class RegularUserCreate(UserBase):
    role:str = "regular_user"

class UserResponse(SQLModel):
    id: int
    username:str
    email: EmailStr

class SignupRequest(SQLModel):
    username: str
    email: EmailStr
    password: str
