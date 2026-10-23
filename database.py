
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pydantic_settings import BaseSettings



class Settings(BaseSettings):
    APP_NAME: str = "Secure Customer AI Chatbot"
    DATABASE_URL: str
    SECRET_KEY: str
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        extra = "ignore"



settings = Settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


class Base(DeclarativeBase):
    pass
