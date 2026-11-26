-- =============================================================================
-- PHASE 2: DATABASE SCHEMA DDL (Implements Approved Phase 1 Schema Unchanged)
-- Database: payroll_attendance_db (MySQL 8.0+, InnoDB, utf8mb4_unicode_ci)
-- =============================================================================

DROP DATABASE IF EXISTS payroll_attendance_db;
CREATE DATABASE payroll_attendance_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE payroll_attendance_db;

-- -----------------------------------------------------------------------------
-- 1. departments
-- -----------------------------------------------------------------------------
CREATE TABLE departments (
    department_id   INT          NOT NULL AUTO_INCREMENT,
    department_code VARCHAR(10)  NOT NULL,
    department_name VARCHAR(100) NOT NULL,
    description     VARCHAR(255) NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_departments PRIMARY KEY (department_id),
    CONSTRAINT uq_dept_code UNIQUE (department_code),
    CONSTRAINT uq_dept_name UNIQUE (department_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 2. employees
-- -----------------------------------------------------------------------------
CREATE TABLE employees (
    employee_id       INT          NOT NULL AUTO_INCREMENT,
    emp_code          VARCHAR(20)  NOT NULL,
    first_name        VARCHAR(50)  NOT NULL,
    last_name         VARCHAR(50)  NOT NULL,
    email             VARCHAR(120) NOT NULL,
    phone             VARCHAR(20)  NOT NULL,
    department_id     INT          NOT NULL,
    designation       VARCHAR(100) NOT NULL,
    hire_date         DATE         NOT NULL,
    employment_status ENUM('ACTIVE', 'ON_LEAVE', 'RESIGNED', 'TERMINATED') NOT NULL DEFAULT 'ACTIVE',
    created_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT pk_employees PRIMARY KEY (employee_id),
    CONSTRAINT uq_emp_code UNIQUE (emp_code),
    CONSTRAINT uq_emp_email UNIQUE (email),
    CONSTRAINT fk_emp_department FOREIGN KEY (department_id)
        REFERENCES departments (department_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 3. user_accounts (RBAC Authentication)
-- -----------------------------------------------------------------------------
CREATE TABLE user_accounts (
    user_id       INT          NOT NULL AUTO_INCREMENT,
    employee_id   INT          NOT NULL,
    username      VARCHAR(50)  NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('HR_ADMIN', 'EMPLOYEE') NOT NULL DEFAULT 'EMPLOYEE',
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    last_login_at DATETIME     NULL,
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT pk_user_accounts PRIMARY KEY (user_id),
    CONSTRAINT uq_user_employee UNIQUE (employee_id),
    CONSTRAINT uq_user_username UNIQUE (username),
    CONSTRAINT fk_user_employee FOREIGN KEY (employee_id)
        REFERENCES employees (employee_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 4. attendance
-- -----------------------------------------------------------------------------
CREATE TABLE attendance (
    attendance_id   INT               NOT NULL AUTO_INCREMENT,
    employee_id     INT               NOT NULL,
    attendance_date DATE              NOT NULL,
    check_in_time   TIME              NULL,
    check_out_time  TIME              NULL,
    status          ENUM('PRESENT', 'ABSENT', 'HALF_DAY', 'ON_LEAVE', 'WORK_FROM_HOME') NOT NULL DEFAULT 'PRESENT',
    is_late         BOOLEAN           NOT NULL DEFAULT FALSE,
    late_minutes    SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    work_hours      DECIMAL(4,2)      NOT NULL DEFAULT 0.00,
    remarks         VARCHAR(255)      NULL,
    created_at      TIMESTAMP         NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT pk_attendance PRIMARY KEY (attendance_id),
    CONSTRAINT uq_attendance_emp_date UNIQUE (employee_id, attendance_date),
    CONSTRAINT fk_attendance_employee FOREIGN KEY (employee_id)
        REFERENCES employees (employee_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT chk_attendance_checkout CHECK (
        check_out_time IS NULL OR check_in_time IS NULL OR check_out_time >= check_in_time
    ),
    CONSTRAINT chk_attendance_work_hours CHECK (work_hours >= 0.00 AND work_hours <= 24.00)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 5. leave_types
-- -----------------------------------------------------------------------------
CREATE TABLE leave_types (
    leave_type_id     INT               NOT NULL AUTO_INCREMENT,
    type_code         VARCHAR(10)       NOT NULL,
    type_name         VARCHAR(50)       NOT NULL,
    is_paid           BOOLEAN           NOT NULL DEFAULT TRUE,
    max_days_per_year SMALLINT UNSIGNED NOT NULL DEFAULT 12,
    description       VARCHAR(255)      NULL,
    CONSTRAINT pk_leave_types PRIMARY KEY (leave_type_id),
    CONSTRAINT uq_leave_type_code UNIQUE (type_code),
    CONSTRAINT uq_leave_type_name UNIQUE (type_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 6. leave_requests
-- -----------------------------------------------------------------------------
CREATE TABLE leave_requests (
    leave_id      INT          NOT NULL AUTO_INCREMENT,
    employee_id   INT          NOT NULL,
    leave_type_id INT          NOT NULL,
    start_date    DATE         NOT NULL,
    end_date      DATE         NOT NULL,
    total_days    DECIMAL(4,1) NOT NULL,
    reason        VARCHAR(255) NOT NULL,
    status        ENUM('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED') NOT NULL DEFAULT 'PENDING',
    approved_by   INT          NULL,
    approved_at   DATETIME     NULL,
    applied_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT pk_leave_requests PRIMARY KEY (leave_id),
    CONSTRAINT fk_leave_employee FOREIGN KEY (employee_id)
        REFERENCES employees (employee_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_leave_type FOREIGN KEY (leave_type_id)
        REFERENCES leave_types (leave_type_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_leave_approver FOREIGN KEY (approved_by)
        REFERENCES employees (employee_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CONSTRAINT chk_leave_dates CHECK (end_date >= start_date),
    CONSTRAINT chk_leave_total_days CHECK (total_days > 0.0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 7. salaries (Preserves Salary Revision History)
-- -----------------------------------------------------------------------------
CREATE TABLE salaries (
    salary_id        INT           NOT NULL AUTO_INCREMENT,
    employee_id      INT           NOT NULL,
    basic_salary     DECIMAL(12,2) NOT NULL,
    hra              DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    da               DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    other_allowances DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    pf_deduction     DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    professional_tax DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    effective_from   DATE          NOT NULL,
    effective_to     DATE          NULL,
    is_current       BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT pk_salaries PRIMARY KEY (salary_id),
    CONSTRAINT uq_salary_emp_effective UNIQUE (employee_id, effective_from),
    CONSTRAINT fk_salary_employee FOREIGN KEY (employee_id)
        REFERENCES employees (employee_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT chk_salary_basic CHECK (basic_salary > 0.00),
    CONSTRAINT chk_salary_nonneg CHECK (
        hra >= 0.00 AND da >= 0.00 AND other_allowances >= 0.00
        AND pf_deduction >= 0.00 AND professional_tax >= 0.00
    ),
    CONSTRAINT chk_salary_dates CHECK (effective_to IS NULL OR effective_to >= effective_from)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- -----------------------------------------------------------------------------
-- 8. payroll (Monthly Payroll Snapshots with Generated Totals)
-- -----------------------------------------------------------------------------
CREATE TABLE payroll (
    payroll_id        INT               NOT NULL AUTO_INCREMENT,
    employee_id       INT               NOT NULL,
    salary_id         INT               NOT NULL,
    pay_month         TINYINT UNSIGNED  NOT NULL,
    pay_year          SMALLINT UNSIGNED NOT NULL,
    working_days      TINYINT UNSIGNED  NOT NULL,
    present_days      DECIMAL(4,1)      NOT NULL DEFAULT 0.0,
    paid_leave_days   DECIMAL(4,1)      NOT NULL DEFAULT 0.0,
    unpaid_leave_days DECIMAL(4,1)      NOT NULL DEFAULT 0.0,
    late_count        SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    basic_earned      DECIMAL(12,2)     NOT NULL,
    allowances_earned DECIMAL(12,2)     NOT NULL DEFAULT 0.00,
    gross_salary      DECIMAL(12,2)     GENERATED ALWAYS AS (basic_earned + allowances_earned) STORED,
    pf_deduction      DECIMAL(12,2)     NOT NULL DEFAULT 0.00,
    professional_tax  DECIMAL(10,2)     NOT NULL DEFAULT 0.00,
    income_tax        DECIMAL(12,2)     NOT NULL DEFAULT 0.00,
    leave_deduction   DECIMAL(12,2)     NOT NULL DEFAULT 0.00,
    total_deductions  DECIMAL(12,2)     GENERATED ALWAYS AS (
        pf_deduction + professional_tax + income_tax + leave_deduction
    ) STORED,
    net_salary        DECIMAL(12,2)     GENERATED ALWAYS AS (
        (basic_earned + allowances_earned) - (pf_deduction + professional_tax + income_tax + leave_deduction)
    ) STORED,
    payment_status    ENUM('DRAFT', 'PROCESSED', 'PAID', 'CANCELLED') NOT NULL DEFAULT 'DRAFT',
    payment_date      DATE              NULL,
    generated_by      INT               NULL,
    generated_at      TIMESTAMP         NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT pk_payroll PRIMARY KEY (payroll_id),
    CONSTRAINT uq_payroll_emp_period UNIQUE (employee_id, pay_year, pay_month),
    CONSTRAINT fk_payroll_employee FOREIGN KEY (employee_id)
        REFERENCES employees (employee_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_payroll_salary FOREIGN KEY (salary_id)
        REFERENCES salaries (salary_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT fk_payroll_generated_by FOREIGN KEY (generated_by)
        REFERENCES employees (employee_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CONSTRAINT chk_payroll_period CHECK (pay_month BETWEEN 1 AND 12 AND pay_year BETWEEN 2000 AND 2100),
    CONSTRAINT chk_payroll_days CHECK (
        working_days BETWEEN 1 AND 31
        AND present_days >= 0.0
        AND paid_leave_days >= 0.0
        AND unpaid_leave_days >= 0.0
    ),
    CONSTRAINT chk_payroll_amounts CHECK (
        basic_earned >= 0.00 AND allowances_earned >= 0.00
        AND pf_deduction >= 0.00 AND professional_tax >= 0.00
        AND income_tax >= 0.00 AND leave_deduction >= 0.00
    ),
    CONSTRAINT chk_payroll_net_nonneg CHECK (
        (basic_earned + allowances_earned) >= (pf_deduction + professional_tax + income_tax + leave_deduction)
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
