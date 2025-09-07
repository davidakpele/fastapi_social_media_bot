import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timezone
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session
from app.models.post import Post
from typing import Set
from jose import JWTError, jwt
from app.config import settings
from app.utils.security import decode_access_token, auth_error

router = APIRouter()
scheduler = AsyncIOScheduler()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

class ConnectionManager:
    """Manages active WebSocket connections with JWT authentication."""
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, token: str):
        """Verify token first, then accept connection."""
        try:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            if user_id is None:
                raise auth_error("Invalid token: missing subject (sub).")
            websocket.state.user_id = int(user_id)
        except Exception as e:
            print(f"[ERROR] JWT validation failed: {e}")
            await websocket.close(code=4000, reason="Invalid token")
            return False

        await websocket.accept()
        self.active_connections.add(websocket)
        return True

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: str):
        for ws in list(self.active_connections):
            try:
                await ws.send_text(message)
            except WebSocketDisconnect:
                self.disconnect(ws)
            except Exception as e:
                print(f"[ERROR] Failed to send message: {e}")
                self.disconnect(ws)

manager = ConnectionManager()

async def publish_scheduled_posts():
    """
    Fetches posts with status 'scheduled' and scheduled_time <= now.
    Marks them as published and notifies connected clients via WebSocket.
    """
    published_post_ids = []
    async with async_session() as db:
        now = datetime.now(timezone.utc)
        try:
            result = await db.execute(
                select(Post)
                .filter(Post.status == "scheduled")
                .filter(Post.scheduled_time <= now)
            )
            posts = result.scalars().all()

            if not posts:
                print("[INFO] No scheduled posts to publish at this time.")
                return

            for post in posts:
                post.status = "published"
                post.published_time = now
                published_post_ids.append(post.id)
                print(f"[INFO] Post id={post.id} auto-published for user_id={post.user_id}")

            await db.commit()
            
            # Broadcast update to clients
            if published_post_ids:
                message = "An update has occurred. Please refresh your data."
                print(f"[INFO] Broadcasting: {message}")
                await manager.broadcast(message)

        except Exception as e:
            await db.rollback()
            print(f"[ERROR] Failed to publish posts: {e}")

@router.on_event("startup")
async def start_scheduler():
    """Start APScheduler safely on FastAPI startup."""
    if not scheduler.get_jobs():
        scheduler.add_job(
            publish_scheduled_posts,
            'interval',
            minutes=1,
            id="publish_posts_job"
        )
        print("[INFO] Job 'publish_posts_job' added to scheduler")

    if not scheduler.running:
        scheduler.start()
        print("[INFO] Scheduler started: checking for scheduled posts every minute")

@router.websocket("/ws/posts/")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """WebSocket endpoint that uses shared JWT verification."""
    print(f"Extracted token: {token}")
    authorized = await manager.connect(websocket, token)
    if not authorized:
        return  

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("[INFO] Client disconnected from WebSocket.")
