import re
from contextlib import contextmanager
from datetime import datetime, UTC
from typing import Any, Iterator

import mysql.connector


DB_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


def _base_connection_config(db_config: dict[str, Any]) -> dict[str, Any]:
    return {
        "host": str(db_config["host"]),
        "port": int(db_config["port"]),
        "user": str(db_config["user"]),
        "password": str(db_config["password"]),
        "charset": str(db_config.get("charset", "utf8mb4")),
    }


def _validate_database_name(db_name: str) -> str:
    if not DB_NAME_PATTERN.fullmatch(db_name):
        raise RuntimeError("DB_NAME faqat harf, raqam va `_` belgisidan iborat bo'lishi kerak.")
    return db_name


@contextmanager
def _connect(db_config: dict[str, Any]) -> Iterator[mysql.connector.MySQLConnection]:
    connection = mysql.connector.connect(
        **_base_connection_config(db_config),
        database=str(db_config["database"]),
        autocommit=True,
    )
    try:
        yield connection
    finally:
        connection.close()


def init_db(db_config: dict[str, Any]) -> None:
    db_name = _validate_database_name(str(db_config["database"]))

    server_connection = mysql.connector.connect(
        **_base_connection_config(db_config),
        autocommit=True,
    )
    try:
        cursor = server_connection.cursor()
        try:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        finally:
            cursor.close()
    finally:
        server_connection.close()

    with _connect(db_config) as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id BIGINT PRIMARY KEY,
                language VARCHAR(10) NOT NULL,
                updated_at DATETIME NOT NULL
            )
            ENGINE=InnoDB
            DEFAULT CHARSET=utf8mb4
            COLLATE=utf8mb4_unicode_ci
            """
            )
            cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                user_id BIGINT NOT NULL,
                event_name VARCHAR(100) NOT NULL,
                language VARCHAR(10) NOT NULL,
                created_at DATETIME NOT NULL,
                INDEX idx_events_user_id (user_id),
                INDEX idx_events_event_name (event_name)
            )
            ENGINE=InnoDB
            DEFAULT CHARSET=utf8mb4
            COLLATE=utf8mb4_unicode_ci
            """
            )
        finally:
            cursor.close()


def get_user_language(db_config: dict[str, Any], user_id: int) -> str | None:
    with _connect(db_config) as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT language FROM user_preferences WHERE user_id = %s",
                (user_id,),
            )
            row = cursor.fetchone()
        finally:
            cursor.close()

    if row is None:
        return None
    return str(row["language"])


def save_user_language(db_config: dict[str, Any], user_id: int, language: str) -> None:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    with _connect(db_config) as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
            """
            INSERT INTO user_preferences (user_id, language, updated_at)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                language = VALUES(language),
                updated_at = VALUES(updated_at)
            """,
            (user_id, language, timestamp),
            )
        finally:
            cursor.close()


def log_event(db_config: dict[str, Any], user_id: int, event_name: str, language: str) -> None:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    with _connect(db_config) as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
            """
            INSERT INTO events (user_id, event_name, language, created_at)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, event_name, language, timestamp),
            )
        finally:
            cursor.close()


def get_stats(db_config: dict[str, Any]) -> dict[str, object]:
    with _connect(db_config) as connection:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT COUNT(*) AS count FROM user_preferences")
            users_count = cursor.fetchone()["count"]
            cursor.execute(
            """
            SELECT language, COUNT(*) AS count
            FROM user_preferences
            GROUP BY language
            ORDER BY count DESC, language ASC
            """
            )
            language_rows = cursor.fetchall()
            cursor.execute(
            """
            SELECT event_name, COUNT(*) AS count
            FROM events
            GROUP BY event_name
            ORDER BY count DESC, event_name ASC
            """
            )
            event_rows = cursor.fetchall()
        finally:
            cursor.close()

    return {
        "users_count": int(users_count),
        "languages": [(str(row["language"]), int(row["count"])) for row in language_rows],
        "events": [(str(row["event_name"]), int(row["count"])) for row in event_rows],
    }
