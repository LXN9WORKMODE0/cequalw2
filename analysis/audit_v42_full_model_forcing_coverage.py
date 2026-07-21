#!/usr/bin/env python3
"""Audit whether the active XLD case can be extended to full 2020-2025 runs.

This is a range audit, not a semantic validation of every forcing value.  It
discovers the time-varying files referenced by the active control and
meteorological-region files and reports their JDAY coverage.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd


EXCEL_ORIGIN = pd.Timestamp("1899-12-30")
YEARS = tuple(range(2020, 2026))
REFERENCE_PATTERN = re.compile(r"(?:\.\\)?InputFiles\\[^,\r\n]+?\.(?:npt|csv)", re.IGNORECASE)
JDAY_PATTERN = re.compile(r"^\s*([0-9]+(?:\.[0-9]*)?)(?:\s|,)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", type=Path, default=Path("cases/xld_2021_base"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("analysis/verification/v42_full_model_forcing_coverage"),
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def discover_references(case_dir: Path) -> list[Path]:
    sources = [case_dir / "w2_con.csv", case_dir / "W2_MetRegions.csv"]
    references: set[Path] = set()
    for source in sources:
        for match in REFERENCE_PATTERN.findall(read_text(source)):
            relative = match.removeprefix(".\\").replace("\\", "/")
            references.add(case_dir / Path(relative))
    return sorted(references, key=lambda path: str(path).lower())


def extract_jdays(path: Path) -> list[float]:
    values: list[float] = []
    for line in read_text(path).splitlines():
        match = JDAY_PATTERN.match(line)
        if not match:
            continue
        value = float(match.group(1))
        if 40000.0 <= value <= 50000.0:
            values.append(value)
    return values


def forcing_role(path: Path) -> str:
    name = path.name.upper()
    if name.startswith("METINPUT_"):
        return "meteorology"
    if "XLDOUTFLOW" in name:
        return "reservoir_outflow"
    if "QIN_" in name or "BHTOUTFLOW" in name:
        return "inflow_or_distributed_flow"
    if "TIN_" in name:
        return "temperature"
    if name in {"XLD_WSC.NPT", "XLD_SHADE.CSV"}:
        return "static_or_climatology"
    return "other_referenced"


def to_date(jday: float) -> pd.Timestamp:
    return EXCEL_ORIGIN + pd.to_timedelta(jday, unit="D")


def audit_files(case_dir: Path) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for path in discover_references(case_dir):
        jdays = extract_jdays(path) if path.exists() else []
        minimum = min(jdays) if jdays else None
        maximum = max(jdays) if jdays else None
        records.append(
            {
                "file": str(path.relative_to(case_dir)) if path.exists() else str(path),
                "role": forcing_role(path),
                "exists": path.exists(),
                "jday_rows": len(jdays),
                "first_jday": minimum,
                "last_jday": maximum,
                "first_datetime": to_date(minimum).isoformat(sep=" ") if minimum is not None else "",
                "last_datetime": to_date(maximum).isoformat(sep=" ") if maximum is not None else "",
            }
        )
    return pd.DataFrame.from_records(records)


def summarize_year_readiness(files: pd.DataFrame) -> pd.DataFrame:
    required = files[files["role"].isin({
        "meteorology",
        "reservoir_outflow",
        "inflow_or_distributed_flow",
        "temperature",
    })]
    records: list[dict[str, object]] = []
    for year in YEARS:
        year_start = (pd.Timestamp(year=year, month=1, day=1) - EXCEL_ORIGIN) / pd.Timedelta(days=1)
        year_end = (
            pd.Timestamp(year=year + 1, month=1, day=1) - pd.Timedelta(hours=1) - EXCEL_ORIGIN
        ) / pd.Timedelta(days=1)
        for role, group in required.groupby("role"):
            covers = (
                group["exists"]
                & group["first_jday"].notna()
                & (group["first_jday"] <= year_start)
                & (group["last_jday"] >= year_end)
            )
            records.append(
                {
                    "year": year,
                    "role": role,
                    "required_files": int(len(group)),
                    "files_covering_full_year": int(covers.sum()),
                    "role_ready": bool(covers.all()),
                }
            )
    result = pd.DataFrame.from_records(records)
    year_ready = result.groupby("year")["role_ready"].all().rename("all_required_roles_ready")
    return result.merge(year_ready, on="year", how="left")


def summarize_declared_window(files: pd.DataFrame) -> pd.DataFrame:
    required = files[files["role"].isin({
        "meteorology",
        "reservoir_outflow",
        "inflow_or_distributed_flow",
        "temperature",
    })]
    start = 44430.0
    end = 44484.0
    records: list[dict[str, object]] = []
    for role, group in required.groupby("role"):
        covers = (
            group["exists"]
            & group["first_jday"].notna()
            & (group["first_jday"] <= start)
            & (group["last_jday"] >= end)
        )
        records.append(
            {
                "window": "existing_v39_44430_44484",
                "start_jday": start,
                "end_jday": end,
                "role": role,
                "required_files": int(len(group)),
                "files_covering_window": int(covers.sum()),
                "role_ready": bool(covers.all()),
            }
        )
    result = pd.DataFrame.from_records(records)
    result["all_required_roles_ready"] = bool(result["role_ready"].all())
    return result


def main() -> None:
    args = parse_args()
    files = audit_files(args.case_dir)
    readiness = summarize_year_readiness(files)
    declared_window = summarize_declared_window(files)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    files.to_csv(args.output_dir / "active_forcing_file_ranges.csv", index=False, encoding="utf-8-sig")
    readiness.to_csv(args.output_dir / "year_readiness.csv", index=False, encoding="utf-8-sig")
    declared_window.to_csv(args.output_dir / "declared_window_readiness.csv", index=False, encoding="utf-8-sig")
    manifest = {
        "case_dir": str(args.case_dir),
        "audit_scope": "time-range coverage of active referenced files",
        "range_audit_only": True,
        "does_not_fabricate_missing_inputs": True,
        "files": [
            "active_forcing_file_ranges.csv",
            "year_readiness.csv",
            "declared_window_readiness.csv",
        ],
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(readiness.to_string(index=False))


if __name__ == "__main__":
    main()
