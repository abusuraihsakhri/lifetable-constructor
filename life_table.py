"""Abridged period life tables from age-specific central death rates.

Input ages are interval lower bounds. All but the final interval have finite
widths inferred from the next age; the final interval is open-ended.
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


FIELDS = ("age", "width", "mx", "ax", "qx", "lx", "dx", "Lx", "Tx", "ex")


def _number(value, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def construct_life_table(intervals: list[dict], *, radix: float = 100_000) -> list[dict]:
    """Construct an abridged life table using qx=n*mx/(1+(n-ax)*mx).

    ``intervals`` contains ascending ``age`` and nonnegative ``mx``. Optional
    ``ax`` is years lived on average by those dying in each finite interval,
    defaulting to half its width. The last row is open-ended and requires mx>0;
    its Lx is lx/mx. qx for the last row is one. No inferential uncertainty is
    calculated because rates alone do not determine sampling variances.
    """
    radix = _number(radix, "radix")
    if radix <= 0:
        raise ValueError("radix must be positive")
    if not intervals:
        raise ValueError("at least one age interval is required")

    table = []
    previous_age = -1.0
    for i, item in enumerate(intervals):
        if not isinstance(item, dict):
            raise ValueError(f"row {i + 1} must be an object")
        age = _number(item.get("age"), f"row {i + 1} age")
        mx = _number(item.get("mx"), f"row {i + 1} mx")
        if age < 0 or age <= previous_age:
            raise ValueError("ages must be nonnegative and strictly increasing")
        if mx < 0:
            raise ValueError(f"row {i + 1} mx must be nonnegative")
        last = i == len(intervals) - 1
        if last:
            if mx == 0:
                raise ValueError("open-ended last interval requires mx > 0")
            width = None
            if item.get("ax") not in (None, ""):
                raise ValueError("ax is not used for the open-ended last interval")
            ax = None
            qx = 1.0
        else:
            next_item = intervals[i + 1]
            if not isinstance(next_item, dict):
                raise ValueError(f"row {i + 2} must be an object")
            next_age = _number(next_item.get("age"), f"row {i + 2} age")
            width = next_age - age
            if width <= 0:
                raise ValueError("ages must be strictly increasing")
            raw_ax = item.get("ax")
            ax = width / 2 if raw_ax in (None, "") else _number(raw_ax, f"row {i + 1} ax")
            if not 0 <= ax <= width:
                raise ValueError(f"row {i + 1} ax must lie between 0 and {width:g}")
            denominator = (1 / mx + width - ax) if mx else None
            qx = min(1.0, width / denominator) if denominator else (1.0 if mx else 0.0)
        table.append({"age": age, "width": width, "mx": mx, "ax": ax, "qx": qx})
        previous_age = age

    survivors = radix
    for row in table:
        row["lx"] = survivors
        row["dx"] = survivors * row["qx"]
        next_survivors = max(0.0, survivors - row["dx"])
        row["Lx"] = (
            survivors / row["mx"] if row["width"] is None
            else row["width"] * next_survivors + row["ax"] * row["dx"]
        )
        if not math.isfinite(row["Lx"]):
            raise ValueError("inputs produce non-finite person-years")
        survivors = next_survivors

    remaining_years = 0.0
    for row in reversed(table):
        remaining_years += row["Lx"]
        row["Tx"] = remaining_years
        row["ex"] = remaining_years / row["lx"] if row["lx"] > 0 else None
    return table


def read_intervals(path: str | Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not {"age", "mx"}.issubset(reader.fieldnames):
            raise ValueError("input CSV requires age,mx headers (optional ax)")
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError("input CSV has duplicate header names")
        rows = list(reader)
    if any(None in row for row in rows):
        raise ValueError("input CSV has more fields than the header")
    return rows


def write_table(path: str | Path, table: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for row in table:
            writer.writerow({name: "" if row[name] is None else f"{row[name]:.12g}" for name in FIELDS})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Construct a Chiang-type abridged period life table")
    parser.add_argument("input", help="CSV file with age,mx and optional ax")
    parser.add_argument("output", help="destination CSV for age, width, mx, ax, qx, lx, dx, Lx, Tx, ex")
    parser.add_argument("--radix", type=float, default=100_000)
    args = parser.parse_args(argv)
    try:
        table = construct_life_table(read_intervals(args.input), radix=args.radix)
        write_table(args.output, table)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    print(f"Constructed {len(table)} age intervals; e({table[0]['age']:g}) = {table[0]['ex']:.4f} years")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
