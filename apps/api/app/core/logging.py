from __future__ import annotations

import logging
import re


PII_PATTERNS = [
    re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b"),
    re.compile(r"\b\d{10}\b"),
]


class PiiRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            message = record.msg
            for pattern in PII_PATTERNS:
                message = pattern.sub("[redacted]", message)
            record.msg = message
        return True


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    root = logging.getLogger()
    for handler in root.handlers:
        handler.addFilter(PiiRedactionFilter())
