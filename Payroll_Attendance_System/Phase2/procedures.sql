-- =============================================================================
-- PHASE 2: STORED PROCEDURES
-- Database: payroll_attendance_db
-- =============================================================================

USE payroll_attendance_db;

DROP PROCEDURE IF EXISTS approve_leave;
DROP PROCEDURE IF EXISTS generate_payroll;
DROP PROCEDURE IF EXISTS process_monthly_payroll;

DELIMITER //

-- -----------------------------------------------------------------------------
-- 1. approve_leave
-- Approves or rejects a PENDING leave request after verifying:
--   - Approver has active HR_ADMIN role
--   - No overlapping APPROVED leave exists for the employee
-- -----------------------------------------------------------------------------
CREATE PROCEDURE approve_leave(
    IN p_leave_id    INT,
    IN p_approver_id INT,
    IN p_decision    VARCHAR(20)
)
BEGIN
    DECLARE v_employee_id   INT;
    DECLARE v_start_date    DATE;
    DECLARE v_end_date      DATE;
    DECLARE v_current_stat  VARCHAR(20);
    DECLARE v_approver_role VARCHAR(20);
    DECLARE v_overlap_count INT DEFAULT 0;

    IF p_decision NOT IN ('APPROVED', 'REJECTED') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Decision must be APPROVED or REJECTED.';
    END IF;

    SELECT role INTO v_approver_role
    FROM user_accounts
    WHERE employee_id = p_approver_id AND is_active = TRUE
    LIMIT 1;

    IF v_approver_role IS NULL OR v_approver_role <> 'HR_ADMIN' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Only an active HR_ADMIN may approve or reject leave requests.';
    END IF;

    SELECT employee_id, start_date, end_date, status
      INTO v_employee_id, v_start_date, v_end_date, v_current_stat
    FROM leave_requests
    WHERE leave_id = p_leave_id;

    IF v_employee_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Leave request not found.';
    END IF;

    IF v_current_stat <> 'PENDING' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Only PENDING leave requests can be processed.';
    END IF;

    IF p_decision = 'APPROVED' THEN
        SELECT COUNT(*) INTO v_overlap_count
        FROM leave_requests
        WHERE employee_id = v_employee_id
          AND leave_id <> p_leave_id
          AND status = 'APPROVED'
          AND start_date <= v_end_date
          AND end_date >= v_start_date;

        IF v_overlap_count > 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Cannot approve: leave dates overlap with an existing approved leave.';
        END IF;
    END IF;

    UPDATE leave_requests
    SET status      = p_decision,
        approved_by = p_approver_id,
        approved_at = NOW()
    WHERE leave_id = p_leave_id;
END //

-- -----------------------------------------------------------------------------
-- 2. generate_payroll
-- Generates one employee's monthly payroll using attendance, leave & salary data.
-- -----------------------------------------------------------------------------
CREATE PROCEDURE generate_payroll(
    IN p_employee_id  INT,
    IN p_pay_month    TINYINT,
    IN p_pay_year     SMALLINT,
    IN p_working_days TINYINT,
    IN p_generated_by INT
)
BEGIN
    DECLARE v_period_start   DATE;
    DECLARE v_period_end     DATE;
    DECLARE v_emp_status     VARCHAR(20);
    DECLARE v_existing_id    INT DEFAULT NULL;

    DECLARE v_salary_id      INT DEFAULT NULL;
    DECLARE v_basic          DECIMAL(12,2) DEFAULT 0.00;
    DECLARE v_hra            DECIMAL(12,2) DEFAULT 0.00;
    DECLARE v_da             DECIMAL(12,2) DEFAULT 0.00;
    DECLARE v_other_allow    DECIMAL(12,2) DEFAULT 0.00;
    DECLARE v_pf             DECIMAL(12,2) DEFAULT 0.00;
    DECLARE v_pt             DECIMAL(10,2) DEFAULT 0.00;

    DECLARE v_present_days   DECIMAL(4,1) DEFAULT 0.0;
    DECLARE v_absent_days    DECIMAL(4,1) DEFAULT 0.0;
    DECLARE v_paid_leaves    DECIMAL(4,1) DEFAULT 0.0;
    DECLARE v_unpaid_leaves  DECIMAL(4,1) DEFAULT 0.0;
    DECLARE v_late_count     SMALLINT UNSIGNED DEFAULT 0;

    DECLARE v_allowances     DECIMAL(12,2) DEFAULT 0.00;
    DECLARE v_full_gross     DECIMAL(12,2) DEFAULT 0.00;
    DECLARE v_unpaid_total   DECIMAL(4,1)  DEFAULT 0.0;
    DECLARE v_leave_deduct   DECIMAL(12,2) DEFAULT 0.00;
    DECLARE v_taxable_gross  DECIMAL(12,2) DEFAULT 0.00;
    DECLARE v_income_tax     DECIMAL(12,2) DEFAULT 0.00;

    IF p_pay_month < 1 OR p_pay_month > 12 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid pay_month; expected 1..12.';
    END IF;

    IF p_working_days < 1 OR p_working_days > 31 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Invalid working_days; expected 1..31.';
    END IF;

    SET v_period_start = STR_TO_DATE(CONCAT(p_pay_year, '-', LPAD(p_pay_month, 2, '0'), '-01'), '%Y-%m-%d');
    SET v_period_end   = LAST_DAY(v_period_start);

    SELECT employment_status INTO v_emp_status
    FROM employees
    WHERE employee_id = p_employee_id;

    IF v_emp_status IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Employee not found.';
    END IF;

    IF v_emp_status NOT IN ('ACTIVE', 'ON_LEAVE') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Payroll can only be generated for ACTIVE or ON_LEAVE employees.';
    END IF;

    SELECT payroll_id INTO v_existing_id
    FROM payroll
    WHERE employee_id = p_employee_id
      AND pay_year = p_pay_year
      AND pay_month = p_pay_month
    LIMIT 1;

    IF v_existing_id IS NOT NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Duplicate payroll generation blocked: payroll already exists for this employee and month.';
    END IF;

    -- Fetch effective salary revision for the target pay period
    SELECT salary_id, basic_salary, hra, da, other_allowances, pf_deduction, professional_tax
      INTO v_salary_id, v_basic, v_hra, v_da, v_other_allow, v_pf, v_pt
    FROM salaries
    WHERE employee_id = p_employee_id
      AND effective_from <= v_period_end
      AND (effective_to IS NULL OR effective_to >= v_period_start)
    ORDER BY effective_from DESC
    LIMIT 1;

    IF v_salary_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'No effective salary structure found for this employee and period.';
    END IF;

    -- Aggregate attendance metrics for the month
    SELECT
        IFNULL(SUM(CASE
            WHEN status IN ('PRESENT', 'WORK_FROM_HOME') THEN 1.0
            WHEN status = 'HALF_DAY' THEN 0.5
            ELSE 0.0
        END), 0.0),
        IFNULL(SUM(CASE WHEN status = 'ABSENT' THEN 1.0 ELSE 0.0 END), 0.0),
        IFNULL(SUM(CASE WHEN is_late = TRUE THEN 1 ELSE 0 END), 0)
    INTO v_present_days, v_absent_days, v_late_count
    FROM attendance
    WHERE employee_id = p_employee_id
      AND attendance_date BETWEEN v_period_start AND v_period_end;

    -- Aggregate approved paid and unpaid leave days overlapping this month
    SELECT
        IFNULL(SUM(CASE
            WHEN lt.is_paid = TRUE THEN
                CASE
                    WHEN lr.start_date >= v_period_start AND lr.end_date <= v_period_end THEN lr.total_days
                    ELSE DATEDIFF(LEAST(lr.end_date, v_period_end), GREATEST(lr.start_date, v_period_start)) + 1
                END
            ELSE 0.0
        END), 0.0),
        IFNULL(SUM(CASE
            WHEN lt.is_paid = FALSE THEN
                CASE
                    WHEN lr.start_date >= v_period_start AND lr.end_date <= v_period_end THEN lr.total_days
                    ELSE DATEDIFF(LEAST(lr.end_date, v_period_end), GREATEST(lr.start_date, v_period_start)) + 1
                END
            ELSE 0.0
        END), 0.0)
    INTO v_paid_leaves, v_unpaid_leaves
    FROM leave_requests lr
    JOIN leave_types lt ON lr.leave_type_id = lt.leave_type_id
    WHERE lr.employee_id = p_employee_id
      AND lr.status = 'APPROVED'
      AND lr.start_date <= v_period_end
      AND lr.end_date >= v_period_start;

    SET v_allowances    = ROUND(v_hra + v_da + v_other_allow, 2);
    SET v_full_gross    = calculate_salary(v_basic, v_hra, v_da, v_other_allow);
    SET v_unpaid_total  = LEAST(v_unpaid_leaves + v_absent_days, p_working_days);
    SET v_leave_deduct  = ROUND((v_full_gross / p_working_days) * v_unpaid_total, 2);
    SET v_taxable_gross = GREATEST(v_full_gross - v_leave_deduct, 0.00);
    SET v_income_tax    = calculate_tax(v_taxable_gross);

    -- Guard against negative net salary on extreme LOP boundary cases
    IF (v_pf + v_pt + v_income_tax + v_leave_deduct) > v_full_gross THEN
        SET v_income_tax = 0.00;
        IF (v_pf + v_pt + v_leave_deduct) > v_full_gross THEN
            SET v_leave_deduct = GREATEST(v_full_gross - v_pf - v_pt, 0.00);
        END IF;
    END IF;

    INSERT INTO payroll (
        employee_id, salary_id, pay_month, pay_year, working_days,
        present_days, paid_leave_days, unpaid_leave_days, late_count,
        basic_earned, allowances_earned, pf_deduction, professional_tax,
        income_tax, leave_deduction, payment_status, payment_date, generated_by
    ) VALUES (
        p_employee_id, v_salary_id, p_pay_month, p_pay_year, p_working_days,
        v_present_days, v_paid_leaves, v_unpaid_total, v_late_count,
        v_basic, v_allowances, v_pf, v_pt,
        v_income_tax, v_leave_deduct, 'PROCESSED', NULL, p_generated_by
    );
END //

-- -----------------------------------------------------------------------------
-- 3. process_monthly_payroll
-- Atomically processes payroll for all eligible ACTIVE/ON_LEAVE employees
-- for a given month/year inside an explicit transaction.
-- -----------------------------------------------------------------------------
CREATE PROCEDURE process_monthly_payroll(
    IN p_pay_month    TINYINT,
    IN p_pay_year     SMALLINT,
    IN p_working_days TINYINT,
    IN p_generated_by INT
)
BEGIN
    DECLARE v_done            BOOLEAN DEFAULT FALSE;
    DECLARE v_emp_id          INT;
    DECLARE v_processed_count INT DEFAULT 0;

    DECLARE emp_cursor CURSOR FOR
        SELECT e.employee_id
        FROM employees e
        WHERE e.employment_status IN ('ACTIVE', 'ON_LEAVE')
          AND EXISTS (
              SELECT 1 FROM salaries s
              WHERE s.employee_id = e.employee_id
                AND s.effective_from <= LAST_DAY(STR_TO_DATE(CONCAT(p_pay_year, '-', LPAD(p_pay_month, 2, '0'), '-01'), '%Y-%m-%d'))
                AND (s.effective_to IS NULL OR s.effective_to >= STR_TO_DATE(CONCAT(p_pay_year, '-', LPAD(p_pay_month, 2, '0'), '-01'), '%Y-%m-%d'))
          )
          AND NOT EXISTS (
              SELECT 1 FROM payroll p
              WHERE p.employee_id = e.employee_id
                AND p.pay_year = p_pay_year
                AND p.pay_month = p_pay_month
          );

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = TRUE;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    OPEN emp_cursor;
    read_loop: LOOP
        FETCH emp_cursor INTO v_emp_id;
        IF v_done THEN
            LEAVE read_loop;
        END IF;

        CALL generate_payroll(v_emp_id, p_pay_month, p_pay_year, p_working_days, p_generated_by);
        SET v_processed_count = v_processed_count + 1;
    END LOOP;
    CLOSE emp_cursor;

    COMMIT;

    SELECT v_processed_count AS processed_employees, p_pay_month AS pay_month, p_pay_year AS pay_year;
END //

DELIMITER ;
