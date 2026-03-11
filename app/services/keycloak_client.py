from keycloak import KeycloakOpenID, KeycloakAdmin
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakPostError
from typing import Dict, Any, Optional

from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import (
    KeycloakConnectionError,
    InvalidCredentialsException,
    InvalidTokenException,
    UserAlreadyExistsException
)

class KeycloakClient:
    def __init__(self):
        self.server_url = settings.KEYCLOAK_URL
        self.realm = settings.KEYCLOAK_REALM
        self.client_id = settings.KEYCLOAK_CLIENT_ID
        self.client_secret = settings.KEYCLOAK_CLIENT_SECRET
        
        # OIDC клиент для аутентификации
        self.oidc = KeycloakOpenID(
            server_url=self.server_url,
            client_id=self.client_id,
            realm_name=self.realm,
            client_secret_key=self.client_secret,
        )
        
        self._admin = None
    
    @property
    def admin(self):
        """Ленивая инициализация админ-клиента"""
        if not self._admin:
            try:
                self._admin = KeycloakAdmin(
                    server_url=self.server_url,
                    realm_name=self.realm,
                    username=settings.KEYCLOAK_ADMIN_USERNAME,
                    password=settings.KEYCLOAK_ADMIN_PASSWORD,
                    verify=True,
                )
            except Exception as e:
                logger.error(f"Failed to connect to Keycloak Admin: {e}")
                raise KeycloakConnectionError("Keycloak Admin connection failed")
        return self._admin
    
    def get_token(self, username: str, password: str) -> Dict[str, Any]:
        """Получение токена"""
        try:
            return self.oidc.token(username, password)
        except KeycloakAuthenticationError as e:
            if e.response_code == 401:
                raise InvalidCredentialsException("Invalid username or password")
            raise KeycloakConnectionError(f"Authentication failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting token: {e}")
            raise KeycloakConnectionError(f"Failed to get token: {e}")
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Обновление токена"""
        try:
            return self.oidc.refresh_token(refresh_token)
        except KeycloakPostError as e:
            if e.response_code == 400:
                raise InvalidTokenException("Invalid refresh token")
            raise KeycloakConnectionError(f"Failed to refresh token: {e}")
        except Exception as e:
            logger.error(f"Unexpected error refreshing token: {e}")
            raise KeycloakConnectionError(f"Failed to refresh token: {e}")
    
    def logout(self, refresh_token: str) -> None:
        """Выход из системы"""
        try:
            self.oidc.logout(refresh_token)
        except KeycloakPostError as e:
            if e.response_code == 400:
                raise InvalidTokenException("Invalid refresh token")
            raise KeycloakConnectionError(f"Logout failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during logout: {e}")
            raise KeycloakConnectionError(f"Logout failed: {e}")
    
    def decode_token(self, token: str, validate: bool = True) -> Dict[str, Any]:
        """Декодирование и валидация токена"""
        try:
            options = {"verify_signature": validate, "verify_aud": validate}
            return self.oidc.decode_token(token, **options)
        except Exception as e:
            logger.error(f"Token decode error: {e}")
            raise InvalidTokenException(f"Invalid token: {str(e)}")
    
    def create_user(self, email: str, username: str, password: str, role: str = "user") -> str:
        """Создание пользователя в Keycloak"""
        try:
            # Проверяем существование
            users_by_email = self.admin.get_users({"email": email})
            if users_by_email:
                raise UserAlreadyExistsException(f"User with email {email} already exists")
            
            users_by_username = self.admin.get_users({"username": username})
            if users_by_username:
                raise UserAlreadyExistsException(f"User with username {username} already exists")
            
            # Создаем пользователя
            user_payload = {
                "email": email,
                "username": username,
                "enabled": True,
                "emailVerified": False,
                "credentials": [{"value": password, "type": "password", "temporary": False}],
            }
            
            user_id = self.admin.create_user(user_payload)
            
            # Назначаем роль
            try:
                realm_role = self.admin.get_realm_role(role)
            except:
                self.admin.create_realm_role({"name": role, "description": f"{role} role"})
                realm_role = self.admin.get_realm_role(role)
            
            self.admin.assign_realm_roles(user_id=user_id, roles=[realm_role])
            
            logger.info(f"User created in Keycloak: {user_id} with role {role}")
            return user_id
            
        except UserAlreadyExistsException:
            raise
        except Exception as e:
            logger.error(f"Failed to create user in Keycloak: {e}")
            raise KeycloakConnectionError(f"Failed to create user: {str(e)}")
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Получение пользователя по email"""
        try:
            users = self.admin.get_users({"email": email})
            return users[0] if users else None
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Получение пользователя по username"""
        try:
            users = self.admin.get_users({"username": username})
            return users[0] if users else None
        except Exception as e:
            logger.error(f"Failed to get user by username {username}: {e}")
            return None

# Синглтон
keycloak_client = KeycloakClient()