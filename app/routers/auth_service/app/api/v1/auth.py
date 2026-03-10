from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict, Any

from . import schemas
from .auth_service import AuthService
from .keycloak_client import KeycloakClient
from .database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Конфигурация Keycloak (возьмите из переменных окружения)
KEYCLOAK_CONFIG = {
    "server_url": "http://localhost:8080/",
    "realm": "your-realm",
    "client_id": "your-client",
    "client_secret": "your-client-secret"
}

# Инициализация клиента (лучше сделать синглтоном)
kc_client = KeycloakClient(**KEYCLOAK_CONFIG)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db, kc_client)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
        request: Request,
        service: AuthService = Depends(get_auth_service)
):
    """Регистрация нового пользователя"""
    try:
        user_data = await request.json()
        result = await service.register(user_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login")
async def login_user(
        request: Request,
        service: AuthService = Depends(get_auth_service)
):
    """Аутентификация пользователя"""
    try:
        credentials = await request.json()
        result = await service.login(credentials)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.post("/refresh")
async def refresh_token(
        request: Request,
        service: AuthService = Depends(get_auth_service)
):
    """Обновление токена"""
    try:
        refresh_data = await request.json()
        result = await service.refresh_token(refresh_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=401, detail="Token refresh failed")


@router.post("/logout")
async def logout_user(
        request: Request,
        service: AuthService = Depends(get_auth_service)
):
    """Выход из системы"""
    try:
        body = await request.json()
        refresh_token = body.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Refresh token required")

        result = await service.logout(refresh_token)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/validate")
async def validate_token(
        request: Request,
        service: AuthService = Depends(get_auth_service)
):
    """Валидация токена"""
    try:
        body = await request.json()
        token = body.get("token")
        if not token:
            raise HTTPException(status_code=400, detail="Token required")

        result = await service.validate_token(token)
        return result
    except Exception as e:
        return {"valid": False, "error": str(e)}