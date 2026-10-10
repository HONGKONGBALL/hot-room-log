"""Hot Room Log application factory."""

import os

from flask import Flask, render_template, request

from .http import json_response


def create_app(config=None):
    app = Flask(__name__)
    app.config["DATABASE"] = os.environ.get("HOTROOM_DB", "instance/hotroom.db")
    app.config["READONLY"] = os.environ.get("HOTROOM_READONLY", "") == "1"
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or os.urandom(24)
    app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
    app.config["JSON_AS_ASCII"] = False
    if config:
        app.config.update(config)
    # Keep HTTP error handlers active under TESTING so 404 and 413 return pages.
    app.config["PROPAGATE_EXCEPTIONS"] = False

    from .db import close_db, init_database

    init_database(app.config["DATABASE"])
    app.teardown_appcontext(close_db)

    from .api import bp as api_bp
    from .views import bp as views_bp

    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp)

    @app.before_request
    def reject_large_body():
        limit = app.config.get("MAX_CONTENT_LENGTH")
        length = request.content_length
        if limit and length is not None and length > limit:
            return (
                render_template(
                    "error.html",
                    title="File too large",
                    heading="File too large",
                    message="File too large (max 1 MB).",
                ),
                413,
            )

    @app.after_request
    def html_charset(response):
        content_type = response.headers.get("Content-Type", "")
        if content_type.startswith("text/html") and "charset" not in content_type.lower():
            response.headers["Content-Type"] = "text/html; charset=utf-8"
        return response

    @app.errorhandler(404)
    def not_found(_error):
        if request.path.startswith("/api/"):
            return json_response({"error": "Not found"}, 404)
        return (
            render_template(
                "error.html",
                title="Page not found",
                heading="Page not found",
                message="Page not found",
            ),
            404,
        )

    @app.errorhandler(413)
    def too_large(_error):
        return (
            render_template(
                "error.html",
                title="File too large",
                heading="File too large",
                message="File too large (max 1 MB).",
            ),
            413,
        )

    return app
