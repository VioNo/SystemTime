from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings

# Синхронный engine (для миграций и простых операций)
engine = create_engine(
    settings.database_url,
    echo=settings.DEBUG,
    pool_size=5,
    max_overflow=10
)

# Фабрика сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Базовый класс для моделей
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Зависимость для получения сессии БД
    Использование: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()