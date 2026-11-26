-- =============================================================================
-- PHASE 2: STORED FUNCTIONS
-- Database: payroll_attendance_db
-- =============================================================================

USE payroll_attendance_db;

DROP FUNCTION IF EXISTS calculate_salary;
DROP FUNCTION IF EXISTS calculate_tax;

DELIMITER //

-- -----------------------------------------------------------------------------
-- 1. calculate_salary
-- Calculates monthly gross salary from basic salary and applicable allowances.
-- Validates non-negative inputs and strictly positive basic salary.
-- -----------------------------------------------------------------------------
CREATE FUNCTION calculate_salary(
    p_basic_salary     DECIMAL(12,2),
    p_hra              DECIMAL(12,2),
    p_da               DECIMAL(12,2),
    p_other_allowances DECIMAL(12,2)
)
RETURNS DECIMAL(12,2)
DETERMINISTIC
BEGIN
    IF p_basic_salary IS NULL OR p_basic_salary <= 0.00 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Basic salary must be strictly greater than zero.';
    END IF;

    IF IFNULL(p_hra, 0.00) < 0.00
       OR IFNULL(p_da, 0.00) < 0.00
       OR IFNULL(p_other_allowances, 0.00) < 0.00 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Salary allowances cannot be negative.';
    END IF;

    RETURN ROUND(
        p_basic_salary
        + IFNULL(p_hra, 0.00)
        + IFNULL(p_da, 0.00)
        + IFNULL(p_other_allowances, 0.00),
        2
    );
END //

-- -----------------------------------------------------------------------------
-- 2. calculate_tax
-- Educational Progressive Annual-Slab Income Tax (Monthly TDS) Model:
--   Annualized Gross = p_monthly_gross * 12
--   Slabs:
--     Up to 300,000             ->  0%
--     300,001 to 600,000        ->  5% on amount above 300,000
--     600,001 to 900,000        -> 15,000 + 10% on amount above 600,000
--     900,001 to 1,200,000      -> 45,000 + 15% on amount above 900,000
--     Above 1,200,000           -> 90,000 + 20% on amount above 1,200,000
--   Returns Monthly TDS = ROUND(annual_tax / 12, 2).
-- -----------------------------------------------------------------------------
CREATE FUNCTION calculate_tax(
    p_monthly_gross DECIMAL(12,2)
)
RETURNS DECIMAL(12,2)
DETERMINISTIC
BEGIN
    DECLARE v_annual_gross DECIMAL(14,2);
    DECLARE v_annual_tax   DECIMAL(14,2) DEFAULT 0.00;

    IF p_monthly_gross IS NULL OR p_monthly_gross <= 0.00 THEN
        RETURN 0.00;
    END IF;

    SET v_annual_gross = p_monthly_gross * 12.00;

    IF v_annual_gross <= 300000.00 THEN
        SET v_annual_tax = 0.00;
    ELSEIF v_annual_gross <= 600000.00 THEN
        SET v_annual_tax = (v_annual_gross - 300000.00) * 0.05;
    ELSEIF v_annual_gross <= 900000.00 THEN
        SET v_annual_tax = 15000.00 + ((v_annual_gross - 600000.00) * 0.10);
    ELSEIF v_annual_gross <= 1200000.00 THEN
        SET v_annual_tax = 45000.00 + ((v_annual_gross - 900000.00) * 0.15);
    ELSE
        SET v_annual_tax = 90000.00 + ((v_annual_gross - 1200000.00) * 0.20);
    END IF;

    RETURN ROUND(v_annual_tax / 12.00, 2);
END //

DELIMITER ;
