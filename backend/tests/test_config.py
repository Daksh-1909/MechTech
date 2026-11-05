from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import PROJECT_ROOT, Settings


def test_invalid_app_env_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(app_env="staging")


def test_invalid_log_level_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(log_level="LOUD")


def test_log_level_is_normalized() -> None:
    settings = Settings(log_level="debug")
    assert settings.log_level == "DEBUG"


def test_relative_sqlite_path_is_resolved_under_project_root() -> None:
    settings = Settings(database_url="sqlite:///./data/db/test.db")
    expected = (PROJECT_ROOT / "data" / "db" / "test.db").resolve().as_posix()

    assert settings.database_url == f"sqlite:///{expected}"


def test_absolute_sqlite_path_is_preserved(tmp_path: Path) -> None:
    database_path = tmp_path / "isolated.db"
    settings = Settings(database_url=f"sqlite:///{database_path.as_posix()}")

    assert settings.database_url == f"sqlite:///{database_path.as_posix()}"


def test_relative_data_root_is_resolved_under_project_root() -> None:
    settings = Settings(data_root="./data")

    assert settings.data_root == (PROJECT_ROOT / "data").resolve()
