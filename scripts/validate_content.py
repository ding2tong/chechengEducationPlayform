"""Validate the metadata contract for managed Markdown content."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

REQUIRED_FIELDS = {
    "title",
    "category",
    "tags",
    "status",
    "author",
    "reviewer",
    "created_at",
    "updated_at",
    "reviewed_at",
    "next_review",
    "evidence_level",
    "references",
}
ALLOWED_STATUSES = {"draft", "review", "approved", "published", "archived"}
DATE_FIELDS = {"created_at", "updated_at", "reviewed_at", "next_review"}
FRONT_MATTER = re.compile(
    r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL
)


def load_allowed_values(path: Path, key: str) -> set[str]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    values = data.get(key, [])
    if key == "categories":
        return {item["id"] for item in values}
    return set(values)


def read_front_matter(path: Path) -> dict[str, Any] | None:
    match = FRONT_MATTER.match(path.read_text(encoding="utf-8"))
    if not match:
        return None
    metadata = yaml.safe_load(match.group(1)) or {}
    if not isinstance(metadata, dict):
        raise ValueError("Front Matter must be a YAML mapping")
    return metadata


def validate_date(path: Path, field: str, value: Any, errors: list[str]) -> None:
    if value in (None, ""):
        return
    if isinstance(value, date):
        return
    try:
        date.fromisoformat(str(value))
    except ValueError:
        errors.append(f"{path}: {field} must use YYYY-MM-DD")


def validate_page(
    path: Path, categories: set[str], tags: set[str], errors: list[str]
) -> None:
    try:
        metadata = read_front_matter(path)
    except (ValueError, yaml.YAMLError) as error:
        errors.append(f"{path}: invalid Front Matter ({error})")
        return

    if metadata is None or "status" not in metadata:
        return

    missing = REQUIRED_FIELDS - metadata.keys()
    if missing:
        errors.append(f"{path}: missing fields: {', '.join(sorted(missing))}")
        return

    if metadata["status"] not in ALLOWED_STATUSES:
        errors.append(f"{path}: invalid status {metadata['status']!r}")
    if metadata["category"] not in categories:
        errors.append(f"{path}: unknown category {metadata['category']!r}")
    if not isinstance(metadata["tags"], list):
        errors.append(f"{path}: tags must be a list")
    else:
        unknown_tags = set(metadata["tags"]) - tags
        if unknown_tags:
            errors.append(f"{path}: unknown tags: {', '.join(sorted(unknown_tags))}")
    if not isinstance(metadata["references"], list):
        errors.append(f"{path}: references must be a list")
    for field in DATE_FIELDS:
        validate_date(path, field, metadata[field], errors)

    if metadata["status"] == "published":
        for field in ("reviewer", "reviewed_at", "next_review", "evidence_level"):
            if not metadata[field]:
                errors.append(f"{path}: published content requires {field}")
        if not metadata["references"]:
            errors.append(f"{path}: published content requires at least one reference")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs", type=Path, default=Path("docs"))
    parser.add_argument("--data", type=Path, default=Path("data"))
    args = parser.parse_args()

    categories = load_allowed_values(args.data / "categories.yaml", "categories")
    tags = load_allowed_values(args.data / "tags.yaml", "tags")
    errors: list[str] = []
    for path in sorted(args.docs.rglob("*.md")):
        validate_page(path, categories, tags, errors)

    if errors:
        print("Content validation failed:", file=sys.stderr)
        print("\\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print("Content validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
