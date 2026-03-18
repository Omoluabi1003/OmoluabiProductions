"""Lightweight Flask dashboard for monitoring."""

from __future__ import annotations

from pathlib import Path

from flask import Flask, render_template

from agent.config import AppConfig



def create_app(config: AppConfig) -> Flask:
    template_folder = Path(__file__).parent / "templates"
    static_folder = Path(__file__).parent / "static"
    app = Flask(__name__, template_folder=str(template_folder), static_folder=str(static_folder))

    @app.route("/")
    def index() -> str:
        logs = ""
        if config.scrape_log_path.exists():
            logs = "\n".join(config.scrape_log_path.read_text(encoding="utf-8", errors="ignore").splitlines()[-30:])
        return render_template(
            "index.html",
            app_name=config.app_name,
            db_path=config.sqlite_path,
            raw_path=config.raw_export_path,
            clean_path=config.clean_export_path,
            excel_path=config.excel_export_path,
            failed_path=config.failed_urls_path,
            summary_path=config.run_summary_path,
            recent_logs=logs,
        )

    return app
