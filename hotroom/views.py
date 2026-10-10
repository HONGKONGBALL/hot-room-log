"""HTML routes."""

from datetime import datetime

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
)

from .calc import BANDS, compare_sentence, compute, format_1, format_effect, working_steps
from .chart import chart_model
from .csvio import MSG_CHOOSE, ImportRejected, import_csv, render_csv
from .db import (
    delete_reading,
    delete_room,
    find_room_by_name,
    get_db,
    get_reading,
    get_room,
    insert_reading,
    insert_room,
    list_readings,
    list_rooms,
    reset_database,
)
from .letter import build_letter, enrich, summarize
from .validate import MSG_DUP, now_minute, parse_name, validate_reading

bp = Blueprint("views", __name__)


def _readonly():
    return bool(current_app.config.get("READONLY"))


def _guard():
    if _readonly():
        return (
            render_template(
                "error.html",
                title="Read-only demo",
                heading="Read-only demo",
                message="Read-only demo",
            ),
            403,
        )
    return None


def _room_not_found():
    return (
        render_template(
            "error.html",
            title="Room not found",
            heading="Room not found",
            message="Room not found",
        ),
        404,
    )


def _reading_not_found():
    return (
        render_template(
            "error.html",
            title="Reading not found",
            heading="Reading not found",
            message="Reading not found",
        ),
        404,
    )


def _as_room(room):
    return {
        "id": room["id"],
        "name": room["name"],
        "is_sample": int(room["is_sample"]),
    }


def _load_room(room_id):
    room = get_room(get_db(), room_id)
    if room is None:
        return None, None, None
    readings = [enrich(row) for row in list_readings(get_db(), room_id)]
    return _as_room(room), readings, summarize(readings)


def _dashboard_context(name_value="", name_error=None):
    conn = get_db()
    cards = []
    has_sample = False
    for room in list_rooms(conn):
        if room["is_sample"]:
            has_sample = True
        readings = [enrich(row) for row in list_readings(conn, room["id"])]
        summary = summarize(readings)
        cards.append(
            {
                "room": _as_room(room),
                "summary": summary,
                "band": summary["latest"]["band_key"] if summary else "none",
            }
        )
    return {
        "title": "Rooms",
        "cards": cards,
        "show_sample_banner": has_sample,
        "name_value": name_value,
        "name_error": name_error,
    }


def _result_block(condition, temperature, humidity):
    result = compute(temperature, humidity)
    return {
        "condition": condition,
        "humidex_text": format_1(result["humidex"]),
        "dew_text": format_1(result["dew_point_c"]),
        "effect_text": format_effect(result["humidity_effect"]),
        "band": result["band"],
        "band_key": result["band_key"],
        "humidex": result["humidex"],
        "steps": working_steps(temperature, humidity, result),
    }


@bp.get("/")
def dashboard():
    return render_template("dashboard.html", **_dashboard_context())


@bp.post("/rooms")
def create_room():
    blocked = _guard()
    if blocked:
        return blocked
    raw = request.form.get("name", "")
    name, error = parse_name(raw)
    if error is None and find_room_by_name(get_db(), name):
        error = MSG_DUP
    if error:
        return render_template(
            "dashboard.html", **_dashboard_context(name_value=raw, name_error=error)
        ), 400
    new_id = insert_room(get_db(), name, is_sample=0)
    flash("Room added.")
    return redirect(f"/rooms/{new_id}")


@bp.get("/rooms/<int:room_id>")
def room_page(room_id):
    room, readings, summary = _load_room(room_id)
    if room is None:
        return _room_not_found()
    return render_template(
        "room.html",
        title=room["name"],
        room=room,
        readings=readings,
        summary=summary,
        chart=chart_model(readings) if readings else None,
        show_sample_banner=bool(room["is_sample"]),
        form_values={
            "temp_c": "",
            "rh_percent": "",
            "taken_at": now_minute().strftime("%Y-%m-%dT%H:%M"),
            "note": "",
        },
        errors={},
    )


@bp.post("/rooms/<int:room_id>/readings")
def add_reading(room_id):
    blocked = _guard()
    if blocked:
        return blocked
    room, readings, summary = _load_room(room_id)
    if room is None:
        return _room_not_found()
    form = {
        "temp_c": request.form.get("temp_c", ""),
        "rh_percent": request.form.get("rh_percent", ""),
        "taken_at": request.form.get("taken_at", ""),
        "note": request.form.get("note", ""),
    }
    errors, parsed = validate_reading(form)
    if errors:
        return render_template(
            "room.html",
            title=room["name"],
            room=room,
            readings=readings,
            summary=summary,
            chart=chart_model(readings) if readings else None,
            show_sample_banner=bool(room["is_sample"]),
            form_values=form,
            errors=errors,
        ), 400
    insert_reading(
        get_db(),
        room_id,
        parsed["taken_at"],
        parsed["temp_c"],
        parsed["rh_percent"],
        parsed["note"],
    )
    flash("Reading added.")
    return redirect(f"/rooms/{room_id}")


@bp.post("/rooms/<int:room_id>/delete")
def remove_room(room_id):
    blocked = _guard()
    if blocked:
        return blocked
    room = get_room(get_db(), room_id)
    if room is None:
        return _room_not_found()
    delete_room(get_db(), room_id)
    flash("Room deleted.")
    return redirect("/")


@bp.post("/readings/<int:reading_id>/delete")
def remove_reading(reading_id):
    blocked = _guard()
    if blocked:
        return blocked
    reading = get_reading(get_db(), reading_id)
    if reading is None:
        return _reading_not_found()
    room_id = reading["room_id"]
    delete_reading(get_db(), reading_id)
    flash("Reading deleted.")
    return redirect(f"/rooms/{room_id}")


@bp.get("/rooms/<int:room_id>/sheet")
def sheet(room_id):
    room, readings, summary = _load_room(room_id)
    if room is None:
        return _room_not_found()
    letter = build_letter(room["name"], readings) if readings else ""
    return render_template(
        "sheet.html",
        title=f"Heat evidence sheet: {room['name']}",
        room=room,
        readings=readings,
        summary=summary,
        chart=chart_model(readings) if readings else None,
        letter=letter,
        today=datetime.now().strftime("%Y-%m-%d"),
        show_sample_banner=bool(room["is_sample"]),
    )


@bp.get("/rooms/<int:room_id>/export.csv")
def export_room(room_id):
    room = get_room(get_db(), room_id)
    if room is None:
        return _room_not_found()
    body = render_csv(get_db(), room_id=room_id)
    return _csv_response(body, f"hot-room-log-room-{room_id}.csv")


@bp.get("/export.csv")
def export_all():
    body = render_csv(get_db())
    return _csv_response(body, "hot-room-log.csv")


def _csv_response(body, filename):
    from flask import Response

    response = Response(body, mimetype="text/csv")
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@bp.get("/import")
def import_form():
    return render_template("import.html", title="Import readings from CSV", import_error=None)


@bp.post("/import")
def import_post():
    blocked = _guard()
    if blocked:
        return blocked
    upload = request.files.get("file")
    if upload is None or not (upload.filename or "").strip():
        return render_template(
            "import.html",
            title="Import readings from CSV",
            import_error=MSG_CHOOSE,
        ), 400
    raw = upload.read()
    try:
        result = import_csv(get_db(), raw)
    except ImportRejected as exc:
        return render_template(
            "import.html",
            title="Import readings from CSV",
            import_error=exc.message,
        ), 400
    return render_template("import_result.html", title="Import results", result=result)


@bp.post("/reset")
def reset():
    blocked = _guard()
    if blocked:
        return blocked
    reset_database(get_db())
    flash("Sample data restored.")
    return redirect("/")


@bp.get("/calc")
def calculator():
    keys = ("temp_c", "rh_percent", "temp_c_b", "rh_percent_b")
    if not any(key in request.args for key in keys):
        return render_template(
            "calc.html",
            title="Humidex calculator",
            bands=BANDS,
            values={key: "" for key in keys},
            errors={},
            result_a=None,
            result_b=None,
            compare=None,
        )
    values = {key: request.args.get(key, "") for key in keys}
    data_a = {"temp_c": values["temp_c"], "rh_percent": values["rh_percent"]}
    errors, _parsed = validate_reading(data_a)
    # Time and note are not part of the calculator. Drop those keys if present.
    errors.pop("taken_at", None)
    errors.pop("note", None)
    b_active = values["temp_c_b"].strip() != "" or values["rh_percent_b"].strip() != ""
    if b_active:
        data_b = {"temp_c": values["temp_c_b"], "rh_percent": values["rh_percent_b"]}
        errors_b, _parsed_b = validate_reading(data_b)
        if "temp_c" in errors_b:
            errors["temp_c_b"] = errors_b["temp_c"]
        if "rh_percent" in errors_b:
            errors["rh_percent_b"] = errors_b["rh_percent"]
    if errors:
        return render_template(
            "calc.html",
            title="Humidex calculator",
            bands=BANDS,
            values=values,
            errors=errors,
            result_a=None,
            result_b=None,
            compare=None,
        ), 400
    result_a = _result_block("a", _parsed["temp_c"], _parsed["rh_percent"])
    result_b = None
    compare = None
    if b_active:
        _errors_b, parsed_b = validate_reading(
            {"temp_c": values["temp_c_b"], "rh_percent": values["rh_percent_b"]}
        )
        result_b = _result_block("b", parsed_b["temp_c"], parsed_b["rh_percent"])
        compare = compare_sentence(result_a["humidex"], result_b["humidex"])
    return render_template(
        "calc.html",
        title="Humidex calculator",
        bands=BANDS,
        values=values,
        errors={},
        result_a=result_a,
        result_b=result_b,
        compare=compare,
    )


@bp.get("/about")
def about():
    return render_template("about.html", title="About Hot Room Log", bands=BANDS)
