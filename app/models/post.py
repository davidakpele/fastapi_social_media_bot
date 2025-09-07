from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    media_url = Column(String, nullable=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=True)
    published_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="scheduled")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # FK → User & Account
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"))

    # Relationships
    owner = relationship("User", back_populates="posts")
    account = relationship("Account", back_populates="posts")
