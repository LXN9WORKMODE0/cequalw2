#!/usr/bin/env python3
"""Run the non-mutating V37 macro-interface target preflight."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import run_w2_v0_v1_smoke as smoke
from analyze_v36_macro_domain_preflight import DEFAULT_BATHYMETRY, center_distance_m, parse_dlx_rows, read_csv_rows
from analyze_v37_macro_target import DEFAULT_OBSERVATIONS, observation_head_check, parse_macro_targets, summarize, write_outputs
from run_v36_tail_domain_scan import assert_domain_run


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CASE = ROOT / "cases" / "xld_2021_base"
DEFAULT_EXE = ROOT / "w2source_v455_2_11_2026" / "build_console" / "w2_v455_console.exe"
WORK_ROOT = ROOT / "analysis" / ".runs" / "v37_macro_target"
DEFAULT_TMEND = 44436.5


def prepare_case(exe_path: Path, tmend: float, interface_segment: int, force: bool) -> Path:
    case_dir = WORK_ROOT / "case"
    if case_dir.exists() and force:
        smoke.remove_tree(case_dir)
    if not case_dir.exists():
        shutil.copytree(SOURCE_CASE, case_dir, ignore=smoke.OUTPUT_IGNORE)
    smoke.update_tmend(case_dir / "w2_con.csv", tmend)
    smoke.stage_exe(case_dir, exe_path)
    (case_dir / "tail_domain.opt").unlink(missing_ok=True)
    (case_dir / "tail_macro.opt").write_text(f"1 {interface_segment}\n", encoding="ascii")
    return case_dir


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interface", type=int, default=26)
    parser.add_argument("--tmend", type=float, default=DEFAULT_TMEND)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    case_dir = prepare_case(args.exe, args.tmend, args.interface, args.force)
    smoke.run_case(case_dir)
    result = smoke.evaluate(case_dir)
    dlx = parse_dlx_rows(read_csv_rows(DEFAULT_BATHYMETRY))
    assert_domain_run(result, center_distance_m(dlx, 2, 6))
    rows = parse_macro_targets(result.warn_path.read_text(encoding="utf-8", errors="ignore"))
    if not rows or any(row.interface_segment != args.interface for row in rows):
        raise AssertionError("V37 macro target marker is absent or reports the wrong interface")
    summary = summarize(rows)
    summary.update(observation_head_check(rows, DEFAULT_OBSERVATIONS))
    write_outputs(WORK_ROOT, rows, summary)
    for key, value in summary.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
