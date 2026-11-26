-- =============================================================================
-- PHASE 4: TRANSACTIONAL INTEGRITY SCRIPTS
-- Database: payroll_attendance_db
-- Demonstrates explicit START TRANSACTION / COMMIT / ROLLBACK for:
--   1. Atomic Salary Revision (closing old revision + inserting new revision)
--   2. Atomic Payroll Processing & Rollback on Mid-Transaction Failure
-- =============================================================================

USE payroll_attendance_db;

DROP PROCEDURE IF EXISTS sp_revise_salary_transactional;

DELIMITER //

-- -----------------------------------------------------------------------------
-- 1. Atomic Salary Revision Procedure
-- Closes the current active salary record and inserts the new revision inside
-- a single ACID transaction. Any constraint/trigger failure triggers ROLLBACK.
-- -----------------------------------------------------------------------------
CREATE PROCEDURE sp_revise_salary_transactional(
    IN p_employee_id      INT,
    IN p_basic_salary     DECIMAL(12,2),
    IN p_hra              DECIMAL(12,2),
    IN p_da               DECIMAL(12,2),
    IN p_other_allowances DECIMAL(12,2),
    IN p_pf_deduction     DECIMAL(12,2),
    IN p_professional_tax DECIMAL(10,2),
    IN p_effective_from   DATE
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

        UPDATE salaries
        SET is_current   = FALSE,
            effective_to = DATE_SUB(p_effective_from, INTERVAL 1 DAY)
        WHERE employee_id = p_employee_id
          AND is_current = TRUE
          AND effective_from < p_effective_from;

        INSERT INTO salaries (
            employee_id, basic_salary, hra, da, other_allowances,
            pf_deduction, professional_tax, effective_from, effective_to, is_current
        ) VALUES (
            p_employee_id, p_basic_salary, p_hra, p_da, p_other_allowances,
            p_pf_deduction, p_professional_tax, p_effective_from, NULL, TRUE
        );

    COMMIT;
END //

DELIMITER ;

-- -----------------------------------------------------------------------------
-- 2. Reference Transaction Pattern for Payroll Batch Disbursement
-- (Executed safely in application/tests with explicit COMMIT or ROLLBACK)
-- -----------------------------------------------------------------------------
-- START TRANSACTION;
-- UPDATE payroll
-- SET payment_status = 'PAID',
--     payment_date   = CURDATE()
-- WHERE pay_year = 2026 AND pay_month = 10 AND payment_status = 'PROCESSED';
-- COMMIT; -- or ROLLBACK on validation failure
