# START HERE — Opening & Running in VS Code

Welcome to the **Payroll & Attendance Management System** (`Payroll_Attendance_System`). Follow these steps to open, configure, initialize, and run the project in Visual Studio Code.

---

## 1. Open the Project in VS Code

1. Extract `Payroll_Attendance_System.zip` to a local folder (e.g., `C:\Projects\Payroll_Attendance_System`).
2. Open **VS Code**.
3. Click **File → Open Folder...** and select the `Payroll_Attendance_System` root folder.
4. Open the integrated terminal in VS Code (`Ctrl + ~` or **Terminal → New Terminal**).

---

## 2. Select or Create a Python Environment

1. Press `Ctrl + Shift + P` → **Python: Select Interpreter** (or create a virtual environment):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Install all Python dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

---

## 3. Configure MySQL Credentials (`.env`)

1. Copy `.env.example` to `.env` in the project root:
   ```powershell
   copy .env.example .env
   ```
2. Open `.env` in VS Code and set your local MySQL 8.0+ password:
   ```ini
   SECRET_KEY=replace-with-a-random-secret-key
   MYSQL_HOST=127.0.0.1
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=YOUR_MYSQL_PASSWORD
   MYSQL_DATABASE=payroll_attendance_db
   ```

---

## 4. Initialize the MySQL 8.0+ Database

Ensure your MySQL 8.0+ server (`MySQL80`) is running, then execute the automated setup script from the VS Code terminal:

```powershell
python backend/setup_db.py
```

This runs all scripts in sequence:
- `Phase2/schema.sql`
- `Phase2/functions.sql`
- `Phase2/triggers.sql`
- `Phase2/procedures.sql`
- `Phase2/sample_data.sql`
- `Phase3/indexes.sql`
- `Phase4/transactions.sql`

---

## 5. Run the Web Application

Start the Flask server from the project root:

```powershell
python backend/app.py
```

Open **http://127.0.0.1:5000** in your browser.

### Demo Login Credentials
- **HR / Admin:** `admin` / `Admin@123` (or `payroll.admin` / `Admin@123`)
- **Employee:** `aarav.m` / `Employee@123`

---

## 6. Run Tests & Query Optimization Check

```powershell
python -m pytest -v tests/test_system.py
python tests/run_explain_comparison.py
```
