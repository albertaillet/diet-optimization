#!/usr/bin/env -S uv run
"""Script to view per-distribution install sizes on disk."""

import argparse
import importlib.metadata as im
import operator
from pathlib import Path

from packaging.utils import canonicalize_name


def humanize(n: int) -> str:
    """Convert a byte count into a human-readable string."""
    units = ("B", "KB", "MB", "GB", "TB")
    i = 0
    size = float(n)
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.1f} {units[i]}"


def dist_size_bytes(d: im.Distribution, include_metadata: bool) -> int | None:
    """Sum byte sizes of files listed by the distribution.

    Returns None if file listing is unavailable.
    """
    files = d.files
    if files is None:
        return None
    base = Path(d.locate_file("."))  # type: ignore
    total = 0
    for rel in files:
        p = base / rel
        if not include_metadata and any(part.endswith((".dist-info", ".egg-info")) for part in p.parts):
            continue
        if p.is_file():
            total += p.stat().st_size
    return total


def get_all_installed_packages(include_metadata: bool) -> list[tuple[str, int, list[str]]]:
    """Get sizes for all installed packages."""
    rows: list[tuple[str, int, list[str]]] = []
    for dist in im.distributions():
        meta_name = dist.metadata.get("Name") or getattr(dist, "_normalized_name", None) or "unknown"
        name = canonicalize_name(meta_name)
        size = dist_size_bytes(dist, include_metadata)
        if size is None:
            note = ["editable or no RECORD"]
            size = 0
        else:
            note = []
        rows.append((name, size, note))
    return rows


def main(include_metadata: bool = False) -> None:
    rows = get_all_installed_packages(include_metadata)
    if not rows:
        print("No distributions found.")
        return

    width = max(len(name) for name, _, _ in rows)
    print(f"{'target'.ljust(width)}  size (installed)")
    print("-" * width + "  ---------------")
    for name, size, _ in sorted(rows, key=operator.itemgetter(1), reverse=True):
        print(f"{name.ljust(width)}  {humanize(size)}")

    notes = [(name, note) for name, _, note in rows if note]
    if notes:
        print("\nNotes:")
        for name, note in notes:
            print(f"  - {name}: skipped ({note})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Show installed package sizes.")
    parser.add_argument("--include-metadata", action="store_true", help="Include *.dist-info/*.egg-info in size totals.")
    args = parser.parse_args()
    main(include_metadata=args.include_metadata)
