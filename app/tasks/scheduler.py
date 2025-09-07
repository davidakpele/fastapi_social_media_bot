from celery import Celery

celery = Celery(__name__, broker="redis://redis:6379/0")

@celery.task
def publish_post_task(account_id: int, content: str):
    """
    Called by Celery at scheduled time.
    Delegates to Instagram/Twitter/TikTok service.
    """
    # Load account from DB (pseudo-code)
    # account = db.get_account(account_id)
    # if account.platform == "instagram":
    #     instagram_service.publish(account, content)
    # elif account.platform == "twitter":
    #     twitter_service.publish(account, content)
    # elif account.platform == "tiktok":
    #     tiktok_service.publish(account, content)
    return {"status": "posted", "account_id": account_id}
