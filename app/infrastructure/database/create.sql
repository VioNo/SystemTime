-- Создание базы данных
CREATE DATABASE system_time_db;

-- Подключаемся к созданной БД
\c system_time_db;

-- =========== СПРАВОЧНЫЕ ТАБЛИЦЫ ===========

-- Таблица статусов сотрудников
CREATE TABLE status_employers (
    id SERIAL PRIMARY KEY,
    description TEXT
);

-- Таблица должностей
CREATE TABLE positions (
    id_position SERIAL PRIMARY KEY,
    description TEXT
);

-- Таблица причин
CREATE TABLE causes (
    id SERIAL PRIMARY KEY,
    description TEXT
);

-- =========== ОСНОВНЫЕ ТАБЛИЦЫ ===========

-- Таблица отделов
CREATE TABLE department (
    department_id SERIAL PRIMARY KEY,
    department_name VARCHAR(150),
    department_head_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица сотрудников (с полем keycloak_id)
CREATE TABLE employee (
    employee_id SERIAL PRIMARY KEY,
    keycloak_id VARCHAR(255) UNIQUE,
    last_name VARCHAR(100),
    first_name VARCHAR(100),
    middle_name VARCHAR(100),
    work_email VARCHAR(255) UNIQUE,
    position_title INTEGER REFERENCES positions(id_position),
    department_id INTEGER REFERENCES department(department_id),
    hire_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status_employer INTEGER REFERENCES status_employers(id),
    is_active BOOLEAN DEFAULT TRUE
);

-- Таблица проектов
CREATE TABLE project (
    project_id SERIAL PRIMARY KEY,
    project_code VARCHAR(50) UNIQUE,
    project_name VARCHAR(255),
    description TEXT,
    client_name VARCHAR(255),
    budget_hours DECIMAL(10,2) DEFAULT 0,
    budget_money DECIMAL(15,2) DEFAULT 0,
    start_date DATE,
    planned_end_date DATE,
    actual_end_date DATE,
    status VARCHAR(50) DEFAULT 'planning',
    project_manager_id INTEGER REFERENCES employee(employee_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (start_date <= COALESCE(planned_end_date, start_date))
);

-- Таблица задач
CREATE TABLE task (
    task_id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES project(project_id) ON DELETE CASCADE,
    task_name VARCHAR(255),
    description TEXT,
    planned_hours FLOAT DEFAULT 0,
    creator_id INTEGER REFERENCES employee(employee_id),
    assignee_id INTEGER REFERENCES employee(employee_id),
    status VARCHAR(50) DEFAULT 'created',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    real_hours FLOAT
);

-- Таблица учета времени (Time_Entry)
CREATE TABLE time_entry (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employee(employee_id),
    task_id INTEGER REFERENCES task(task_id),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_minutes INTEGER GENERATED ALWAYS AS (EXTRACT(EPOCH FROM (end_time - start_time)) / 60) STORED,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица табелей (Timesheet)
CREATE TABLE timesheet (
    timesheet_id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employee(employee_id) ON DELETE CASCADE,
    period_start DATE,
    period_end DATE,
    total_reported_hours DECIMAL(10,2) DEFAULT 0,
    approval_status VARCHAR(50) DEFAULT 'draft',
    approver_id INTEGER REFERENCES employee(employee_id),
    approved_at TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(employee_id, period_start, period_end),
    CHECK (period_start <= period_end)
);

-- Таблица аудита
CREATE TABLE audit_log (
    log_id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES employee(employee_id),
    action VARCHAR(100),
    entity_type VARCHAR(50),
    entity_id VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    ip_address VARCHAR(45)
);

-- Таблица документации
CREATE TABLE documentation (
    id SERIAL PRIMARY KEY,
    id_employers_who INTEGER REFERENCES employee(employee_id),
    id_employers_for INTEGER REFERENCES employee(employee_id),
    cause INTEGER REFERENCES causes(id),
    description VARCHAR(10)
);

-- =========== ИНДЕКСЫ ===========

-- Индексы для employee
CREATE INDEX idx_employee_department ON employee(department_id);
CREATE INDEX idx_employee_email ON employee(work_email);
CREATE INDEX idx_employee_keycloak ON employee(keycloak_id);

-- Индексы для project
CREATE INDEX idx_project_code ON project(project_code);
CREATE INDEX idx_project_manager ON project(project_manager_id);
CREATE INDEX idx_project_status ON project(status);
CREATE INDEX idx_project_dates ON project(start_date, planned_end_date);

-- Индексы для task
CREATE INDEX idx_task_project ON task(project_id);
CREATE INDEX idx_task_assignee ON task(assignee_id);
CREATE INDEX idx_task_status ON task(status);

-- Индексы для time_entry
CREATE INDEX idx_time_entry_task ON time_entry(task_id);
CREATE INDEX idx_time_entry_employee ON time_entry(employee_id);
CREATE INDEX idx_time_entry_dates ON time_entry(start_time, end_time);

-- Индексы для timesheet
CREATE INDEX idx_timesheet_employee_period ON timesheet(employee_id, period_start, period_end);
CREATE INDEX idx_timesheet_dates ON timesheet(period_start, period_end);
CREATE INDEX idx_timesheet_approval_status ON timesheet(approval_status);
CREATE INDEX idx_timesheet_approver ON timesheet(approver_id);

-- Индексы для audit_log
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_action ON audit_log(action);
CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);

-- Индексы для department
CREATE INDEX idx_department_head ON department(department_head_id);

-- =========== ПРЕДСТАВЛЕНИЯ ===========

-- Представление для сводной информации по проектам
CREATE VIEW project_summary AS
SELECT
    p.project_id,
    p.project_code,
    p.project_name,
    p.client_name,
    p.status,
    CONCAT(e.last_name, ' ', LEFT(e.first_name, 1), '.') as manager_name,
    COUNT(DISTINCT t.task_id) as task_count,
    COUNT(DISTINCT te.id) as time_entry_count,
    COALESCE(SUM(te.duration_minutes), 0) / 60.0 as total_hours_spent,
    p.budget_hours,
    CASE
        WHEN p.budget_hours > 0
        THEN (COALESCE(SUM(te.duration_minutes), 0) / 60.0 / p.budget_hours * 100)
        ELSE 0
    END as budget_utilization_percent
FROM project p
LEFT JOIN employee e ON p.project_manager_id = e.employee_id
LEFT JOIN task t ON p.project_id = t.project_id
LEFT JOIN time_entry te ON t.task_id = te.task_id
WHERE p.status != 'archived' OR p.status IS NULL
GROUP BY
    p.project_id, p.project_code, p.project_name, p.client_name,
    p.status, e.last_name, e.first_name, p.budget_hours;

-- Представление для отчетов по сотрудникам
CREATE VIEW employee_time_report AS
SELECT
    e.employee_id,
    CONCAT(e.last_name, ' ', e.first_name, ' ', COALESCE(e.middle_name, '')) as full_name,
    e.position_title,
    d.department_name,
    ts.period_start,
    ts.period_end,
    ts.total_reported_hours,
    ts.approval_status,
    COUNT(DISTINCT te.task_id) as tasks_count,
    COUNT(DISTINCT t.project_id) as projects_count
FROM employee e
LEFT JOIN department d ON e.department_id = d.department_id
LEFT JOIN timesheet ts ON e.employee_id = ts.employee_id
LEFT JOIN time_entry te ON e.employee_id = te.employee_id
    AND te.start_time::date BETWEEN ts.period_start AND ts.period_end
LEFT JOIN task t ON te.task_id = t.task_id
WHERE (e.is_active = true OR e.is_active IS NULL)
GROUP BY
    e.employee_id, e.last_name, e.first_name, e.middle_name,
    e.position_title, d.department_name, ts.period_start,
    ts.period_end, ts.total_reported_hours, ts.approval_status;

-- =========== ТРИГГЕРЫ ДЛЯ АВТОМАТИЧЕСКОГО ОБНОВЛЕНИЯ updated_at ===========

-- Функция для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггеры для таблиц с updated_at
CREATE TRIGGER update_project_updated_at
    BEFORE UPDATE ON project
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_task_updated_at
    BEFORE UPDATE ON task
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_time_entry_updated_at
    BEFORE UPDATE ON time_entry
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_timesheet_updated_at
    BEFORE UPDATE ON timesheet
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =========== КОММЕНТАРИИ К ПОЛЯМ ===========

COMMENT ON COLUMN employee.keycloak_id IS 'ID пользователя в Keycloak для аутентификации';
COMMENT ON COLUMN employee.is_active IS 'Флаг активности сотрудника';
COMMENT ON COLUMN task.status IS 'Статус задачи: created, in_progress, clarification, suspended, review, rejected, completed';