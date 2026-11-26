/**
 * Payroll & Attendance Management System — Client Helpers
 */
document.addEventListener("DOMContentLoaded", () => {
    // Mobile sidebar toggle
    const toggleBtn = document.getElementById("sidebarToggle");
    const sidebar = document.getElementById("appSidebar");
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener("click", () => {
            sidebar.classList.toggle("show");
        });
    }

    // Quick-fill demo credentials on Login page
    document.querySelectorAll("[data-demo-user]").forEach((btn) => {
        btn.addEventListener("click", () => {
            const u = document.getElementById("username");
            const p = document.getElementById("password");
            if (u && p) {
                u.value = btn.getAttribute("data-demo-user");
                p.value = btn.getAttribute("data-demo-pass");
            }
        });
    });

    // Leave form half-day date sync
    const halfDayCheck = document.getElementById("isHalfDayCheck");
    const leaveStart = document.getElementById("leaveStartDate");
    const leaveEnd = document.getElementById("leaveEndDate");
    if (halfDayCheck && leaveStart && leaveEnd) {
        halfDayCheck.addEventListener("change", () => {
            if (halfDayCheck.checked && leaveStart.value) {
                leaveEnd.value = leaveStart.value;
            }
        });
        leaveStart.addEventListener("change", () => {
            if (halfDayCheck.checked) {
                leaveEnd.value = leaveStart.value;
            }
        });
    }

    // Populate Edit Employee Modal
    const editEmpModal = document.getElementById("editEmployeeModal");
    if (editEmpModal) {
        editEmpModal.addEventListener("show.bs.modal", (event) => {
            const btn = event.relatedTarget;
            if (!btn) return;
            const form = document.getElementById("editEmployeeForm");
            form.action = btn.getAttribute("data-action");
            document.getElementById("editFirstName").value = btn.getAttribute("data-first-name") || "";
            document.getElementById("editLastName").value = btn.getAttribute("data-last-name") || "";
            document.getElementById("editEmail").value = btn.getAttribute("data-email") || "";
            document.getElementById("editPhone").value = btn.getAttribute("data-phone") || "";
            document.getElementById("editDepartmentId").value = btn.getAttribute("data-department-id") || "";
            document.getElementById("editDesignation").value = btn.getAttribute("data-designation") || "";
            document.getElementById("editHireDate").value = btn.getAttribute("data-hire-date") || "";
            document.getElementById("editStatus").value = btn.getAttribute("data-status") || "ACTIVE";
        });
    }

    // Populate Edit Attendance Modal
    const editAttModal = document.getElementById("editAttendanceModal");
    if (editAttModal) {
        editAttModal.addEventListener("show.bs.modal", (event) => {
            const btn = event.relatedTarget;
            if (!btn) return;
            document.getElementById("editAttendanceForm").action = btn.getAttribute("data-action");
            document.getElementById("editAttEmployeeName").textContent = btn.getAttribute("data-emp-name") || "";
            document.getElementById("editAttStatus").value = btn.getAttribute("data-status") || "PRESENT";
            document.getElementById("editAttCheckIn").value = (btn.getAttribute("data-checkin") || "").slice(0, 5);
            document.getElementById("editAttCheckOut").value = (btn.getAttribute("data-checkout") || "").slice(0, 5);
            document.getElementById("editAttRemarks").value = btn.getAttribute("data-remarks") || "";
        });
    }

    // Populate Reset Password Modal
    const resetPwdModal = document.getElementById("resetPasswordModal");
    if (resetPwdModal) {
        resetPwdModal.addEventListener("show.bs.modal", (event) => {
            const btn = event.relatedTarget;
            if (!btn) return;
            document.getElementById("resetPasswordForm").action = btn.getAttribute("data-action");
            document.getElementById("resetPwdUsername").textContent = btn.getAttribute("data-username") || "";
        });
    }
});
