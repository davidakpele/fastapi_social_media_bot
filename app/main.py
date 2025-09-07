from fastapi import FastAPI
from app.routers import auth, accounts, posts, analytics, webhooks
from app.config import settings
from fastapi.staticfiles import StaticFiles
import uvicorn

# Initialize FastAPI app
app = FastAPI(title=settings.PROJECT_NAME, version=settings.APP_VERSION)

# Mount the static directory for CSS and JS
# app.mount("/static", StaticFiles(directory="static"), name="static")
# Routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(accounts.router, prefix="/accounts", tags=["Accounts"])
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
