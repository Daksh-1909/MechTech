import json
import logging
import re
from contextvars import ContextVar, Token
from datetime import UTC, datetime

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)

_SENSITIVE_FIELD = re.compile(
    r"(?i)(password|passwd|token|secret|api[_-]?key|cookie|authorization)"
    r"([\"']?\s*[:=]\s*[\"']?)([^\"'\s,;}]+)"
)
_BEARER_TOKEN = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+")


def set_request_id(value: str) -> Token[str | None]:
    return _request_id.set(value)


def reset_request_id(token: Token[str | None]) -> None:
    _request_id.reset(token)


def get_request_id() -> str | None:
    return _request_id.get()


def redact_log_text(value: str) -> str:
    redacted = _BEARER_TOKEN.sub(r"\1[redacted]", value)
    return _SENSITIVE_FIELD.sub(r"\1\2[redacted]", redacted)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return redact_log_text(json.dumps(payload, ensure_ascii=True, default=str))


def configure_logging(level: str) -> None:
    root = logging.getLogger()
    root.setLevel(level)

    if any(getattr(handler, "_mechtech_handler", False) for handler in root.handlers):
        return

    handler = logging.StreamHandler()
    handler._mechtech_handler = True  # type: ignore[attr-defined]
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
