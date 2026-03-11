from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.employee import Employee
from app.schemas.employee import EmployeeResponse, EmployeeUpdate, EmployeeCreate
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user

router = APIRouter(tags=["Employees"])

@router.get("/me", response_model=EmployeeResponse)
async def get_current_employee(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение данных текущего сотрудника"""
    keycloak_id = current_user.get("sub")
    employee = db.query(Employee).filter(Employee.keycloak_id == keycloak_id).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return employee

@router.put("/me", response_model=EmployeeResponse)
async def update_current_employee(
    employee_data: EmployeeUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление данных текущего сотрудника"""
    keycloak_id = current_user.get("sub")
    employee = db.query(Employee).filter(Employee.keycloak_id == keycloak_id).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Обновляем только переданные поля
    for field, value in employee_data.dict(exclude_unset=True).items():
        setattr(employee, field, value)
    
    db.commit()
    db.refresh(employee)
    
    return employee

@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получение данных сотрудника по ID"""
    employee = db.query(Employee).filter(Employee.employee_id == employee_id).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return employee

@router.get("/", response_model=List[EmployeeResponse])
async def get_employees(
    skip: int = 0,
    limit: int = 100,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получение списка сотрудников с фильтрацией"""
    query = db.query(Employee)
    
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    
    employees = query.offset(skip).limit(limit).all()
    return employees