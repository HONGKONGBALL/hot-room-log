"""CSV export and import."""

import csv
import io

from .calc import format_1, format_meas
from .db import export_rows, find_room_by_name, insert_reading, insert_room
from .validate import parse_name, parse_note, parse_rh, parse_temp, parse_time, format_taken_at

MSG_EMPTY = "The CSV file is empty."
MSG_CHOOSE = "Choose a CSV file to import."
MSG_UTF8 = "The file must be a UTF-8 CSV file."
MSG_TOO_MANY = "Too many rows (max 2000)."

REQUIRED = ("room", "taken_at", "temp_c", "rh_percent")
MAX_ROWS = 2000
MAX_ERRORS = 50


class ImportRejected(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def _enrich_export(row):
    from .calc import compute

    metrics = compute(row["temp_c"], row["rh_percent"])
    return [
        row["room_name"],
        row["taken_at"],
        format_meas(row["temp_c"]),
        format_meas(row["rh_percent"]),
        format_1(metrics["dew_point_c"]),
        format_1(metrics["humidex"]),
        metrics["band"],
        row["note"] or "",
    ]


def render_csv(conn, room_id=None):
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(
        ["room", "taken_at", "temp_c", "rh_percent", "dew_point_c", "humidex", "band", "note"]
    )
    for row in export_rows(conn, room_id=room_id):
        writer.writerow(_enrich_export(row))
    return b"\xef\xbb\xbf" + buffer.getvalue().encode("utf-8")


def _is_blank(row):
    return not row or all(not (cell or "").strip() for cell in row)


def _parse_table(text):
    stream = io.StringIO(text)
    reader = csv.reader(stream)
    records = []
    try:
        for row in reader:
            records.append((reader.line_num, row))
    except csv.Error as exc:
        raise ImportRejected(MSG_UTF8) from exc
    return records


def _header_map(header):
    found = {}
    for index, cell in enumerate(header):
        key = (cell or "").strip().casefold()
        if key and key not in found:
            found[key] = index
    return found


def _cell(row, index):
    if index is None or index >= len(row):
        return ""
    return row[index]


def import_csv(conn, raw, now=None):
    if raw is None or len(raw) == 0:
        raise ImportRejected(MSG_EMPTY)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ImportRejected(MSG_UTF8) from exc
    if text.strip() == "":
        raise ImportRejected(MSG_EMPTY)

    records = _parse_table(text)
    content = [(line, row) for line, row in records if not _is_blank(row)]
    if not content:
        raise ImportRejected(MSG_EMPTY)

    _header_line, header = content[0]
    columns = _header_map(header)
    missing = [name for name in REQUIRED if name not in columns]
    if missing:
        raise ImportRejected("Missing column(s): " + ", ".join(missing))

    data_rows = content[1:]
    if len(data_rows) > MAX_ROWS:
        raise ImportRejected(MSG_TOO_MANY)

    note_index = columns.get("note")
    added = 0
    new_rooms = 0
    duplicates = 0
    invalid = 0
    errors = []

    rooms = {
        room["name"].strip().casefold(): room
        for room in conn.execute("SELECT * FROM rooms").fetchall()
    }
    seen = set()
    for row in conn.execute(
        "SELECT room_id, taken_at, temp_c, rh_percent FROM readings"
    ):
        seen.add(
            (
                row["room_id"],
                row["taken_at"],
                format_meas(row["temp_c"]),
                format_meas(row["rh_percent"]),
            )
        )

    conn.execute("BEGIN")
    try:
        for line_no, row in data_rows:
            room_raw = _cell(row, columns["room"])
            time_raw = _cell(row, columns["taken_at"])
            temp_raw = _cell(row, columns["temp_c"])
            rh_raw = _cell(row, columns["rh_percent"])
            note_raw = _cell(row, note_index) if note_index is not None else None

            name, name_error = parse_name(room_raw)
            if name_error:
                invalid += 1
                errors.append(f"Row {line_no}: {name_error}")
                continue
            taken, time_error = parse_time(time_raw, now=now)
            if time_error:
                invalid += 1
                errors.append(f"Row {line_no}: {time_error}")
                continue
            temp, temp_error = parse_temp(temp_raw)
            if temp_error:
                invalid += 1
                errors.append(f"Row {line_no}: {temp_error}")
                continue
            humidity, rh_error = parse_rh(rh_raw)
            if rh_error:
                invalid += 1
                errors.append(f"Row {line_no}: {rh_error}")
                continue
            note, note_error = parse_note(note_raw)
            if note_error:
                invalid += 1
                errors.append(f"Row {line_no}: {note_error}")
                continue

            key_name = name.casefold()
            room = rooms.get(key_name)
            if room is None:
                # Re-check the database in case the cache missed a match.
                existing = find_room_by_name(conn, name)
                if existing is None:
                    room_id = insert_room(conn, name, is_sample=0)
                    room = {"id": room_id, "name": name, "is_sample": 0}
                    new_rooms += 1
                else:
                    room = existing
                rooms[key_name] = room

            taken_at = format_taken_at(taken)
            signature = (room["id"], taken_at, format_meas(temp), format_meas(humidity))
            if signature in seen:
                duplicates += 1
                continue
            insert_reading(conn, room["id"], taken_at, temp, humidity, note)
            seen.add(signature)
            added += 1
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise

    extra = 0
    shown = errors
    if len(errors) > MAX_ERRORS:
        extra = len(errors) - MAX_ERRORS
        shown = errors[:MAX_ERRORS]
    return {
        "added": added,
        "new_rooms": new_rooms,
        "duplicates": duplicates,
        "invalid": invalid,
        "errors": shown,
        "extra": extra,
    }
