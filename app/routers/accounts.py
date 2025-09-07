from app.models.account import Account, Platform
from app.payloads.account_create import AccountCreate
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



TWITTER_API_KEY = settings.TWITTER_API_KEY
TWITTER_API_SECRET = settings.TWITTER_API_SECRET
TWITTER_CALLBACK_URL = "https://fastapi-social-media-bot-1.onrender.com"

router = APIRouter()

# Temporary in-memory storage for request tokens (for local testing)
request_tokens: Dict[int, dict] = {}


@router.get("/authorize")
async def twitter_authorize(current_user: int = Depends(get_current_user)):
    """
    Step 1: Redirect user to Twitter for authorization.
    """
    auth = tweepy.OAuth1UserHandler(
        TWITTER_API_KEY,
        TWITTER_API_SECRET,
        TWITTER_CALLBACK_URL
    )
    redirect_url = auth.get_authorization_url()

    # Save the request token in memory
    request_tokens[current_user] = auth.request_token

    # Return the URL so frontend can redirect user
    return {"auth_url": redirect_url}


@router.get("/callback")
async def twitter_callback(
    oauth_token: str,
    oauth_verifier: str,
    db: AsyncSession = Depends(get_db),
    current_user: int = Depends(get_current_user),
):
    """
    Step 2: Handle callback from Twitter and save account.
    """
    # Check if the request token exists
    if current_user not in request_tokens:
        raise HTTPException(status_code=400, detail="Request token missing or expired")

    auth = tweepy.OAuth1UserHandler(
        TWITTER_API_KEY,
        TWITTER_API_SECRET,
        TWITTER_CALLBACK_URL
    )
    # Retrieve and remove the original request token
    auth.request_token = request_tokens.pop(current_user)

    # Exchange oauth_verifier for access token
    try:
        access_token, access_token_secret = auth.get_access_token(oauth_verifier)
    except tweepy.TweepyException as e:
        raise HTTPException(status_code=400, detail=f"Twitter OAuth error: {str(e)}")

    # Fetch Twitter account info
    api = tweepy.API(auth)
    twitter_user = api.verify_credentials()
    username = twitter_user.screen_name

    # Save to database
    new_account = Account(
        platform=Platform.twitter,
        username=username,
        access_token=access_token,
        access_token_secret=access_token_secret,
        user_id=current_user
    )
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)

    return {"msg": "Twitter account linked successfully", "account_id": new_account.id}

@router.post("/", response_model=dict)
async def create_account(
    data: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: int = Depends(get_current_user), 
):
    # Check if account already exists for this user with same platform and username
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

    # Create new account
    new_account = Account(
        platform=data.platform,
        username=data.username,
        user_id=current_user
    )
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)
    return {"msg": "Account linked successfully", "account_id": new_account.id}


@router.get("/", response_model=List[dict])
async def get_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: int = Depends(get_current_user),  # user_id
):
    result = await db.execute(
        select(Account).filter(Account.user_id == current_user)
    )
    accounts = result.scalars().all()
    
    return [
        {
            "id": acc.id,
            "platform": acc.platform,
            "username": acc.username,
            "created_at": acc.created_at
        }
        for acc in accounts
    ]


@router.delete("/{account_id}")
async def delete_account(account_id: int, 
                         db: AsyncSession = Depends(get_db), 
                         current_user=Depends(get_current_user)):
    result = await db.execute(
        select(Account).filter(Account.id == account_id, Account.user_id == current_user.id)
    )
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    await db.delete(account)
    await db.commit()
    return {"msg": "Account disconnected successfully"}