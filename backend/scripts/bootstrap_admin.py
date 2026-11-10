"""Create the first administrator account.

Runs only when no administrator exists. The password is read with getpass and
never passed on the command line or stored in plaintext.
"""

import argparse
import getpass
import sys

from pydantic import EmailStr, TypeAdapter, ValidationError

from app.core.exceptions import AppError
from app.core.security import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH
from app.db.session import SessionLocal
from app.modules.audit import service as audit_service
from app.modules.audit.actions import AuditAction
from app.modules.auth import service

_email_adapter = TypeAdapter(EmailStr)


def _prompt_email() -> str:
    raw_email = input("Administrator email: ").strip()
    try:
        return str(_email_adapter.validate_python(raw_email))
    except ValidationError:
        print("Invalid email address.", file=sys.stderr)
        raise SystemExit(1) from None


def _prompt_password() -> str:
    password = getpass.getpass("Password: ")
    confirmation = getpass.getpass("Confirm password: ")

    if password != confirmation:
        print("Passwords do not match.", file=sys.stderr)
        raise SystemExit(1)

    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        print(
            f"Password must be between {MIN_PASSWORD_LENGTH} and {MAX_PASSWORD_LENGTH} characters.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    return password


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap the first MechTech administrator.")
    parser.add_argument("--name", help="Administrator display name.")
    parser.add_argument("--email", help="Administrator email address.")
    args = parser.parse_args()

    name = (args.name or input("Administrator name: ")).strip()
    if not name:
        print("Administrator name is required.", file=sys.stderr)
        return 1

    if args.email:
        try:
            email = str(_email_adapter.validate_python(args.email))
        except ValidationError:
            print("Invalid email address.", file=sys.stderr)
            return 1
    else:
        email = _prompt_email()

    password = _prompt_password()

    with SessionLocal() as db:
        try:
            user = service.create_initial_admin(
                db,
                name=name,
                email=email,
                password=password,
            )
            audit_service.record_event(
                db,
                action=AuditAction.USER_CREATED,
                resource_type="user",
                resource_id=user.id,
                metadata={"role": "platform_admin", "bootstrap": True},
            )
            db.commit()
        except AppError as exc:
            print(exc.message, file=sys.stderr)
            return 1

    print(f"Administrator created: {user.email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
