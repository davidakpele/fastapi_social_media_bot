from app.payloads.register_request import RegisterRequest
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.user import User
from fastapi.templating import Jinja2Templates
from app.utils.security import hash_password, validate_email, verify_password, create_access_token

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# Register
@router.post("/register")
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == data.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return {"msg": "User registered successfully"}

# Login
@router.post("/login")
async def login(request: Request, db: AsyncSession = Depends(get_db)):
    data = await request.json()

    email = data.get("email")
    password = data.get("password")

    # validate email
    if not email or not validate_email(email):
        raise HTTPException(status_code=400, detail="Invalid email")

    # validate password
    if not password or len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    # find user by email
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(
        data={"sub": str(user.id), "name": user.username},
        role={"admin": user.is_admin if hasattr(user, "is_admin") else False}
    )

    return {
        "access_token": token,
        "id": user.id,
        "username": user.username,
        "email": user.email
    }


