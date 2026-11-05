from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


def list_users(db: Session, *, limit: int, offset: int) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id.asc()).limit(limit).offset(offset)))


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))
