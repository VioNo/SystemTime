from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List


class SharedJWTConfig(BaseSettings):
    """Общая конфигурация JWT"""
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="SHARED__JWT__",
        case_sensitive=False,
    )

    secret: str
    algorithm: str = "HS256"
    issuer: str
    audience: str
    expire_minutes: int = 5


class KeycloakConfig(BaseSettings):
    """Конфигурация Keycloak"""
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="KEYCLOAK__",
        case_sensitive=False,
    )

    server_url: str
    realm: str


class AuthKeycloakClientConfig(BaseSettings):
    """Конфигурация клиента Keycloak для auth-сервиса"""
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="AUTH__KEYCLOAK__",
        case_sensitive=False,
    )

    client_id: str
    client_secret: Optional[str] = None
    default_role: str = "user"


class AuthServiceConfig(BaseSettings):
    """Основные настройки auth-сервиса"""
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="AUTH__",
        case_sensitive=False,
    )

    debug: bool = True
    service_name: str = "systemtime-auth"
    service_port: int = 8001
    service_host: str = "localhost"


class FrontendConfig(BaseSettings):
    """Конфигурация фронтенда"""
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="FRONTEND__",
        case_sensitive=False,
    )

    urls: str = "http://localhost:3000,http://localhost:3001"

    @property
    def urls_list(self) -> List[str]:
        """Список URL фронтенда для CORS"""
        return [url.strip() for url in self.urls.split(",")]


class Settings(BaseSettings):
    """
    Композитная конфигурация для монолитного auth-сервиса.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Вложенные конфигурации
    jwt: SharedJWTConfig = SharedJWTConfig()
    keycloak: KeycloakConfig = KeycloakConfig()
    auth_keycloak: AuthKeycloakClientConfig = AuthKeycloakClientConfig()
    service: AuthServiceConfig = AuthServiceConfig()
    frontend: FrontendConfig = FrontendConfig()

    @property
    def debug(self) -> bool:
        return self.service.debug

    @property
    def service_name(self) -> str:
        return self.service.service_name

    @property
    def app_name(self) -> str:
        return "SystemTime Auth Service"

    @property
    def frontend_urls(self) -> List[str]:
        """Список URL фронтенда для CORS"""
        return self.frontend.urls_list


# Создаем глобальный экземпляр настроек
settings = Settings()

__all__ = [
    "settings",
    "Settings",
    "KeycloakConfig",
    "AuthKeycloakClientConfig",
    "AuthServiceConfig",
    "FrontendConfig",
    "SharedJWTConfig"
]