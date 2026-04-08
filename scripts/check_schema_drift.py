from __future__ import annotations

import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("DATABASE_URL", "sqlite:///./schema_drift.db")
sys.path.insert(0, str(ROOT / "apps/api"))

from app.db.models import Analysis, AudioJob, AuditLog, EventLog, ExtractedParam, Feedback, Report, User  # noqa: E402
from app.db.session import Base  # noqa: E402


MODEL_TO_TABLE = {
    "User": "users",
    "Report": "reports",
    "ExtractedParam": "extracted_params",
    "Analysis": "analyses",
    "AudioJob": "audio_jobs",
    "AuditLog": "audit_logs",
    "Feedback": "feedback",
    "EventLog": "event_logs",
}

PRISMA_SCALARS = {
    "String": "string",
    "Int": "integer",
    "Float": "float",
    "Boolean": "boolean",
    "DateTime": "datetime",
    "Json": "json",
}

SQLA_TYPES = {
    "VARCHAR": "string",
    "TEXT": "string",
    "INTEGER": "integer",
    "FLOAT": "float",
    "BOOLEAN": "boolean",
    "DATETIME": "datetime",
    "JSON": "json",
}


def parse_prisma_schema(path: Path) -> dict[str, dict[str, str]]:
    source = path.read_text(encoding="utf-8")
    model_pattern = re.compile(r"model\s+(\w+)\s+\{([^}]*)\}", re.MULTILINE | re.DOTALL)
    parsed: dict[str, dict[str, str]] = {}
    for model_name, body in model_pattern.findall(source):
        fields: dict[str, str] = {}
        for line in body.splitlines():
            clean = line.strip()
            if not clean or clean.startswith("//"):
                continue
            parts = clean.split()
            if len(parts) < 2:
                continue
            field_name, field_type = parts[0], parts[1].rstrip("?[]")
            if field_type in PRISMA_SCALARS:
                fields[field_name] = PRISMA_SCALARS[field_type]
        parsed[model_name] = fields
    return parsed


def parse_sqla_metadata() -> dict[str, dict[str, str]]:
    parsed: dict[str, dict[str, str]] = {}
    for model_name, table_name in MODEL_TO_TABLE.items():
        table = Base.metadata.tables[table_name]
        columns: dict[str, str] = {}
        for column in table.columns:
            key = str(column.type).upper().split("(")[0]
            columns[column.name] = SQLA_TYPES.get(key, key.lower())
        parsed[model_name] = columns
    return parsed


def main() -> int:
    prisma = parse_prisma_schema(ROOT / "apps/api/prisma/schema.prisma")
    sqla = parse_sqla_metadata()
    failures: list[str] = []

    for model_name, prisma_fields in prisma.items():
      sqla_fields = sqla.get(model_name)
      if sqla_fields is None:
          failures.append(f"Missing SQLAlchemy mapping for Prisma model {model_name}")
          continue
      missing_in_sqla = sorted(set(prisma_fields) - set(sqla_fields))
      missing_in_prisma = sorted(set(sqla_fields) - set(prisma_fields))
      if missing_in_sqla:
          failures.append(f"{model_name}: fields missing in SQLAlchemy -> {', '.join(missing_in_sqla)}")
      if missing_in_prisma:
          failures.append(f"{model_name}: fields missing in Prisma -> {', '.join(missing_in_prisma)}")
      for field, prisma_type in prisma_fields.items():
          sqla_type = sqla_fields.get(field)
          if sqla_type and sqla_type != prisma_type:
              failures.append(f"{model_name}.{field}: Prisma={prisma_type} SQLAlchemy={sqla_type}")

    if failures:
        print("Schema drift detected:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Prisma and SQLAlchemy schemas are aligned.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
