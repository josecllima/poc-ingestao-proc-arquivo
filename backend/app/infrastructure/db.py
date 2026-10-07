from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, pool_size=5, max_overflow=5)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def ping() -> None:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))