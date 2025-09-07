from app.models.account import Platform
from pydantic import BaseModel

class AccountCreate(BaseModel):
    platform: Platform
    username: str