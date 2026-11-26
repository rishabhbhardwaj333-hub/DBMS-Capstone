"""Flask application factory and entry point."""

import calendar
from pathlib import Path
import sys
from flask import Flask, render_template

# Ensure project root is importable when running `python backend/app.py` directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.auth import current_user
from backend.config import Config
from backend.routes.admin_routes import admin_bp
from backend.routes.auth_routes import auth_bp
from backend.routes.employee_routes import employee_bp


def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder=str(PROJECT_ROOT / "frontend" / "templates"),
        static_folder=str(PROJECT_ROOT / "frontend" / "static"),
    )
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(employee_bp)

    @app.context_processor
    def inject_globals():
        return {"user": current_user()}

    @app.template_filter("inr")
    def format_inr(value):
        try:
            num = float(value or 0)
            return f"₹{num:,.2f}"
        except (TypeError, ValueError):
            return "₹0.00"

    @app.template_filter("month_name")
    def format_month_name(month_num):
        try:
            return calendar.month_name[int(month_num)]
        except (TypeError, ValueError, IndexError):
            return str(month_num)

    @app.errorhandler(403)
    def forbidden(_err):
        return render_template("error.html", code=403, title="Access Denied",
                               message="You do not have permission to view this resource."), 403

    @app.errorhandler(404)
    def not_found(_err):
        return render_template("error.html", code=404, title="Not Found",
                               message="The requested page or record could not be found."), 404

    @app.errorhandler(500)
    def server_error(_err):
        return render_template("error.html", code=500, title="Server Error",
                               message="An unexpected server error occurred. Please check database connectivity."), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=Config.DEBUG)
