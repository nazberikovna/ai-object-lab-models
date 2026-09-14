#!/usr/bin/env python3
"""Validate catalog paths, sizes, required fields, and GLB headers."""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog" / "catalog.json"


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(1)


def main() -> None:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if catalog.get("schema_version") != "1.0":
        fail("unsupported schema_version")

    ids: set[str] = set()
    aliases: dict[str, str] = {}
    required = {"id", "titles", "aliases", "file", "capabilities", "accuracy_note", "provenance"}

    for item in catalog.get("models", []):
        missing = required - item.keys()
        if missing:
            fail(f"{item.get('id', '<unknown>')}: missing {sorted(missing)}")
        model_id = item["id"]
        if model_id in ids:
            fail(f"duplicate id: {model_id}")
        ids.add(model_id)

        path = ROOT / item["file"]
        if not path.is_file():
            fail(f"{model_id}: file not found: {item['file']}")
        actual_size = path.stat().st_size
        if actual_size != item.get("bytes"):
            fail(f"{model_id}: bytes is {item.get('bytes')}, actual size is {actual_size}")
        if actual_size > 15 * 1024 * 1024:
            fail(f"{model_id}: exceeds the 15 MiB classroom target")

        with path.open("rb") as handle:
            magic, version, declared_length = struct.unpack("<4sII", handle.read(12))
        if magic != b"glTF" or version != 2 or declared_length != actual_size:
            fail(f"{model_id}: invalid GLB v2 header")

        for alias in item["aliases"]:
            key = alias.casefold().strip()
            if key in aliases and aliases[key] != model_id:
                fail(f"alias {alias!r} is shared by {aliases[key]} and {model_id}")
            aliases[key] = model_id

        provenance = item["provenance"]
        for field in ("title", "author", "source_url", "license", "license_url"):
            if not provenance.get(field):
                fail(f"{model_id}: missing provenance.{field}")

    if not ids:
        fail("catalog contains no models")
    print(f"OK: {len(ids)} models, {len(aliases)} aliases, all files valid")


if __name__ == "__main__":
    main()
