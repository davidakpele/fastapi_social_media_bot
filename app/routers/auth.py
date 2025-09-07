from app.payloads.register_request import RegisterRequest
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.user import User
from fastapi.templating import Jinja2Templates
from app.utils.security import hash_password, validate_email, verify_password, create_access_token
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.status import HTTP_302_FOUND

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# ---------------- Register ----------------

@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/api/register")
async def register_action(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    data = await request.json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not email or not validate_email(email):
        return JSONResponse({"detail": "Invalid email"}, status_code=400)
    if not password or len(password) < 6:
        return JSONResponse({"detail": "Password must be at least 6 characters"}, status_code=400)

    result = await db.execute(select(User).filter(User.email == email))
    existing_user = result.scalars().first()
    if existing_user:
        return JSONResponse({"detail": "Email already registered"}, status_code=400)

    new_user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return JSONResponse({"msg": "User registered successfully"}, status_code=201)



@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/api/login")
async def login_action(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")

    if not email or not validate_email(email):
        return JSONResponse({"detail": "Invalid email"}, status_code=400)

    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()

    if not user or not verify_password(password, user.hashed_password):
        return JSONResponse({"detail": "Invalid credentials"}, status_code=401)

    token = create_access_token(data={"sub": str(user.id), "name": user.username})

    request.session["user"] = {
        "id": user.id,
        "username": user.username,
        "email": user.email
    }

    return JSONResponse({
        "access_token": token,
        "id": user.id,
        "username": user.username,
        "email": user.email
    })


@router.get("/logout")
def logout_user(request: Request):
    request.session.clear()
    return RedirectResponse("/auth/login", status_code=HTTP_302_FOUND)
