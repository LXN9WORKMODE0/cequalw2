#!/usr/bin/env python3
"""Run frozen long-window boundary candidates around the accepted V38 interval."""

from __future__ import annotations

import argparse
import math
import shutil
from pathlib import Path

import run_w2_v0_v1_smoke as smoke
from analyze_v35_multistation_waterline import (
    DEFAULT_AUDIT,
    DEFAULT_GAPS,
    DEFAULT_OBSERVATIONS,
    run_analysis,
)
from analyze_v36_macro_domain_preflight import (
    DEFAULT_BATHYMETRY,
    center_distance_m,
    parse_dlx_rows,
    read_csv_rows,
)
from analyze_v40_holdout_regimes import (
    CALIBRATION_END,
    HOLDOUT_END,
    evaluate_acceptance,
    evaluate_regime_improvement,
    load_station_samples,
    reduction,
    relative_change,
    summarize_regimes,
    write_csv,
)
from run_v36_tail_domain_scan import assert_domain_run
from run_v39_long_window_validation import metric_row


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CASE = ROOT / "cases" / "xld_2021_base"
DEFAULT_EXE = ROOT / "w2source_v455_2_11_2026" / "build_console" / "w2_v455_console.exe"
WORK_ROOT = ROOT / "analysis" / ".runs" / "v41_long_window_robustness"
V39_ROOT = ROOT / "analysis" / ".runs" / "v39_long_window_validation"
DEFAULT_BASELINE = V39_ROOT / "baseline_case"
DEFAULT_CENTER = V39_ROOT / "v38_neff_0725_case"
DEFAULT_NEFFS = (0.070, 0.075)
FULL_START = 44430.0


def case_label(neff: float) -> str:
    return f"v38_neff_{neff:.4f}".replace("0.", "")


def prepare_case(neff: float, tmend: float, exe_path: Path, force: bool) -> Path:
    label = case_label(neff)
    case_dir = WORK_ROOT / f"{label}_case"
    if case_dir.exists() and force:
        smoke.remove_tree(case_dir)
    if not case_dir.exists():
        shutil.copytree(SOURCE_CASE, case_dir, ignore=smoke.OUTPUT_IGNORE)
    smoke.update_tmend(case_dir / "w2_con.csv", tmend)
    smoke.stage_exe(case_dir, exe_path)
    for option in ("tail_domain.opt", "tail_macro.opt", "tail_macro_active.opt"):
        (case_dir / option).unlink(missing_ok=True)
    (case_dir / "tail_domain.opt").write_text("1 26\n", encoding="ascii")
    (case_dir / "tail_macro_active.opt").write_text(
        f"1 28 {neff:.8f}\n", encoding="ascii"
    )
    return case_dir


def all_candidates_pass(rows: list[dict[str, object]]) -> bool:
    return bool(rows) and all(bool(row["passed"]) for row in rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--neff", nargs="+", type=float, default=list(DEFAULT_NEFFS))
    parser.add_argument("--tmend", type=float, default=HOLDOUT_END)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--baseline-case", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--center-case", type=Path, default=DEFAULT_CENTER)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    case_by_label: dict[str, Path] = {
        "baseline": args.baseline_case,
        "v38_neff_0725": args.center_case,
    }
    for neff in args.neff:
        label = case_label(neff)
        case_dir = prepare_case(neff, args.tmend, args.exe, args.force)
        print(f"Running {label}", flush=True)
        smoke.run_case(case_dir)
        case_by_label[label] = case_dir

    dlx = parse_dlx_rows(read_csv_rows(DEFAULT_BATHYMETRY))
    full_rows: list[dict[str, object]] = []
    holdout_rows: list[dict[str, object]] = []
    station_regime_by_case: dict[str, list[dict[str, object]]] = {}
    interval_regime_by_case: dict[str, list[dict[str, object]]] = {}
    strict_start = math.nextafter(CALIBRATION_END, math.inf)
    ordered_labels = ["baseline", *sorted(label for label in case_by_label if label != "baseline")]
    for label in ordered_labels:
        case_dir = case_by_label[label]
        result = smoke.evaluate(case_dir)
        interface = 6 if label == "baseline" else 28
        assert_domain_run(result, center_distance_m(dlx, 2, interface))
        _, _, station_rows, interval_rows, _ = run_analysis(
            case_dir,
            DEFAULT_OBSERVATIONS,
            DEFAULT_AUDIT,
            DEFAULT_GAPS,
            WORK_ROOT / "analysis" / label / "full",
            FULL_START,
            args.tmend,
        )
        full_rows.append(metric_row(label, result, station_rows, interval_rows))
        _, _, station_rows, interval_rows, _ = run_analysis(
            case_dir,
            DEFAULT_OBSERVATIONS,
            DEFAULT_AUDIT,
            DEFAULT_GAPS,
            WORK_ROOT / "analysis" / label / "holdout",
            strict_start,
            args.tmend,
        )
        holdout_rows.append(metric_row(label, result, station_rows, interval_rows))
        samples, regime_index, thresholds = load_station_samples(
            case_dir, CALIBRATION_END, args.tmend
        )
        station_regime_by_case[label], interval_regime_by_case[label] = summarize_regimes(
            label, samples, regime_index, thresholds
        )

    holdout_by_case = {str(row["case"]): row for row in holdout_rows}
    baseline = holdout_by_case["baseline"]
    gate_rows: list[dict[str, object]] = []
    regime_rows: list[dict[str, object]] = []
    candidate_rows: list[dict[str, object]] = []
    for label in ordered_labels:
        if label == "baseline":
            continue
        candidate = holdout_by_case[label]
        gates, full_pass = evaluate_acceptance(baseline, candidate)
        for row in gates:
            row = {"candidate": label, **row}
            gate_rows.append(row)
        stations = station_regime_by_case["baseline"] + station_regime_by_case[label]
        intervals = interval_regime_by_case["baseline"] + interval_regime_by_case[label]
        regimes, regime_pass = evaluate_regime_improvement(stations, intervals, label)
        for row in regimes:
            regime_rows.append({"candidate": label, **row})
        gate_rows.append(
            {
                "candidate": label,
                "gate": "bht_and_total_head_improve_in_every_regime",
                "value": int(regime_pass),
                "operator": "==",
                "limit": 1,
                "passed": regime_pass,
            }
        )
        side_effect = max(
            relative_change(float(baseline[field]), float(candidate[field]))
            for field in ("xld_rmse_m", "ymt_rmse_m", "sj_rmse_m")
        )
        candidate_rows.append(
            {
                "candidate": label,
                "bht_holdout_rmse_reduction": reduction(
                    float(baseline["bht_rmse_m"]), float(candidate["bht_rmse_m"])
                ),
                "xld_bht_head_holdout_rmse_reduction": reduction(
                    float(baseline["xld_bht_head_rmse_m"]),
                    float(candidate["xld_bht_head_rmse_m"]),
                ),
                "maximum_other_station_relative_worsening": side_effect,
                "all_regimes_improve": regime_pass,
                "passed": full_pass and regime_pass,
            }
        )

    write_csv(WORK_ROOT / "full_window_summary.csv", full_rows)
    write_csv(WORK_ROOT / "holdout_summary.csv", holdout_rows)
    write_csv(WORK_ROOT / "candidate_acceptance.csv", candidate_rows)
    write_csv(WORK_ROOT / "acceptance_gates.csv", gate_rows)
    write_csv(WORK_ROOT / "regime_improvement.csv", regime_rows)
    passed = all_candidates_pass(candidate_rows)
    print(f"V41 parameter-interval robustness: {'PASS' if passed else 'FAIL'}")
    print(f"Output: {WORK_ROOT}")
    if not passed:
        raise AssertionError("V41 parameter-interval robustness gates failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
