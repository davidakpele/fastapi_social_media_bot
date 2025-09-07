from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Base for models
Base = declarative_base()

# Create async engine 
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

# Session factory
async_session = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# Dependency for FastAPI routes
async def get_db():
    async with async_session() as session:
        yield session
