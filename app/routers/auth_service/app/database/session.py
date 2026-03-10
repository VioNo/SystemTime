from urllib.parse import quote_plus
import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("AUTH__DB__USER", "auth_user")
DB_PASSWORD = os.getenv("AUTH__DB__PASSWORD", "auth_user_password")
DB_HOST = os.getenv("AUTH__DB__HOST", "postgres")  # внутри Docker это postgres
DB_PORT = os.getenv("AUTH__DB__PORT", "5432")      # внутри Docker 5432
DB_NAME = os.getenv("AUTH__DB__NAME", "system_time_db")

DATABASE_URL = (
    f"postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Создаем engine
engine = create_engine(
    DATABASE_URL,
    echo=DB_ECHO,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Зависимость для получения сессии БД.
    Использование: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_url() -> str:
    """Возвращает URL для подключения к БД (для миграций и т.д.)"""
    return DATABASE_URL


def get_async_db_url() -> str:
    """Возвращает асинхронный URL для подключения к БД"""
    return (
        f"postgresql+asyncpg://{DB_USER}:{quote_plus(DB_PASSWORD)}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )


__all__ = [
    "engine",
    "SessionLocal",
    "get_db",
    "get_db_url",
    "get_async_db_url"
]