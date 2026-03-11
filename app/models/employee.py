from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base

class Employee(Base):
    __tablename__ = "employee"
    
    employee_id = Column(Integer, primary_key=True, autoincrement=True)
    keycloak_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Основные данные (заполняются отдельно)
    last_name = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    middle_name = Column(String(100), nullable=True)
    work_email = Column(String(255), unique=True, nullable=True)
    position_title = Column(Integer, ForeignKey("positions.id_position"), nullable=True)
    department_id = Column(Integer, ForeignKey("department.department_id"), nullable=True)
    hire_date = Column(Date, nullable=True)
    status_employer = Column(Integer, ForeignKey("status_employers.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    department = relationship("Department", back_populates="employees")
    position = relationship("Position", back_populates="employees")
    status = relationship("StatusEmployer", back_populates="employees")
    
    # Проекты, где сотрудник менеджер
    managed_projects = relationship("Project", back_populates="manager")
    
    # Задачи
    created_tasks = relationship("Task", foreign_keys="Task.creator_id", back_populates="creator")
    assigned_tasks = relationship("Task", foreign_keys="Task.assignee_id", back_populates="assignee")
    
    # Учет времени
    time_entries = relationship("TimeEntry", back_populates="employee")
    timesheets = relationship("Timesheet", back_populates="employee")
    
    def __repr__(self):
        return f"<Employee(keycloak_id={self.keycloak_id})>"