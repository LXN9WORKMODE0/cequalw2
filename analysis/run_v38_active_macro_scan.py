#!/usr/bin/env python3
"""Run reversible V38 active BHT-SJ aggregate-closure cases."""

from __future__ import annotations

import argparse
import csv
import re
import shutil
from pathlib import Path

import run_w2_v0_v1_smoke as smoke
from analyze_v29_qstate_response import parse_accepted_tail, summarize as summarize_qstate
from analyze_v35_multistation_waterline import (
    DEFAULT_AUDIT,
    DEFAULT_GAPS,
    DEFAULT_OBSERVATIONS,
    run_analysis,
)
from analyze_v36_macro_domain_preflight import DEFAULT_BATHYMETRY, center_distance_m, parse_dlx_rows, read_csv_rows
from run_v36_tail_domain_scan import assert_domain_run, select_primary_station_rows


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CASE = ROOT / "cases" / "xld_2021_base"
DEFAULT_EXE = ROOT / "w2source_v455_2_11_2026" / "build_console" / "w2_v455_console.exe"
WORK_ROOT = ROOT / "analysis" / ".runs" / "v38_active_macro_scan"
DEFAULT_TMEND = 44431.0
DOMAIN_NSEG = 26
INTERFACE_SEGMENT = 28
CONFIG_PATTERN = re.compile(
    r"\[V38_ACTIVE_MACRO_CONFIG\].*?JB=\s*(?P<jb>\d+).*?ISEG=\s*(?P<iseg>\d+)"
    r".*?NEFF=\s*(?P<neff>[-+0-9.eE]+)",
    re.IGNORECASE,
)


def case_name(neff: float, tmend: float, domain_nseg: int = DOMAIN_NSEG, interface: int = INTERFACE_SEGMENT) -> str:
    return (
        f"nseg_{domain_nseg:02d}_i{interface:03d}_neff_{neff:.4f}_tmend_{tmend:.2f}".replace(".", "p")
        + "_case"
    )


def prepare_case(
    neff: float,
    tmend: float,
    exe_path: Path,
    force: bool,
    domain_nseg: int = DOMAIN_NSEG,
    interface: int = INTERFACE_SEGMENT,
) -> Path:
    case_dir = WORK_ROOT / case_name(neff, tmend, domain_nseg, interface)
    if case_dir.exists() and force:
        smoke.remove_tree(case_dir)
    if not case_dir.exists():
        shutil.copytree(SOURCE_CASE, case_dir, ignore=smoke.OUTPUT_IGNORE)
    smoke.update_tmend(case_dir / "w2_con.csv", tmend)
    smoke.stage_exe(case_dir, exe_path)
    (case_dir / "tail_domain.opt").write_text(f"1 {domain_nseg}\n", encoding="ascii")
    (case_dir / "tail_macro_active.opt").write_text(
        f"1 {interface} {neff:.8f}\n", encoding="ascii"
    )
    (case_dir / "tail_macro.opt").unlink(missing_ok=True)
    return case_dir


def parse_active_config(path: Path, branch: int = 1) -> tuple[int, float]:
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            match = CONFIG_PATTERN.search(line)
            if match and int(match.group("jb")) == branch:
                return int(match.group("iseg")), float(match.group("neff"))
    raise ValueError(f"V38 active macro config marker not found in {path}")


def result_row(
    requested_neff: float,
    tmend: float,
    result: smoke.SmokeResult,
    station_rows: list[dict[str, object]],
    interval_rows: list[dict[str, object]],
    qstate_summary: dict[str, float | int],
) -> dict[str, object]:
    interface, configured_neff = parse_active_config(result.warn_path)
    stations = select_primary_station_rows(station_rows)
    intervals = {str(row["interval"]): row for row in interval_rows}
    row: dict[str, object] = {
        "case": result.case_dir.name,
        "tmend": tmend,
        "requested_neff": requested_neff,
        "configured_neff": configured_neff,
        "interface_segment": interface,
        "actual_domain_nseg": result.tail_domain_nseg_min,
        "couple_segment": result.tail_couple_seg,
        "reach_length_m": result.tail_reach_length_min,
        "computational_warning_count": result.computational_warning_count,
        "v24_mass_residual_max": result.tail_mass_resid_max,
        "v24_flux_gap_max": result.tail_flux_gap_max,
        "v27_profile_gap_max": result.tail_profile_storage_gap_max,
        "v31_full_storage_residual_max": result.tail_full_storage_resid_max,
        "v32_segment_volume_gap_max": result.tail_segment_volume_gap_max,
        "accepted_state_count": qstate_summary["count"],
        "qstate_qtarget_corr": qstate_summary["qstate_qtarget_corr"],
        "qstate_minus_qtarget_rmse_m3s": qstate_summary["qstate_minus_qtarget_rmse"],
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
    path = WORK_ROOT / "active_macro_scan_summary.csv"
    merged: dict[tuple[int, int, float, float], dict[str, object]] = {}
    if path.exists():
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                key = (
                    int(row["actual_domain_nseg"]),
                    int(row["interface_segment"]),
                    float(row["tmend"]),
                    float(row["requested_neff"]),
                )
                merged[key] = row
    for row in rows:
        key = (
            int(row["actual_domain_nseg"]),
            int(row["interface_segment"]),
            float(row["tmend"]),
            float(row["requested_neff"]),
        )
        merged[key] = row
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(merged[key] for key in sorted(merged))
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--neff", nargs="+", type=float, default=[0.065, 0.070, 0.0725, 0.075])
    parser.add_argument("--tmend", type=float, default=DEFAULT_TMEND)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--nseg", type=int, default=DOMAIN_NSEG)
    parser.add_argument("--interface", type=int, default=INTERFACE_SEGMENT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.interface != 2 + args.nseg:
        parser.error("for branch 1, --interface must equal 2 + --nseg")

    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    dlx = parse_dlx_rows(read_csv_rows(DEFAULT_BATHYMETRY))
    expected_length = center_distance_m(dlx, 2, args.interface)
    rows: list[dict[str, object]] = []
    for neff in args.neff:
        case_dir = prepare_case(neff, args.tmend, args.exe, args.force, args.nseg, args.interface)
        print(f"Running {case_dir.name}", flush=True)
        smoke.run_case(case_dir)
        result = smoke.evaluate(case_dir)
        assert_domain_run(result, expected_length)
        station_output = case_dir / "v35_multistation"
        _, _, station_rows, interval_rows, _ = run_analysis(
            case_dir,
            DEFAULT_OBSERVATIONS,
            DEFAULT_AUDIT,
            DEFAULT_GAPS,
            station_output,
            smoke.WINDOW_START if hasattr(smoke, "WINDOW_START") else 44430.0,
            args.tmend,
        )
        accepted = parse_accepted_tail(result.warn_path.read_text(encoding="utf-8", errors="ignore"))
        rows.append(result_row(neff, args.tmend, result, station_rows, interval_rows, summarize_qstate(accepted)))
    summary = write_summary(rows)
    print(f"Summary: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
