from datetime import datetime, timezone
from app.models.account import Account, Platform
from app.models.post import Post
from app.payloads.account_create import AccountCreate
from app.payloads.create_twitter import ScheduleTweetRequest, TweetCreate, TweetWithMedia
from app.payloads.register_request import RegisterRequest
from app.routers.dependencies import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.user import User
from fastapi.templating import Jinja2Templates
from typing import List
import tweepy
from app.config import settings
from typing import Dict
import secrets
from fastapi.responses import RedirectResponse

router = APIRouter()

# -----------------------------
# Simulated Twitter Authorization
# -----------------------------
demo_request_tokens: dict[int, str] = {}
APP_DOMAIN = settings.DOMAIN_URL

@router.get("/authorize")
async def twitter_authorize(current_user: int = Depends(get_current_user)):
    demo_token = secrets.token_urlsafe(32)
    demo_request_tokens[current_user] = demo_token

    callback_url = f"{APP_DOMAIN}/accounts/callback?token={demo_token}"
    return RedirectResponse(callback_url)


@router.get("/callback")
async def twitter_callback(token: str, current_user: int = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Account).filter(Account.user_id == current_user, Account.platform == Platform.twitter)
    )
    existing_account = result.scalars().first()
    if existing_account:
        return {"msg": "Twitter account already linked", "account_id": existing_account.id}

    fake_username = f"demo_user_{current_user}"
    new_account = Account(
        platform=Platform.twitter,
        username=fake_username,
        access_token=secrets.token_urlsafe(32),
        refresh_token=secrets.token_urlsafe(32),
        user_id=current_user
    )
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)

    # Remove token after use
    demo_request_tokens.pop(current_user, None)

    return {"msg": "Twitter account linked successfully", "account_id": new_account.id}

# -----------------------------
# Fetch User Info
# -----------------------------
@router.get("/me")
async def twitter_me(db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    result = await db.execute(select(Account).filter(Account.user_id == current_user))
    accounts = result.scalars().all()

    if not accounts:
        raise HTTPException(status_code=200, detail="No accounts linked")

    return [
        {
            "username": acc.username,
            "platform": acc.platform.value if hasattr(acc.platform, "value") else acc.platform,
            "name": "Demo User",
            "followers_count": 100,
            "following_count": 50
        }
        for acc in accounts
    ]


@router.delete("/{platform}/{username}")
async def delete_account_by_platform(
    platform: str,
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: int = Depends(get_current_user) 
):
    result = await db.execute(
        select(Account).filter(
            Account.user_id == current_user, 
            Account.platform == platform.lower(),
            Account.username == username
        )
    )
    account = result.scalars().first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    await db.delete(account)
    await db.commit()
    
    return {"msg": f"Account '{username}' on {platform} disconnected successfully"}

# -----------------------------
# Fetch Followers / Following
# -----------------------------
@router.get("/followers")
async def twitter_followers(db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    followers = [{"username": f"follower_{i}", "name": f"Follower {i}"} for i in range(1, 6)]
    return followers

@router.get("/following")
async def twitter_following(db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    following = [{"username": f"following_{i}", "name": f"Following {i}"} for i in range(1, 6)]
    return following

# -----------------------------
# User Timeline / Posts
# -----------------------------
@router.get("/tweets")
async def get_user_tweets(count: int = 5, db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    result = await db.execute(select(Post).filter(Post.user_id == current_user).order_by(Post.created_at.desc()))
    posts = result.scalars().all()
    return [
        {"id": p.id, "text": p.content, "created_at": p.created_at, "status": p.status}
        for p in posts[:count]
    ]

# -----------------------------
# Post Tweet (Offline / DB)
# -----------------------------
@router.post("/tweets")
async def create_tweet(content: TweetCreate, db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    result = await db.execute(
        select(Account).filter(Account.user_id == current_user)
    )
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="No linked account found")
    new_post = Post(
        content=content.content,
        status="published",
        published_time=datetime.utcnow(),
        user_id=current_user,
        account_id=account.id
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)

    return {
        "msg": f"Post published successfully on {account.platform.value.capitalize()} (offline demo)",
        "post_id": new_post.id
    }


# -----------------------------
# Schedule Tweet
# -----------------------------
@router.post("/schedule")
async def schedule_post(
    request: ScheduleTweetRequest,
    db: AsyncSession = Depends(get_db),
    current_user: int = Depends(get_current_user)
):
    result = await db.execute(
        select(Account).filter(Account.user_id == current_user)
    )
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="No linked account found")

    now = datetime.now(timezone.utc)
    if request.scheduled_time <= now:
        raise HTTPException(status_code=400, detail="scheduled_time must be in the future")

    new_post = Post(
        content=request.content,
        scheduled_time=request.scheduled_time,
        status="scheduled",
        user_id=current_user,
        account_id=account.id
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)

    print(f"[INFO] {now.isoformat()} - Scheduled post id={new_post.id} for user_id={current_user} on {account.platform.value} at {request.scheduled_time.isoformat()}")

    return {
        "msg": f"Post scheduled successfully on {account.platform.value.capitalize()} (offline demo)",
        "post_id": new_post.id,
        "scheduled_time": new_post.scheduled_time
    }


@router.post("/add-platform", response_model=dict)
async def add_platform_account(
    data: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: int = Depends(get_current_user), 
):

    result = await db.execute(
        select(Account)
        .filter(Account.user_id == current_user)
        .filter(Account.platform == data.platform)
        .filter(Account.username == data.username)
    )
    existing_account = result.scalars().first()
    if existing_account:
        raise HTTPException(
            status_code=400,
            detail=f"Account with username '{data.username}' on platform '{data.platform.value}' already exists for this user."
        )

    new_account = Account(
        platform=data.platform,
        username=data.username,
        user_id=current_user
    )
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)
    return {"msg": "Account linked successfully", "account_id": new_account.id}
