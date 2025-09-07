import os
from fastapi import FastAPI
from app.routers import auth, accounts, bot_interface, schedule
from app.config import settings
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

app = FastAPI(title=settings.PROJECT_NAME, version=settings.APP_VERSION)

# Use correct static path
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key="super-secret-session-key")
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(accounts.router, prefix="/accounts", tags=["Accounts"])
app.include_router(bot_interface.router, tags=["Home"])
# Include the WebSocket router
app.include_router(schedule.router, tags=["WebSocket"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
