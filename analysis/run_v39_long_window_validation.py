#!/usr/bin/env python3
"""Compare the default baseline and fixed V38 candidate over the original 54-day case."""

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

import run_w2_v0_v1_smoke as smoke
from analyze_v35_multistation_waterline import DEFAULT_AUDIT, DEFAULT_GAPS, DEFAULT_OBSERVATIONS, run_analysis
from analyze_v36_macro_domain_preflight import DEFAULT_BATHYMETRY, center_distance_m, parse_dlx_rows, read_csv_rows
from run_v36_tail_domain_scan import assert_domain_run, select_primary_station_rows


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CASE = ROOT / "cases" / "xld_2021_base"
DEFAULT_EXE = ROOT / "w2source_v455_2_11_2026" / "build_console" / "w2_v455_console.exe"
WORK_ROOT = ROOT / "analysis" / ".runs" / "v39_long_window_validation"
DEFAULT_START = 44430.0
DEFAULT_END = 44484.0
DEFAULT_NEFF = 0.0725
DEFAULT_WINDOW_DAYS = 7.0


def candidate_label(neff: float) -> str:
    return f"v38_neff_{neff:.4f}".replace("0.", "")


def window_ranges(start: float, end: float, days: float) -> list[tuple[float, float]]:
    if end <= start:
        raise ValueError("end must be greater than start")
    if days <= 0.0:
        raise ValueError("window days must be positive")
    ranges: list[tuple[float, float]] = []
    left = start
    while left < end:
        right = min(left + days, end)
        ranges.append((left, right))
        left = right
    return ranges


def prepare_case(label: str, tmend: float, exe_path: Path, active: bool, neff: float, force: bool) -> Path:
    case_dir = WORK_ROOT / f"{label}_case"
    if case_dir.exists() and force:
        smoke.remove_tree(case_dir)
    if not case_dir.exists():
        shutil.copytree(SOURCE_CASE, case_dir, ignore=smoke.OUTPUT_IGNORE)
    smoke.update_tmend(case_dir / "w2_con.csv", tmend)
    smoke.stage_exe(case_dir, exe_path)
    for option in ("tail_domain.opt", "tail_macro.opt", "tail_macro_active.opt"):
        (case_dir / option).unlink(missing_ok=True)
    if active:
        (case_dir / "tail_domain.opt").write_text("1 26\n", encoding="ascii")
        (case_dir / "tail_macro_active.opt").write_text(f"1 28 {neff:.8f}\n", encoding="ascii")
    return case_dir


def metric_row(label: str, result: smoke.SmokeResult, station_rows: list[dict[str, object]], interval_rows: list[dict[str, object]]) -> dict[str, object]:
    stations = select_primary_station_rows(station_rows)
    intervals = {str(row["interval"]): row for row in interval_rows}
    row: dict[str, object] = {
        "case": label,
        "computational_warning_count": result.computational_warning_count,
        "v24_mass_residual_max": result.tail_mass_resid_max,
        "v27_profile_gap_max": result.tail_profile_storage_gap_max,
        "v32_segment_volume_gap_max": result.tail_segment_volume_gap_max,
    }
    for code in ("XLD", "YMT", "SJ", "BHT"):
        row[f"{code.lower()}_bias_m"] = stations[code]["bias_m"]
        row[f"{code.lower()}_rmse_m"] = stations[code]["rmse_m"]
        row[f"{code.lower()}_stage_q_slope_ratio"] = stations[code]["stage_q_slope_ratio"]
        row[f"{code.lower()}_flagged_points"] = stations[code]["flagged_points_in_window"]
    for interval, prefix in (("YMT->SJ", "ymt_sj"), ("SJ->BHT", "sj_bht"), ("XLD->BHT", "xld_bht")):
        row[f"{prefix}_head_bias_m"] = intervals[interval]["head_bias_m"]
        row[f"{prefix}_head_rmse_m"] = intervals[interval]["head_rmse_m"]
        row[f"{prefix}_head_q_slope_ratio"] = intervals[interval]["head_q_slope_ratio"]
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=float, default=DEFAULT_START)
    parser.add_argument("--end", type=float, default=DEFAULT_END)
    parser.add_argument("--neff", type=float, default=DEFAULT_NEFF)
    parser.add_argument("--window-days", type=float, default=DEFAULT_WINDOW_DAYS)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--reuse", action="store_true", help="Reuse completed model outputs and rerun analysis only")
    args = parser.parse_args()
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    dlx = parse_dlx_rows(read_csv_rows(DEFAULT_BATHYMETRY))
    rows: list[dict[str, object]] = []
    window_rows: list[dict[str, object]] = []
    for label, active, interface in (("baseline", False, 6), (candidate_label(args.neff), True, 28)):
        case_preexisting = (WORK_ROOT / f"{label}_case").is_dir()
        case_dir = prepare_case(label, args.end, args.exe, active, args.neff, args.force)
        if args.reuse and case_preexisting and not args.force:
            print(f"Reusing {label}", flush=True)
        else:
            print(f"Running {label}", flush=True)
            smoke.run_case(case_dir)
        result = smoke.evaluate(case_dir)
        assert_domain_run(result, center_distance_m(dlx, 2, interface))
        _, _, station_rows, interval_rows, _ = run_analysis(
            case_dir, DEFAULT_OBSERVATIONS, DEFAULT_AUDIT, DEFAULT_GAPS,
            case_dir / "v35_multistation", args.start, args.end,
        )
        rows.append(metric_row(label, result, station_rows, interval_rows))
        for index, (start, end) in enumerate(window_ranges(args.start, args.end, args.window_days), start=1):
            _, _, station_rows, interval_rows, _ = run_analysis(
                case_dir, DEFAULT_OBSERVATIONS, DEFAULT_AUDIT, DEFAULT_GAPS,
                case_dir / "v39_windows" / f"window_{index:02d}", start, end,
            )
            window_row = {
                "case": label,
                "window": index,
                "start_jday": start,
                "end_jday": end,
            }
            window_row.update(metric_row(label, result, station_rows, interval_rows))
            window_rows.append(window_row)
    summary = WORK_ROOT / "long_window_summary.csv"
    with summary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    window_summary = WORK_ROOT / "window_summary.csv"
    with window_summary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(window_rows[0].keys()))
        writer.writeheader()
        writer.writerows(window_rows)
    print(f"Summary: {summary}")
    print(f"Window summary: {window_summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
