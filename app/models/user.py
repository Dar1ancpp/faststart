
from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class UserBase(SQLModel,):
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)
    password: str
    role:str = ""

class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)