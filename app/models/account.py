from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class Platform(str, enum.Enum):
    instagram = "instagram"
    twitter = "twitter"
    tiktok = "tiktok"


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(Enum(Platform), nullable=False) 
    username = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # FK → User
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    # Relationships
    owner = relationship("User", back_populates="accounts")
    posts = relationship("Post", back_populates="account", cascade="all, delete")
