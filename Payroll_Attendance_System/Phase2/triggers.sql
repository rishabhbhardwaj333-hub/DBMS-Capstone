-- =============================================================================
-- PHASE 2: DATABASE TRIGGERS
-- Database: payroll_attendance_db
-- =============================================================================

USE payroll_attendance_db;

DROP TRIGGER IF EXISTS trg_leave_before_insert;
DROP TRIGGER IF EXISTS trg_leave_before_update;
DROP TRIGGER IF EXISTS trg_attendance_before_insert;
DROP TRIGGER IF EXISTS trg_attendance_before_update;
DROP TRIGGER IF EXISTS trg_salary_before_insert;
DROP TRIGGER IF EXISTS trg_salary_before_update;
DROP TRIGGER IF EXISTS trg_payroll_before_insert;

DELIMITER //

-- -----------------------------------------------------------------------------
-- 1. Leave Validation Triggers (Before Insert & Before Update)
--    - Enforces valid date range & hire_date boundary
--    - Prevents overlapping APPROVED leave periods for the same employee
-- -----------------------------------------------------------------------------
CREATE TRIGGER trg_leave_before_insert
BEFORE INSERT ON leave_requests
FOR EACH ROW
BEGIN
    DECLARE v_hire_date DATE;
    DECLARE v_overlap_count INT DEFAULT 0;

    SELECT hire_date INTO v_hire_date
    FROM employees
    WHERE employee_id = NEW.employee_id;

    IF v_hire_date IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid employee_id for leave request.';
    END IF;

    IF NEW.end_date < NEW.start_date THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Leave end_date cannot be earlier than start_date.';
    END IF;

    IF NEW.total_days <= 0.0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Leave total_days must be greater than zero.';
    END IF;

    IF NEW.total_days > (DATEDIFF(NEW.end_date, NEW.start_date) + 1) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Leave total_days cannot exceed the calendar span between start_date and end_date.';
    END IF;

    IF NEW.start_date < v_hire_date THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Leave start_date cannot precede the employee hire_date.';
    END IF;

    IF NEW.status = 'APPROVED' THEN
        SELECT COUNT(*) INTO v_overlap_count
        FROM leave_requests
        WHERE employee_id = NEW.employee_id
          AND status = 'APPROVED'
          AND start_date <= NEW.end_date
          AND end_date >= NEW.start_date;

        IF v_overlap_count > 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Overlapping approved leave dates are not allowed for this employee.';
        END IF;
    END IF;
END //

CREATE TRIGGER trg_leave_before_update
BEFORE UPDATE ON leave_requests
FOR EACH ROW
BEGIN
    DECLARE v_hire_date DATE;
    DECLARE v_overlap_count INT DEFAULT 0;

    SELECT hire_date INTO v_hire_date
    FROM employees
    WHERE employee_id = NEW.employee_id;

    IF NEW.end_date < NEW.start_date THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Leave end_date cannot be earlier than start_date.';
    END IF;

    IF NEW.total_days <= 0.0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Leave total_days must be greater than zero.';
    END IF;

    IF NEW.total_days > (DATEDIFF(NEW.end_date, NEW.start_date) + 1) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Leave total_days cannot exceed the calendar span between start_date and end_date.';
    END IF;

    IF NEW.start_date < v_hire_date THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Leave start_date cannot precede the employee hire_date.';
    END IF;

    IF NEW.status = 'APPROVED' THEN
        SELECT COUNT(*) INTO v_overlap_count
        FROM leave_requests
        WHERE employee_id = NEW.employee_id
          AND leave_id <> OLD.leave_id
          AND status = 'APPROVED'
          AND start_date <= NEW.end_date
          AND end_date >= NEW.start_date;

        IF v_overlap_count > 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Overlapping approved leave dates are not allowed for this employee.';
        END IF;
    END IF;
END //

-- -----------------------------------------------------------------------------
-- 2. Attendance Validation & Auto-Calculation Triggers
--    - Enforces attendance_date between hire_date and CURDATE()
--    - Rejects working status on approved leave dates
--    - Auto-computes is_late, late_minutes (shift start 09:30:00) & work_hours
-- -----------------------------------------------------------------------------
CREATE TRIGGER trg_attendance_before_insert
BEFORE INSERT ON attendance
FOR EACH ROW
BEGIN
    DECLARE v_hire_date DATE;
    DECLARE v_approved_leave_count INT DEFAULT 0;

    SELECT hire_date INTO v_hire_date
    FROM employees
    WHERE employee_id = NEW.employee_id;

    IF v_hire_date IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid employee_id for attendance record.';
    END IF;

    IF NEW.attendance_date < v_hire_date THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Attendance date cannot precede employee hire_date.';
    END IF;

    IF NEW.attendance_date > CURDATE() THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Attendance date cannot be in the future.';
    END IF;

    IF NEW.status IN ('PRESENT', 'HALF_DAY', 'WORK_FROM_HOME') THEN
        SELECT COUNT(*) INTO v_approved_leave_count
        FROM leave_requests
        WHERE employee_id = NEW.employee_id
          AND status = 'APPROVED'
          AND NEW.attendance_date BETWEEN start_date AND end_date;

        IF v_approved_leave_count > 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Cannot mark working attendance on an approved leave date.';
        END IF;

        IF NEW.check_in_time IS NOT NULL AND NEW.check_out_time IS NOT NULL
           AND NEW.check_out_time < NEW.check_in_time THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'check_out_time cannot be earlier than check_in_time.';
        END IF;

        IF NEW.status = 'PRESENT' AND NEW.check_in_time IS NOT NULL AND NEW.check_in_time > '09:30:00' THEN
            SET NEW.is_late = TRUE;
            SET NEW.late_minutes = TIMESTAMPDIFF(MINUTE, '09:30:00', NEW.check_in_time);
        ELSE
            SET NEW.is_late = FALSE;
            SET NEW.late_minutes = 0;
        END IF;

        IF NEW.check_in_time IS NOT NULL AND NEW.check_out_time IS NOT NULL THEN
            SET NEW.work_hours = ROUND(TIMESTAMPDIFF(MINUTE, NEW.check_in_time, NEW.check_out_time) / 60.0, 2);
        END IF;
    ELSE
        -- ABSENT or ON_LEAVE: normalize timing & late attributes
        SET NEW.check_in_time = NULL;
        SET NEW.check_out_time = NULL;
        SET NEW.is_late = FALSE;
        SET NEW.late_minutes = 0;
        SET NEW.work_hours = 0.00;
    END IF;
END //

CREATE TRIGGER trg_attendance_before_update
BEFORE UPDATE ON attendance
FOR EACH ROW
BEGIN
    DECLARE v_hire_date DATE;
    DECLARE v_approved_leave_count INT DEFAULT 0;

    SELECT hire_date INTO v_hire_date
    FROM employees
    WHERE employee_id = NEW.employee_id;

    IF NEW.attendance_date < v_hire_date THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Attendance date cannot precede employee hire_date.';
    END IF;

    IF NEW.attendance_date > CURDATE() THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Attendance date cannot be in the future.';
    END IF;

    IF NEW.status IN ('PRESENT', 'HALF_DAY', 'WORK_FROM_HOME') THEN
        SELECT COUNT(*) INTO v_approved_leave_count
        FROM leave_requests
        WHERE employee_id = NEW.employee_id
          AND status = 'APPROVED'
          AND NEW.attendance_date BETWEEN start_date AND end_date;

        IF v_approved_leave_count > 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Cannot mark working attendance on an approved leave date.';
        END IF;

        IF NEW.check_in_time IS NOT NULL AND NEW.check_out_time IS NOT NULL
           AND NEW.check_out_time < NEW.check_in_time THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'check_out_time cannot be earlier than check_in_time.';
        END IF;

        IF NEW.status = 'PRESENT' AND NEW.check_in_time IS NOT NULL AND NEW.check_in_time > '09:30:00' THEN
            SET NEW.is_late = TRUE;
            SET NEW.late_minutes = TIMESTAMPDIFF(MINUTE, '09:30:00', NEW.check_in_time);
        ELSE
            SET NEW.is_late = FALSE;
            SET NEW.late_minutes = 0;
        END IF;

        IF NEW.check_in_time IS NOT NULL AND NEW.check_out_time IS NOT NULL THEN
            SET NEW.work_hours = ROUND(TIMESTAMPDIFF(MINUTE, NEW.check_in_time, NEW.check_out_time) / 60.0, 2);
        END IF;
    ELSE
        SET NEW.check_in_time = NULL;
        SET NEW.check_out_time = NULL;
        SET NEW.is_late = FALSE;
        SET NEW.late_minutes = 0;
        SET NEW.work_hours = 0.00;
    END IF;
END //

-- -----------------------------------------------------------------------------
-- 3. Salary Validation Triggers
-- -----------------------------------------------------------------------------
CREATE TRIGGER trg_salary_before_insert
BEFORE INSERT ON salaries
FOR EACH ROW
BEGIN
    IF NEW.basic_salary <= 0.00 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Basic salary must be strictly positive (> 0).';
    END IF;

    IF NEW.hra < 0.00 OR NEW.da < 0.00 OR NEW.other_allowances < 0.00
       OR NEW.pf_deduction < 0.00 OR NEW.professional_tax < 0.00 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Salary allowances and statutory deductions cannot be negative.';
    END IF;

    IF NEW.effective_to IS NOT NULL AND NEW.effective_to < NEW.effective_from THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Salary effective_to cannot precede effective_from.';
    END IF;
END //

CREATE TRIGGER trg_salary_before_update
BEFORE UPDATE ON salaries
FOR EACH ROW
BEGIN
    IF NEW.basic_salary <= 0.00 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Basic salary must be strictly positive (> 0).';
    END IF;

    IF NEW.hra < 0.00 OR NEW.da < 0.00 OR NEW.other_allowances < 0.00
       OR NEW.pf_deduction < 0.00 OR NEW.professional_tax < 0.00 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Salary allowances and statutory deductions cannot be negative.';
    END IF;

    IF NEW.effective_to IS NOT NULL AND NEW.effective_to < NEW.effective_from THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Salary effective_to cannot precede effective_from.';
    END IF;
END //

-- -----------------------------------------------------------------------------
-- 4. Payroll Validation Trigger
-- -----------------------------------------------------------------------------
CREATE TRIGGER trg_payroll_before_insert
BEFORE INSERT ON payroll
FOR EACH ROW
BEGIN
    IF NEW.pay_month < 1 OR NEW.pay_month > 12 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'pay_month must be between 1 and 12.';
    END IF;

    IF (NEW.basic_earned + NEW.allowances_earned) <
       (NEW.pf_deduction + NEW.professional_tax + NEW.income_tax + NEW.leave_deduction) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Total deductions cannot exceed gross salary.';
    END IF;
END //

DELIMITER ;
