from fastapi import APIRouter, Depends
from app.tasks.scheduler import publish_post_task

router = APIRouter()

@router.post("/schedule")
def schedule_post(account_id: int, content: str, publish_time: str):
    """
    Schedule a post for Instagram/Twitter/TikTok.
    - account_id: linked account
    - content: text/caption
    - publish_time: ISO datetime string
    """
    publish_post_task.apply_async(args=[account_id, content], eta=publish_time)
    return {"status": "scheduled", "account_id": account_id}
