"""Small JSON response helper. Bodies use standard json spacing."""

import json

from flask import Response


def json_response(payload, status=200):
    body = json.dumps(payload, ensure_ascii=False)
    response = Response(body, status=status, mimetype="application/json")
    response.headers["Content-Type"] = "application/json"
    return response
