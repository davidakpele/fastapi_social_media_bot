# bot_interface.py
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_302_FOUND

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/")
def home(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/auth/login", status_code=HTTP_302_FOUND)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})
