# ==================================================
# SMART ROAD DIGITAL TWIN - SQLITE DATABASE
# ==================================================

import csv
import sqlite3
from datetime import datetime
from pathlib import Path


DATABASE_FOLDER = Path(__file__).resolve().parent
DATABASE_PATH = DATABASE_FOLDER / "smart_road.db"
EXPORT_FOLDER = DATABASE_FOLDER / "exports"

DATABASE_TIMEOUT = 10


def get_connection():
    """
    Create and return a configured SQLite connection.
    """

    DATABASE_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=DATABASE_TIMEOUT,
    )

    return connection


def create_database():
    """
    Create the potholes table and safely migrate
    older database versions.
    """

    DATABASE_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    EXPORT_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS potholes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pothole_id INTEGER NOT NULL UNIQUE,
                x INTEGER NOT NULL,
                y INTEGER NOT NULL,
                depth REAL NOT NULL,
                severity TEXT NOT NULL,
                latitude REAL DEFAULT 0.0,
                longitude REAL DEFAULT 0.0,
                photo_captured INTEGER DEFAULT 0,
                image_path TEXT DEFAULT '',
                detected_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            PRAGMA table_info(potholes)
            """
        )

        existing_columns = {
            row[1]
            for row in cursor.fetchall()
        }

        if "latitude" not in existing_columns:
            cursor.execute(
                """
                ALTER TABLE potholes
                ADD COLUMN latitude REAL DEFAULT 0.0
                """
            )

        if "longitude" not in existing_columns:
            cursor.execute(
                """
                ALTER TABLE potholes
                ADD COLUMN longitude REAL DEFAULT 0.0
                """
            )

        if "photo_captured" not in existing_columns:
            cursor.execute(
                """
                ALTER TABLE potholes
                ADD COLUMN photo_captured INTEGER DEFAULT 0
                """
            )

        if "image_path" not in existing_columns:
            cursor.execute(
                """
                ALTER TABLE potholes
                ADD COLUMN image_path TEXT DEFAULT ''
                """
            )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            index_potholes_detected_at
            ON potholes(detected_at)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            index_potholes_severity
            ON potholes(severity)
            """
        )

        connection.commit()


def save_pothole(
    pothole_id,
    x,
    y,
    depth,
    severity,
    latitude=0.0,
    longitude=0.0,
    photo_captured=False,
    image_path="",
):
    """
    Save one detected pothole without creating duplicates.

    Returns:
        True when a new pothole is inserted.
        False when the pothole already exists.
    """

    create_database()

    detected_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    safe_image_path = ""

    if image_path:
        safe_image_path = str(image_path)

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT OR IGNORE INTO potholes (
                pothole_id,
                x,
                y,
                depth,
                severity,
                latitude,
                longitude,
                photo_captured,
                image_path,
                detected_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(pothole_id),
                int(x),
                int(y),
                float(depth),
                str(severity).upper(),
                float(latitude),
                float(longitude),
                int(bool(photo_captured)),
                safe_image_path,
                detected_at,
            ),
        )

        connection.commit()

        return cursor.rowcount > 0


def update_pothole_image(
    pothole_id,
    image_path,
):
    """
    Update a stored pothole after an image is captured.

    Returns:
        True when the pothole record is updated.
        False when the pothole ID does not exist.
    """

    create_database()

    if not image_path:
        return False

    safe_image_path = str(image_path)

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE potholes
            SET
                photo_captured = 1,
                image_path = ?
            WHERE pothole_id = ?
            """,
            (
                safe_image_path,
                int(pothole_id),
            ),
        )

        connection.commit()

        return cursor.rowcount > 0


def remove_pothole_image(pothole_id):
    """
    Remove the stored image information for one pothole.
    """

    create_database()

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE potholes
            SET
                photo_captured = 0,
                image_path = ''
            WHERE pothole_id = ?
            """,
            (int(pothole_id),),
        )

        connection.commit()

        return cursor.rowcount > 0


def get_all_potholes():
    """
    Return all stored potholes, newest first.
    """

    create_database()

    with get_connection() as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM potholes
            ORDER BY id DESC
            """
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]


def get_recent_potholes(limit=20):
    """
    Return a limited number of recent potholes.
    """

    create_database()

    safe_limit = max(
        1,
        int(limit),
    )

    with get_connection() as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM potholes
            ORDER BY id DESC
            LIMIT ?
            """,
            (safe_limit,),
        )

        return [
            dict(row)
            for row in cursor.fetchall()
        ]


def get_pothole_by_id(pothole_id):
    """
    Return one pothole using its pothole ID.
    """

    create_database()

    with get_connection() as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM potholes
            WHERE pothole_id = ?
            """,
            (int(pothole_id),),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return dict(row)


def get_pothole_count():
    """
    Return the total number of stored potholes.
    """

    create_database()

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM potholes
            """
        )

        result = cursor.fetchone()

        return int(result[0] or 0)


def get_statistics():
    """
    Return pothole statistics for dashboard panels.
    """

    create_database()

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total,

                SUM(
                    CASE
                        WHEN UPPER(severity) = 'HIGH'
                        THEN 1
                        ELSE 0
                    END
                ) AS high_count,

                SUM(
                    CASE
                        WHEN UPPER(severity) = 'MEDIUM'
                        THEN 1
                        ELSE 0
                    END
                ) AS medium_count,

                SUM(
                    CASE
                        WHEN UPPER(severity) = 'LOW'
                        THEN 1
                        ELSE 0
                    END
                ) AS low_count,

                COALESCE(
                    AVG(depth),
                    0
                ) AS average_depth,

                COALESCE(
                    MAX(depth),
                    0
                ) AS maximum_depth,

                SUM(
                    CASE
                        WHEN photo_captured = 1
                        THEN 1
                        ELSE 0
                    END
                ) AS photo_count

            FROM potholes
            """
        )

        result = cursor.fetchone()

        return {
            "total": int(result[0] or 0),
            "high": int(result[1] or 0),
            "medium": int(result[2] or 0),
            "low": int(result[3] or 0),
            "average_depth": round(
                float(result[4] or 0),
                2,
            ),
            "maximum_depth": round(
                float(result[5] or 0),
                2,
            ),
            "photos": int(result[6] or 0),
        }


def export_to_csv():
    """
    Export all pothole records to a timestamped CSV file.

    Returns:
        Exported CSV Path object.
        None when no records exist.
    """

    records = get_all_potholes()

    if not records:
        return None

    EXPORT_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    export_path = (
        EXPORT_FOLDER
        / f"pothole_report_{timestamp}.csv"
    )

    fieldnames = [
        "id",
        "pothole_id",
        "x",
        "y",
        "depth",
        "severity",
        "latitude",
        "longitude",
        "photo_captured",
        "image_path",
        "detected_at",
    ]

    with export_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(records)

    return export_path


def clear_database():
    """
    Delete all pothole records and reset database IDs.
    """

    create_database()

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM potholes
            """
        )

        cursor.execute(
            """
            DELETE FROM sqlite_sequence
            WHERE name = 'potholes'
            """
        )

        connection.commit()


create_database()