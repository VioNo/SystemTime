from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date, datetime

# Schemas для создания/обновления данных сотрудника
class EmployeeBase(BaseModel):
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    work_email: Optional[EmailStr] = None
    position_title: Optional[int] = None
    department_id: Optional[int] = None
    hire_date: Optional[date] = None
    status_employer: Optional[int] = None

class EmployeeCreate(EmployeeBase):
    keycloak_id: str

class EmployeeUpdate(EmployeeBase):
    pass

class EmployeeResponse(EmployeeBase):
    employee_id: int
    keycloak_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Schemas для регистрации/авторизации
class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int

class RefreshRequest(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    keycloak_id: str
    email: str
    username: str
    is_active: bool
    
    class Config:
        from_attributes = True