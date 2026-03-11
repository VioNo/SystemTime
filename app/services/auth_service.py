from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from app.models.employee import Employee
from app.schemas.employee import UserRegister, UserLogin
from app.services.keycloak_client import keycloak_client
from app.core.exceptions import (
    UserAlreadyExistsException,
    InvalidCredentialsException,
    DatabaseException
)
from app.core.logger import logger

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.kc = keycloak_client
    
    async def register(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Регистрация пользователя:
        1. Создание в Keycloak
        2. Сохранение keycloak_id в БД
        """
        try:
            user_register = UserRegister(**user_data)
        except Exception as e:
            raise ValueError(f"Invalid registration data: {str(e)}")
        
        # Проверяем, нет ли уже такого пользователя в БД
        existing_user = self.db.query(Employee).filter(
            Employee.work_email == user_register.email
        ).first()
        
        if existing_user:
            raise UserAlreadyExistsException(f"User with email {user_register.email} already exists")
        
        try:
            # Создаем пользователя в Keycloak
            keycloak_id = self.kc.create_user(
                email=user_register.email,
                username=user_register.username,
                password=user_register.password,
                role="user"
            )
            
            # Сохраняем только keycloak_id в БД
            employee = Employee(
                keycloak_id=keycloak_id,
                work_email=user_register.email,
                is_active=True
            )
            
            self.db.add(employee)
            self.db.commit()
            self.db.refresh(employee)
            
            logger.info(f"User registered: {user_register.email} with keycloak_id: {keycloak_id}")
            
            # Получаем токен для автоматического входа
            token_response = self.kc.get_token(
                username=user_register.username,
                password=user_register.password
            )
            
            return {
                "status": "success",
                "message": "User registered successfully",
                "keycloak_id": keycloak_id,
                "employee_id": employee.employee_id,
                "tokens": token_response
            }
            
        except UserAlreadyExistsException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Registration failed: {e}")
            raise DatabaseException(f"Registration failed: {str(e)}")
    
    async def login(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Вход пользователя:
        1. Проверка credentials в Keycloak
        2. Получение токена
        3. Проверка существования пользователя в БД
        """
        try:
            user_login = UserLogin(**credentials)
        except Exception as e:
            raise ValueError(f"Invalid login data: {str(e)}")
        
        try:
            # Получаем токен от Keycloak
            token_response = self.kc.get_token(
                username=user_login.username,
                password=user_login.password
            )
            
            # Декодируем токен, чтобы получить keycloak_id
            token_info = self.kc.decode_token(token_response["access_token"], validate=True)
            keycloak_id = token_info.get("sub")
            
            # Проверяем, существует ли пользователь в БД
            employee = self.db.query(Employee).filter(
                Employee.keycloak_id == keycloak_id
            ).first()
            
            if not employee:
                # Если пользователь есть в Keycloak, но нет в БД - создаем запись
                logger.warning(f"User {keycloak_id} exists in Keycloak but not in DB - creating record")
                employee = Employee(
                    keycloak_id=keycloak_id,
                    work_email=token_info.get("email"),
                    is_active=True
                )
                self.db.add(employee)
                self.db.commit()
            
            return {
                **token_response,
                "user": {
                    "keycloak_id": keycloak_id,
                    "employee_id": employee.employee_id,
                    "email": employee.work_email,
                    "is_active": employee.is_active,
                    "profile_complete": all([
                        employee.last_name,
                        employee.first_name,
                        employee.position_title
                    ])
                }
            }
            
        except InvalidCredentialsException:
            raise
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise
    
    async def refresh_token(self, refresh_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновление токена"""
        refresh_token = refresh_data.get("refresh_token")
        if not refresh_token:
            raise ValueError("Refresh token required")
        
        return self.kc.refresh_token(refresh_token)
    
    async def logout(self, refresh_token: str) -> Dict[str, Any]:
        """Выход из системы"""
        if not refresh_token:
            raise ValueError("Refresh token required")
        
        self.kc.logout(refresh_token)
        return {"message": "Successfully logged out"}
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Валидация токена"""
        try:
            payload = self.kc.decode_token(token, validate=True)
            return {"valid": True, "payload": payload}
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def get_user_by_keycloak_id(self, keycloak_id: str) -> Optional[Employee]:
        """Получение пользователя из БД по keycloak_id"""
        return self.db.query(Employee).filter(
            Employee.keycloak_id == keycloak_id
        ).first()