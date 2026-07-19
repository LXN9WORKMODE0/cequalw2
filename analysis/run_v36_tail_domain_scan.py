#!/usr/bin/env python3
"""Run reversible V36 tail-domain sensitivity cases using tail_domain.opt."""

from __future__ import annotations

import argparse
import csv
import re
import shutil
from pathlib import Path

import run_w2_v0_v1_smoke as smoke
from analyze_v35_multistation_waterline import (
    DEFAULT_AUDIT,
    DEFAULT_GAPS,
    DEFAULT_OBSERVATIONS,
    run_analysis,
)
from analyze_v36_macro_domain_preflight import DEFAULT_BATHYMETRY, center_distance_m, parse_dlx_rows, read_csv_rows


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CASE = ROOT / "cases" / "xld_2021_base"
DEFAULT_EXE = ROOT / "w2source_v455_2_11_2026" / "build_console" / "w2_v455_console.exe"
WORK_ROOT = ROOT / "analysis" / ".runs" / "v36_tail_domain_scan"
DEFAULT_TMEND = 44436.5
V36_CONFIG_PATTERN = re.compile(
    r"\[V36_TAIL_DOMAIN_CONFIG\].*?JB=(?P<jb>\d+).*?MIN_NSEG=(?P<nseg>\d+).*?MAX_SUPPORTED=(?P<maximum>\d+)",
    re.IGNORECASE,
)


def prepare_case(nseg: int, exe_path: Path, tmend: float, force: bool) -> Path:
    case_dir = WORK_ROOT / f"tail_nseg_{nseg:02d}_case"
    if case_dir.exists() and force:
        smoke.remove_tree(case_dir)
    if not case_dir.exists():
        shutil.copytree(SOURCE_CASE, case_dir, ignore=smoke.OUTPUT_IGNORE)
    smoke.update_tmend(case_dir / "w2_con.csv", tmend)
    smoke.stage_exe(case_dir, exe_path)
    option = case_dir / "tail_domain.opt"
    if nseg == 4:
        option.unlink(missing_ok=True)
    else:
        option.write_text(f"1 {nseg}\n", encoding="ascii")
    return case_dir


def parse_v36_config(path: Path, branch: int = 1) -> tuple[int, int]:
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            match = V36_CONFIG_PATTERN.search(line)
            if match and int(match.group("jb")) == branch:
                return int(match.group("nseg")), int(match.group("maximum"))
    raise ValueError(f"V36 tail-domain config marker not found in {path}")


def assert_domain_run(result: smoke.SmokeResult, expected_length_m: float) -> None:
    smoke.assert_v24_conservation(result)
    smoke.assert_v25_boundary_alignment(result)
    smoke.assert_v26_domain_ownership(result)
    if result.tail_profile_storage_count <= 0 or result.tail_profile_storage_gap_max > 1.0e-2:
        raise AssertionError("V27 profile storage is not closed")
    if abs(result.tail_reach_length_min - expected_length_m) > 1.0e-6:
        raise AssertionError(
            f"Unexpected minimum reach length: {result.tail_reach_length_min} vs {expected_length_m}"
        )
    if abs(result.tail_reach_length_max - expected_length_m) > 1.0e-6:
        raise AssertionError(
            f"Unexpected maximum reach length: {result.tail_reach_length_max} vs {expected_length_m}"
        )
    smoke.assert_v29_accepted_diagnostics(result)
    smoke.assert_v31_single_step(result)
    smoke.assert_v32_segment_volume(result)
    smoke.assert_v33_local_targets(result)
    smoke.assert_no_computational_warning(result)


def select_primary_station_rows(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    return {
        str(row["station_code"]): row
        for row in rows
        if row["mapping_variant"] != "segment222_center_origin"
    }


def result_row(
    requested_nseg: int,
    result: smoke.SmokeResult,
    station_rows: list[dict[str, object]],
    interval_rows: list[dict[str, object]],
) -> dict[str, object]:
    configured_nseg, maximum = parse_v36_config(result.warn_path)
    stations = select_primary_station_rows(station_rows)
    intervals = {str(row["interval"]): row for row in interval_rows}
    row: dict[str, object] = {
        "case": result.case_dir.name,
        "requested_nseg": requested_nseg,
        "configured_nseg": configured_nseg,
        "max_supported": maximum,
        "actual_domain_nseg": result.tail_domain_nseg_min,
        "couple_segment": result.tail_couple_seg,
        "reach_length_m": result.tail_reach_length_min,
        "computational_warning_count": result.computational_warning_count,
        "v24_mass_residual_max": result.tail_mass_resid_max,
        "v24_flux_gap_max": result.tail_flux_gap_max,
        "v27_profile_gap_max": result.tail_profile_storage_gap_max,
        "v31_full_storage_residual_max": result.tail_full_storage_resid_max,
        "v32_segment_volume_gap_max": result.tail_segment_volume_gap_max,
    }
    for code in ("XLD", "YMT", "SJ", "BHT"):
        row[f"{code.lower()}_bias_m"] = stations[code]["bias_m"]
        row[f"{code.lower()}_rmse_m"] = stations[code]["rmse_m"]
        row[f"{code.lower()}_stage_q_slope_ratio"] = stations[code]["stage_q_slope_ratio"]
    for interval, prefix in (("YMT->SJ", "ymt_sj"), ("SJ->BHT", "sj_bht"), ("XLD->BHT", "xld_bht")):
        row[f"{prefix}_head_bias_m"] = intervals[interval]["head_bias_m"]
        row[f"{prefix}_head_rmse_m"] = intervals[interval]["head_rmse_m"]
        row[f"{prefix}_head_q_slope_ratio"] = intervals[interval]["head_q_slope_ratio"]
    return row


def write_summary(rows: list[dict[str, object]]) -> Path:
    path = WORK_ROOT / "tail_domain_scan_summary.csv"
    merged: dict[int, dict[str, object]] = {}
    if path.exists():
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                merged[int(row["requested_nseg"])] = row
    for row in rows:
        merged[int(row["requested_nseg"])] = row
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(merged[key] for key in sorted(merged))
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nsegs", nargs="+", type=int, default=[4, 26])
    parser.add_argument("--tmend", type=float, default=DEFAULT_TMEND)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    dlx = parse_dlx_rows(read_csv_rows(DEFAULT_BATHYMETRY))
    rows: list[dict[str, object]] = []
    for nseg in args.nsegs:
        case_dir = prepare_case(nseg, args.exe, args.tmend, args.force)
        print(f"Running {case_dir.name}", flush=True)
        smoke.run_case(case_dir)
        result = smoke.evaluate(case_dir)
        expected_couple = 2 + nseg
        expected_length = center_distance_m(dlx, 2, expected_couple)
        assert_domain_run(result, expected_length)
        _, _, station_rows, interval_rows, _ = run_analysis(
            case_dir,
            DEFAULT_OBSERVATIONS,
            DEFAULT_AUDIT,
            DEFAULT_GAPS,
            case_dir / "v35_multistation",
            smoke.WINDOW_START if hasattr(smoke, "WINDOW_START") else 44430.0,
            args.tmend,
        )
        rows.append(result_row(nseg, result, station_rows, interval_rows))
    summary = write_summary(rows)
    print(f"Summary: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
