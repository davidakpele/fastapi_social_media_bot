from pydantic import BaseModel
from datetime import datetime

class TweetCreate(BaseModel):
    content: str  

class TweetWithMedia(BaseModel):
    content: str
    media_path: str
    
class ScheduleTweetRequest(BaseModel):
    content: str
    scheduled_time: datetime