from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.schemas.employee import UserRegister, UserLogin, RefreshRequest, TokenResponse

router = APIRouter(tags=["Authentication"])

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
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
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login", response_model=Dict[str, Any])
async def login(
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
        raise HTTPException(status_code=401, detail=str(e))

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
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/logout")
async def logout(
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