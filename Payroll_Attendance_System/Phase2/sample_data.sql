-- =============================================================================
-- PHASE 2: REALISTIC SAMPLE DATA
-- Database: payroll_attendance_db
-- Covers:
--   - 5 IT Firm Departments
--   - 12 Employees (2 HR_ADMIN + 10 EMPLOYEE)
--   - 12 User Accounts (real Werkzeug scrypt password hashes)
--   - 4 Leave Types & multiple Leave Requests (APPROVED, PENDING, REJECTED)
--   - 14 Salary Records (preserving revision history for 2 employees)
--   - 3+ full months of realistic weekday attendance + current month up to CURDATE()
--   - 3 months of payroll generated via process_monthly_payroll()
-- =============================================================================

USE payroll_attendance_db;

-- 1. Departments
INSERT INTO departments (department_code, department_name, description) VALUES
('ENG', 'Software Engineering', 'Core product engineering, backend APIs, and frontend architecture'),
('QA',  'Quality Assurance',    'Automated testing, regression validation, and release quality'),
('OPS', 'DevOps & Cloud',       'CI/CD pipelines, cloud infrastructure, and site reliability'),
('HR',  'Human Resources',      'Talent acquisition, employee relations, and attendance compliance'),
('FIN', 'Finance & Payroll',    'Compensation governance, taxation, and monthly payroll disbursement');

-- 2. Leave Types
INSERT INTO leave_types (type_code, type_name, is_paid, max_days_per_year, description) VALUES
('CL',  'Casual Leave',    TRUE,  12, 'Short-notice personal leave'),
('SL',  'Sick Leave',      TRUE,  10, 'Medical and health recovery leave'),
('EL',  'Earned Leave',    TRUE,  15, 'Planned annual privilege leave'),
('LWP', 'Leave Without Pay', FALSE, 0, 'Unpaid leave resulting in Loss-of-Pay deduction');

-- 3. Employees (12 IT firm employees hired well before the 3-month window)
INSERT INTO employees (emp_code, first_name, last_name, email, phone, department_id, designation, hire_date, employment_status) VALUES
('EMP001', 'Ananya',  'Sharma',     'ananya.sharma@novatech.in',    '+91-98101-10001', 4, 'HR Manager',                  '2022-03-15', 'ACTIVE'),
('EMP002', 'Rohan',   'Verma',      'rohan.verma@novatech.in',      '+91-98101-10002', 5, 'Payroll Administrator',       '2022-06-01', 'ACTIVE'),
('EMP003', 'Aarav',   'Mehta',      'aarav.mehta@novatech.in',      '+91-98101-10003', 1, 'Senior Software Engineer',    '2023-01-10', 'ACTIVE'),
('EMP004', 'Priya',   'Nair',       'priya.nair@novatech.in',       '+91-98101-10004', 1, 'Full Stack Developer',        '2023-04-18', 'ACTIVE'),
('EMP005', 'Kabir',   'Malhotra',   'kabir.malhotra@novatech.in',   '+91-98101-10005', 1, 'Backend Tech Lead',           '2021-11-05', 'ACTIVE'),
('EMP006', 'Sneha',   'Kulkarni',   'sneha.kulkarni@novatech.in',   '+91-98101-10006', 2, 'QA Lead',                     '2022-09-12', 'ACTIVE'),
('EMP007', 'Vikram',  'Reddy',      'vikram.reddy@novatech.in',     '+91-98101-10007', 2, 'Automation Test Engineer',    '2024-02-01', 'ACTIVE'),
('EMP008', 'Neha',    'Joshi',      'neha.joshi@novatech.in',       '+91-98101-10008', 3, 'Site Reliability Engineer',   '2023-07-24', 'ACTIVE'),
('EMP009', 'Arjun',   'Deshmukh',   'arjun.deshmukh@novatech.in',   '+91-98101-10009', 3, 'Cloud DevOps Engineer',       '2024-05-14', 'ACTIVE'),
('EMP010', 'Meera',   'Iyer',       'meera.iyer@novatech.in',       '+91-98101-10010', 1, 'UI/UX Frontend Engineer',     '2024-08-05', 'ACTIVE'),
('EMP011', 'Siddharth','Bhatia',    'siddharth.bhatia@novatech.in', '+91-98101-10011', 5, 'Financial Analyst',           '2023-10-09', 'ACTIVE'),
('EMP012', 'Divya',   'Kapoor',     'divya.kapoor@novatech.in',     '+91-98101-10012', 4, 'Talent Acquisition Specialist','2024-01-15', 'ACTIVE');

-- 4. User Accounts
-- Demo passwords (hashed with Werkzeug scrypt):
--   HR_ADMIN accounts (admin, payroll.admin) -> Admin@123
--   EMPLOYEE accounts                        -> Employee@123
INSERT INTO user_accounts (employee_id, username, password_hash, role, is_active) VALUES
(1,  'admin',         'scrypt:32768:8:1$b0o6oaNF6jTex7YJ$3cbc0db3c52a0018d761d3595e1ce6ffeadda71ad8c2171f1ee75d8cf618656dd35ac760f2bc5982ad5397072e240367eaa5fb795abb0fe4cea6363326b113ba', 'HR_ADMIN', TRUE),
(2,  'payroll.admin', 'scrypt:32768:8:1$b0o6oaNF6jTex7YJ$3cbc0db3c52a0018d761d3595e1ce6ffeadda71ad8c2171f1ee75d8cf618656dd35ac760f2bc5982ad5397072e240367eaa5fb795abb0fe4cea6363326b113ba', 'HR_ADMIN', TRUE),
(3,  'aarav.m',       'scrypt:32768:8:1$M4TNpuYr6QVo2Jsg$f1ec67385168222af744caf59ed3279998168687a72107517607f705c36a81da50afa9149d3b95ac68dd4529e7b42c26de60c242702c7c571a437d0ca430ba26', 'EMPLOYEE', TRUE),
(4,  'priya.n',       'scrypt:32768:8:1$M4TNpuYr6QVo2Jsg$f1ec67385168222af744caf59ed3279998168687a72107517607f705c36a81da50afa9149d3b95ac68dd4529e7b42c26de60c242702c7c571a437d0ca430ba26', 'EMPLOYEE', TRUE),
(5,  'kabir.m',       'scrypt:32768:8:1$M4TNpuYr6QVo2Jsg$f1ec67385168222af744caf59ed3279998168687a72107517607f705c36a81da50afa9149d3b95ac68dd4529e7b42c26de60c242702c7c571a437d0ca430ba26', 'EMPLOYEE', TRUE),
(6,  'sneha.k',       'scrypt:32768:8:1$M4TNpuYr6QVo2Jsg$f1ec67385168222af744caf59ed3279998168687a72107517607f705c36a81da50afa9149d3b95ac68dd4529e7b42c26de60c242702c7c571a437d0ca430ba26', 'EMPLOYEE', TRUE),
(7,  'vikram.r',      'scrypt:32768:8:1$M4TNpuYr6QVo2Jsg$f1ec67385168222af744caf59ed3279998168687a72107517607f705c36a81da50afa9149d3b95ac68dd4529e7b42c26de60c242702c7c571a437d0ca430ba26', 'EMPLOYEE', TRUE),
(8,  'neha.j',        'scrypt:32768:8:1$M4TNpuYr6QVo2Jsg$f1ec67385168222af744caf59ed3279998168687a72107517607f705c36a81da50afa9149d3b95ac68dd4529e7b42c26de60c242702c7c571a437d0ca430ba26', 'EMPLOYEE', TRUE),
(9,  'arjun.d',       'scrypt:32768:8:1$M4TNpuYr6QVo2Jsg$f1ec67385168222af744caf59ed3279998168687a72107517607f705c36a81da50afa9149d3b95ac68dd4529e7b42c26de60c242702c7c571a437d0ca430ba26', 'EMPLOYEE', TRUE),
(10, 'meera.i',       'scrypt:32768:8:1$M4TNpuYr6QVo2Jsg$f1ec67385168222af744caf59ed3279998168687a72107517607f705c36a81da50afa9149d3b95ac68dd4529e7b42c26de60c242702c7c571a437d0ca430ba26', 'EMPLOYEE', TRUE),
(11, 'siddharth.b',   'scrypt:32768:8:1$M4TNpuYr6QVo2Jsg$f1ec67385168222af744caf59ed3279998168687a72107517607f705c36a81da50afa9149d3b95ac68dd4529e7b42c26de60c242702c7c571a437d0ca430ba26', 'EMPLOYEE', TRUE),
(12, 'divya.k',       'scrypt:32768:8:1$M4TNpuYr6QVo2Jsg$f1ec67385168222af744caf59ed3279998168687a72107517607f705c36a81da50afa9149d3b95ac68dd4529e7b42c26de60c242702c7c571a437d0ca430ba26', 'EMPLOYEE', TRUE);

-- 5. Salary Structures (Including historical revisions for EMP003 & EMP004)
INSERT INTO salaries (employee_id, basic_salary, hra, da, other_allowances, pf_deduction, professional_tax, effective_from, effective_to, is_current) VALUES
(1,  65000.00, 26000.00,  8000.00,  6000.00, 3600.00, 200.00, '2025-04-01', NULL, TRUE),
(2,  60000.00, 24000.00,  7500.00,  5500.00, 3600.00, 200.00, '2025-04-01', NULL, TRUE),
-- EMP003: old revision + current revision
(3,  55000.00, 22000.00,  6000.00,  5000.00, 3000.00, 200.00, '2025-01-01', DATE_SUB(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 1 MONTH) - INTERVAL 1 DAY, FALSE),
(3,  68000.00, 27200.00,  8500.00,  6300.00, 3600.00, 200.00, DATE_SUB(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 1 MONTH), NULL, TRUE),
-- EMP004: old revision + current revision
(4,  45000.00, 18000.00,  5000.00,  4000.00, 2400.00, 200.00, '2025-01-01', DATE_SUB(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 2 MONTH) - INTERVAL 1 DAY, FALSE),
(4,  52000.00, 20800.00,  6200.00,  4800.00, 3000.00, 200.00, DATE_SUB(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 2 MONTH), NULL, TRUE),
(5,  80000.00, 32000.00, 10000.00,  8000.00, 3600.00, 200.00, '2025-04-01', NULL, TRUE),
(6,  58000.00, 23200.00,  7000.00,  5000.00, 3600.00, 200.00, '2025-04-01', NULL, TRUE),
(7,  38000.00, 15200.00,  4500.00,  3300.00, 2160.00, 200.00, '2025-04-01', NULL, TRUE),
(8,  64000.00, 25600.00,  8000.00,  6400.00, 3600.00, 200.00, '2025-04-01', NULL, TRUE),
(9,  48000.00, 19200.00,  6000.00,  4800.00, 2880.00, 200.00, '2025-04-01', NULL, TRUE),
(10, 42000.00, 16800.00,  5000.00,  4200.00, 2520.00, 200.00, '2025-04-01', NULL, TRUE),
(11, 50000.00, 20000.00,  6000.00,  4000.00, 3000.00, 200.00, '2025-04-01', NULL, TRUE),
(12, 36000.00, 14400.00,  4000.00,  3600.00, 2160.00, 200.00, '2025-04-01', NULL, TRUE);

-- 6. Leave Requests across the past 3 full months & current month
--    Dates anchored to the 1st day of M-3, M-2, M-1, and current month M0
SET @m3_start = DATE_SUB(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 3 MONTH);
SET @m2_start = DATE_SUB(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 2 MONTH);
SET @m1_start = DATE_SUB(DATE_FORMAT(CURDATE(), '%Y-%m-01'), INTERVAL 1 MONTH);
SET @m0_start = DATE_FORMAT(CURDATE(), '%Y-%m-01');

INSERT INTO leave_requests (employee_id, leave_type_id, start_date, end_date, total_days, reason, status, approved_by, approved_at) VALUES
-- Month M-3 leaves (Approved)
(3,  1, DATE_ADD(@m3_start, INTERVAL 4 DAY),  DATE_ADD(@m3_start, INTERVAL 5 DAY),  2.0, 'Family function out of town',          'APPROVED', 1, DATE_ADD(@m3_start, INTERVAL 1 DAY)),
(7,  2, DATE_ADD(@m3_start, INTERVAL 10 DAY), DATE_ADD(@m3_start, INTERVAL 10 DAY), 1.0, 'Viral fever recovery',                  'APPROVED', 1, DATE_ADD(@m3_start, INTERVAL 9 DAY)),
-- Month M-2 leaves (Approved & Rejected)
(4,  3, DATE_ADD(@m2_start, INTERVAL 7 DAY),  DATE_ADD(@m2_start, INTERVAL 9 DAY),  3.0, 'Planned annual vacation',               'APPROVED', 1, DATE_ADD(@m2_start, INTERVAL 2 DAY)),
(9,  4, DATE_ADD(@m2_start, INTERVAL 14 DAY), DATE_ADD(@m2_start, INTERVAL 15 DAY), 2.0, 'Personal travel (LWP)',                 'APPROVED', 1, DATE_ADD(@m2_start, INTERVAL 11 DAY)),
(10, 1, DATE_ADD(@m2_start, INTERVAL 18 DAY), DATE_ADD(@m2_start, INTERVAL 19 DAY), 2.0, 'Urgent personal errand',                'REJECTED', 1, DATE_ADD(@m2_start, INTERVAL 16 DAY)),
-- Month M-1 leaves (Approved Paid & LWP)
(6,  2, DATE_ADD(@m1_start, INTERVAL 2 DAY),  DATE_ADD(@m1_start, INTERVAL 3 DAY),  2.0, 'Dental surgery and rest',               'APPROVED', 1, DATE_ADD(@m1_start, INTERVAL 1 DAY)),
(12, 4, DATE_ADD(@m1_start, INTERVAL 11 DAY), DATE_ADD(@m1_start, INTERVAL 12 DAY), 2.0, 'Extended hometown visit (LWP)',         'APPROVED', 1, DATE_ADD(@m1_start, INTERVAL 8 DAY)),
(5,  1, DATE_ADD(@m1_start, INTERVAL 20 DAY), DATE_ADD(@m1_start, INTERVAL 20 DAY), 1.0, 'Home appliance installation',           'APPROVED', 1, DATE_ADD(@m1_start, INTERVAL 18 DAY)),
-- Current Month M0 leaves (Pending for HR Dashboard workflow)
(3,  1, DATE_ADD(CURDATE(), INTERVAL 3 DAY),  DATE_ADD(CURDATE(), INTERVAL 4 DAY),  2.0, 'Attending sister wedding',              'PENDING',  NULL, NULL),
(8,  3, DATE_ADD(CURDATE(), INTERVAL 7 DAY),  DATE_ADD(CURDATE(), INTERVAL 9 DAY),  3.0, 'Year-end family trip',                  'PENDING',  NULL, NULL),
(11, 2, DATE_ADD(CURDATE(), INTERVAL 1 DAY),  DATE_ADD(CURDATE(), INTERVAL 1 DAY),  1.0, 'Scheduled medical checkup',             'PENDING',  NULL, NULL);

-- 7. Populate 3+ Months of Daily Weekday Attendance (M-3 start through CURDATE())
--    Uses a temporary helper procedure that respects approved leave dates,
--    adds realistic on-time check-ins, occasional late marks (> 09:30), WFH,
--    half-days, and occasional unexcused absences.
DROP PROCEDURE IF EXISTS sp_seed_attendance_window;
DELIMITER //
CREATE PROCEDURE sp_seed_attendance_window()
BEGIN
    DECLARE v_cur_date DATE;
    DECLARE v_emp_id   INT;
    DECLARE v_dow      INT;
    DECLARE v_hash     INT;
    DECLARE v_on_leave INT;
    DECLARE v_cin      TIME;
    DECLARE v_cout     TIME;
    DECLARE v_status   VARCHAR(20);
    DECLARE v_remarks  VARCHAR(255);

    SET v_cur_date = @m3_start;

    WHILE v_cur_date <= CURDATE() DO
        SET v_dow = DAYOFWEEK(v_cur_date); -- 1=Sun, 7=Sat

        IF v_dow BETWEEN 2 AND 6 THEN
            SET v_emp_id = 1;
            WHILE v_emp_id <= 12 DO
                -- Check if employee has an APPROVED leave covering v_cur_date
                SELECT COUNT(*) INTO v_on_leave
                FROM leave_requests
                WHERE employee_id = v_emp_id
                  AND status = 'APPROVED'
                  AND v_cur_date BETWEEN start_date AND end_date;

                IF v_on_leave > 0 THEN
                    INSERT INTO attendance (employee_id, attendance_date, check_in_time, check_out_time, status, remarks)
                    VALUES (v_emp_id, v_cur_date, NULL, NULL, 'ON_LEAVE', 'Approved leave');
                ELSE
                    SET v_hash = MOD((v_emp_id * 37) + DAY(v_cur_date) * 13 + MONTH(v_cur_date) * 7, 100);

                    IF v_hash < 4 THEN
                        -- Occasional unexcused absence (~4%)
                        INSERT INTO attendance (employee_id, attendance_date, check_in_time, check_out_time, status, remarks)
                        VALUES (v_emp_id, v_cur_date, NULL, NULL, 'ABSENT', 'Unplanned absence');
                    ELSEIF v_hash < 8 THEN
                        -- Occasional half-day (~4%)
                        INSERT INTO attendance (employee_id, attendance_date, check_in_time, check_out_time, status, remarks)
                        VALUES (v_emp_id, v_cur_date, '09:20:00', '13:45:00', 'HALF_DAY', 'Half-day shift');
                    ELSEIF v_hash < 16 THEN
                        -- Work From Home (~8%)
                        INSERT INTO attendance (employee_id, attendance_date, check_in_time, check_out_time, status, remarks)
                        VALUES (v_emp_id, v_cur_date, '09:15:00', '18:15:00', 'WORK_FROM_HOME', 'Remote sprint day');
                    ELSEIF v_hash < 28 THEN
                        -- Late check-in (~12%, triggers auto-compute is_late = TRUE and late_minutes)
                        SET v_cin  = ADDTIME('09:35:00', SEC_TO_TIME(MOD(v_hash * 180, 2700)));
                        SET v_cout = ADDTIME('18:20:00', SEC_TO_TIME(MOD(v_hash * 120, 1800)));
                        INSERT INTO attendance (employee_id, attendance_date, check_in_time, check_out_time, status, remarks)
                        VALUES (v_emp_id, v_cur_date, v_cin, v_cout, 'PRESENT', 'Late arrival');
                    ELSE
                        -- Standard on-time PRESENT
                        SET v_cin  = ADDTIME('08:55:00', SEC_TO_TIME(MOD(v_hash * 95, 1980)));
                        SET v_cout = ADDTIME('18:00:00', SEC_TO_TIME(MOD(v_hash * 110, 2400)));
                        INSERT INTO attendance (employee_id, attendance_date, check_in_time, check_out_time, status, remarks)
                        VALUES (v_emp_id, v_cur_date, v_cin, v_cout, 'PRESENT', 'Regular shift');
                    END IF;
                END IF;

                SET v_emp_id = v_emp_id + 1;
            END WHILE;
        END IF;

        SET v_cur_date = DATE_ADD(v_cur_date, INTERVAL 1 DAY);
    END WHILE;
END //
DELIMITER ;

CALL sp_seed_attendance_window();
DROP PROCEDURE IF EXISTS sp_seed_attendance_window;

-- 8. Generate 3 Complete Months of Payroll using Phase 2 Stored Procedure
CALL process_monthly_payroll(MONTH(@m3_start), YEAR(@m3_start), 22, 2);
CALL process_monthly_payroll(MONTH(@m2_start), YEAR(@m2_start), 22, 2);
CALL process_monthly_payroll(MONTH(@m1_start), YEAR(@m1_start), 22, 2);

-- Mark the first two historical payroll months as PAID and keep M-1 as PROCESSED
UPDATE payroll
SET payment_status = 'PAID',
    payment_date = LAST_DAY(STR_TO_DATE(CONCAT(pay_year, '-', LPAD(pay_month, 2, '0'), '-01'), '%Y-%m-%d'))
WHERE (pay_year = YEAR(@m3_start) AND pay_month = MONTH(@m3_start))
   OR (pay_year = YEAR(@m2_start) AND pay_month = MONTH(@m2_start));
