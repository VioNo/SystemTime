from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine
from app.models import Base
from app.api.v1 import auth, employees#, projects, timesheet

# Создание таблиц в БД (только для разработки)
# В продакшене используйте alembic миграции
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Система учета рабочего времени",
    version="1.0.0",
    description="Монолитная система для учета рабочего времени"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_urls,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(employees.router, prefix="/api/v1/employees", tags=["Employees"])
# app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
# app.include_router(timesheet.router, prefix="/api/v1/timesheet", tags=["Timesheet"])

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.service_name,
        "database": "connected"
    }

@app.get("/")
async def root():
    return {
        "message": "SystemTime API",
        "docs": "/docs",
        "version": "1.0.0"
    }