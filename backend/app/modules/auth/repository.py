from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models import User, UserRole, UserSession


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def create_user_record(
    db: Session,
    *,
    name: str,
    email: str,
    password_hash: str,
    role: UserRole,
) -> User:
    user = User(
        name=name,
        email=email,
        password_hash=password_hash,
        role=role.value,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def admin_exists(db: Session) -> bool:
    count = db.scalar(
        select(func.count()).select_from(User).where(User.role == UserRole.ADMIN.value)
    )
    return bool(count)


def create_session_record(
    db: Session,
    *,
    user_id: int,
    token_hash: str,
    csrf_token_hash: str,
    expires_at: datetime,
    user_agent_summary: str | None,
) -> UserSession:
    session = UserSession(
        user_id=user_id,
        token_hash=token_hash,
        csrf_token_hash=csrf_token_hash,
        expires_at=expires_at,
        user_agent_summary=user_agent_summary,
    )
    db.add(session)
    db.flush()
    return session


def get_session_by_token_hash(db: Session, token_hash: str) -> UserSession | None:
    return db.scalar(select(UserSession).where(UserSession.token_hash == token_hash))


def list_sessions_for_user(db: Session, user_id: int) -> list[UserSession]:
    return list(
        db.scalars(
            select(UserSession)
            .where(UserSession.user_id == user_id)
            .order_by(UserSession.created_at.desc())
        )
    )


def get_session_for_user(db: Session, *, session_id: int, user_id: int) -> UserSession | None:
    return db.scalar(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == user_id,
        )
    )


def revoke_other_sessions(
    db: Session,
    *,
    user_id: int,
    except_session_id: int,
    revoked_at: datetime,
) -> None:
    db.execute(
        update(UserSession)
        .where(
            UserSession.user_id == user_id,
            UserSession.id != except_session_id,
            UserSession.revoked_at.is_(None),
        )
        .values(revoked_at=revoked_at)
    )


def revoke_all_sessions(
    db: Session,
    *,
    user_id: int,
    revoked_at: datetime,
) -> None:
    db.execute(
        update(UserSession)
        .where(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
        )
        .values(revoked_at=revoked_at)
    )
