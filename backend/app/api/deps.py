from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import get_db

__all__ = ["get_db", "DbSession"]


def db_session() -> Generator[Session]:
    yield from get_db()


DbSession = Session
