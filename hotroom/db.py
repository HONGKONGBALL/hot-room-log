"""SQLite schema, sample seed and queries."""

import os
import sqlite3
from datetime import datetime

from flask import g, current_app

SEED_ROOMS = (
    (1, "Demo Estate Study Room"),
    (2, "Demo Classroom 3F"),
    (3, "Demo Library Corner"),
)

# id, room_id, taken_at, temp_c, rh_percent, note
SEED_READINGS = (
    (1, 1, "2026-09-14 10:00", 29, 78, None),
    (2, 1, "2026-09-14 15:00", 32, 68, None),
    (3, 1, "2026-09-15 10:00", 29.5, 76, None),
    (4, 1, "2026-09-15 15:00", 33, 66, "Fan on, windows open"),
    (5, 1, "2026-09-16 10:00", 30, 75, None),
    (6, 1, "2026-09-16 15:00", 34, 65, None),
    (7, 2, "2026-09-14 10:00", 26, 60, None),
    (8, 2, "2026-09-14 15:00", 28, 63, None),
    (9, 2, "2026-09-15 10:00", 26.5, 62, None),
    (10, 2, "2026-09-15 15:00", 30, 68, "Full class after lunch"),
    (11, 2, "2026-09-16 10:00", 26, 58, None),
    (12, 2, "2026-09-16 15:00", 28, 60, None),
    (13, 3, "2026-09-14 10:00", 23.5, 55, None),
    (14, 3, "2026-09-14 15:00", 24, 58, None),
    (15, 3, "2026-09-15 10:00", 23, 60, None),
    (16, 3, "2026-09-15 15:00", 24.5, 55, None),
    (17, 3, "2026-09-16 10:00", 23.5, 52, None),
    (18, 3, "2026-09-16 15:00", 25, 50, None),
)


def timestamp(moment=None):
    moment = moment or datetime.now()
    return moment.strftime("%Y-%m-%d %H:%M:%S")


def connect(path):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(conn):
    conn.execute(
        """
        CREATE TABLE rooms (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            is_sample INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE readings (
            id INTEGER PRIMARY KEY,
            room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
            taken_at TEXT NOT NULL,
            temp_c REAL NOT NULL,
            rh_percent REAL NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL
        )
        """
    )


def seed(conn):
    created = "2026-09-14 08:00:00"
    conn.execute("BEGIN")
    try:
        conn.executemany(
            "INSERT INTO rooms (id, name, is_sample, created_at) VALUES (?, ?, 1, ?)",
            [(room_id, name, created) for room_id, name in SEED_ROOMS],
        )
        conn.executemany(
            """
            INSERT INTO readings
                (id, room_id, taken_at, temp_c, rh_percent, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (rid, room_id, taken_at, temp, rh, note, created)
                for rid, room_id, taken_at, temp, rh, note in SEED_READINGS
            ],
        )
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def init_database(path):
    """Create and seed the database only when it has no tables."""
    conn = connect(path)
    try:
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'rooms'"
        ).fetchone()
        if exists is None:
            create_schema(conn)
            seed(conn)
    finally:
        conn.close()


def reset_database(conn):
    conn.execute("BEGIN")
    try:
        conn.execute("DROP TABLE IF EXISTS readings")
        conn.execute("DROP TABLE IF EXISTS rooms")
        create_schema(conn)
        # seed() starts its own transaction; commit the schema first.
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    seed(conn)


def get_db():
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE"])
    return g.db


def close_db(_error=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def list_rooms(conn):
    return conn.execute("SELECT * FROM rooms ORDER BY id").fetchall()


def get_room(conn, room_id):
    return conn.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()


def find_room_by_name(conn, name):
    target = name.strip().casefold()
    for room in list_rooms(conn):
        if room["name"].strip().casefold() == target:
            return room
    return None


def list_readings(conn, room_id):
    return conn.execute(
        """
        SELECT * FROM readings
        WHERE room_id = ?
        ORDER BY taken_at ASC, id ASC
        """,
        (room_id,),
    ).fetchall()


def get_reading(conn, reading_id):
    return conn.execute(
        "SELECT * FROM readings WHERE id = ?", (reading_id,)
    ).fetchone()


def insert_room(conn, name, is_sample=0):
    cursor = conn.execute(
        "INSERT INTO rooms (name, is_sample, created_at) VALUES (?, ?, ?)",
        (name, 1 if is_sample else 0, timestamp()),
    )
    return cursor.lastrowid


def insert_reading(conn, room_id, taken_at, temp_c, rh_percent, note):
    cursor = conn.execute(
        """
        INSERT INTO readings (room_id, taken_at, temp_c, rh_percent, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (room_id, taken_at, temp_c, rh_percent, note, timestamp()),
    )
    return cursor.lastrowid


def delete_reading(conn, reading_id):
    conn.execute("DELETE FROM readings WHERE id = ?", (reading_id,))


def delete_room(conn, room_id):
    conn.execute("DELETE FROM readings WHERE room_id = ?", (room_id,))
    conn.execute("DELETE FROM rooms WHERE id = ?", (room_id,))


def export_rows(conn, room_id=None):
    sql = """
        SELECT rooms.name AS room_name,
               readings.id AS id,
               readings.room_id AS room_id,
               readings.taken_at AS taken_at,
               readings.temp_c AS temp_c,
               readings.rh_percent AS rh_percent,
               readings.note AS note
        FROM readings
        JOIN rooms ON rooms.id = readings.room_id
    """
    params = ()
    if room_id is not None:
        sql += " WHERE readings.room_id = ?"
        params = (room_id,)
    sql += " ORDER BY rooms.id ASC, readings.taken_at ASC, readings.id ASC"
    return conn.execute(sql, params).fetchall()
