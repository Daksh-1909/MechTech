import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.db.session import engine


def test_sqlite_foreign_keys_are_enforced() -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE fk_parent (id INTEGER PRIMARY KEY)"))
        connection.execute(
            text(
                "CREATE TABLE fk_child ("
                "id INTEGER PRIMARY KEY, "
                "parent_id INTEGER NOT NULL REFERENCES fk_parent(id)"
                ")"
            )
        )

    try:
        with pytest.raises(IntegrityError), engine.begin() as connection:
            connection.execute(text("INSERT INTO fk_child (id, parent_id) VALUES (1, 999)"))
    finally:
        with engine.begin() as connection:
            connection.execute(text("DROP TABLE IF EXISTS fk_child"))
            connection.execute(text("DROP TABLE IF EXISTS fk_parent"))


def test_sqlite_wal_mode_is_enabled() -> None:
    with engine.connect() as connection:
        mode = connection.execute(text("PRAGMA journal_mode")).scalar_one()

    assert str(mode).lower() == "wal"
