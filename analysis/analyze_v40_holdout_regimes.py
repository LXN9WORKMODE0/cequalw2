#!/usr/bin/env python3
"""Evaluate the frozen V38 candidate on the strict post-calibration holdout."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import run_w2_v0_v1_smoke as smoke
from analyze_v35_multistation_waterline import (
    DEFAULT_AUDIT,
    DEFAULT_GAPS,
    DEFAULT_OBSERVATIONS,
    PRIMARY_STATIONS,
    build_station_samples,
    observation_path,
    read_npt_with_header,
    run_analysis,
    summarize_interval,
    summarize_station,
)
from analyze_v36_macro_domain_preflight import (
    DEFAULT_BATHYMETRY,
    center_distance_m,
    parse_dlx_rows,
    read_csv_rows,
)
from run_v21_bht_redistribution_scan import interpolate_series, parse_wl
from run_v36_tail_domain_scan import assert_domain_run
from run_v39_long_window_validation import metric_row


ROOT = Path(__file__).resolve().parents[1]
V39_ROOT = ROOT / "analysis" / ".runs" / "v39_long_window_validation"
DEFAULT_BASELINE = V39_ROOT / "baseline_case"
DEFAULT_CANDIDATE = V39_ROOT / "v38_neff_0725_case"
DEFAULT_OUTPUT = ROOT / "analysis" / ".runs" / "v40_holdout_regimes"
CALIBRATION_END = 44436.5
HOLDOUT_END = 44484.0
STATION_CODES = ("XLD", "YMT", "SJ", "BHT")
INTERVALS = (("YMT", "SJ"), ("SJ", "BHT"), ("XLD", "BHT"))


def quantile(values: list[float], probability: float) -> float:
    if not values:
        raise ValueError("quantile requires at least one value")
    if probability < 0.0 or probability > 1.0:
        raise ValueError("probability must be between zero and one")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


def build_regime_index(
    qphysical: list[tuple[float, float]],
    start_exclusive: float,
    end_inclusive: float,
    sample_times: list[float] | None = None,
) -> tuple[dict[float, tuple[str, str]], tuple[float, float]]:
    ordered_source = sorted(qphysical)
    holdout_positions = [
        position
        for position, (time, _) in enumerate(ordered_source)
        if start_exclusive < time <= end_inclusive
    ]
    holdout = [ordered_source[position] for position in holdout_positions]
    if len(holdout) < 3:
        raise ValueError("holdout needs at least three physical-flow samples")
    low = quantile([flow for _, flow in holdout], 1.0 / 3.0)
    high = quantile([flow for _, flow in holdout], 2.0 / 3.0)
    index: dict[float, tuple[str, str]] = {}
    evaluation_times = sample_times if sample_times is not None else [time for time, _ in holdout]
    for time in evaluation_times:
        if not start_exclusive < time <= end_inclusive:
            continue
        flow = interpolate_series(ordered_source, time)
        if flow <= low:
            flow_regime = "low"
        elif flow <= high:
            flow_regime = "middle"
        else:
            flow_regime = "high"
        hourly_offset = 1.0 / 24.0
        delta = interpolate_series(ordered_source, time + hourly_offset) - interpolate_series(
            ordered_source, time - hourly_offset
        )
        if delta > 1.0e-12:
            trend_regime = "rising"
        elif delta < -1.0e-12:
            trend_regime = "falling"
        else:
            trend_regime = "steady"
        index[round(time, 8)] = (flow_regime, trend_regime)
    return index, (low, high)


def relative_change(baseline: float, candidate: float) -> float:
    if baseline <= 0.0:
        raise ValueError("baseline metric must be positive")
    return candidate / baseline - 1.0


def reduction(baseline: float, candidate: float) -> float:
    return -relative_change(baseline, candidate)


def evaluate_acceptance(
    baseline: dict[str, object], candidate: dict[str, object]
) -> tuple[list[dict[str, object]], bool]:
    rows: list[dict[str, object]] = []

    def add(name: str, value: float, operator: str, limit: float, passed: bool) -> None:
        rows.append(
            {
                "gate": name,
                "value": value,
                "operator": operator,
                "limit": limit,
                "passed": passed,
            }
        )

    for field, name in (
        ("bht_rmse_m", "bht_rmse_reduction"),
        ("xld_bht_head_rmse_m", "xld_bht_head_rmse_reduction"),
    ):
        value = reduction(float(baseline[field]), float(candidate[field]))
        add(name, value, ">=", 0.50, value >= 0.50)
    for field in ("xld_rmse_m", "ymt_rmse_m", "sj_rmse_m"):
        value = relative_change(float(baseline[field]), float(candidate[field]))
        add(f"{field}_relative_worsening", value, "<=", 0.10, value <= 0.10)
    warning_count = float(candidate["computational_warning_count"])
    add("computational_warning_count", warning_count, "==", 0.0, warning_count == 0.0)
    for field, limit in (
        ("v24_mass_residual_max", 1.0e-6),
        ("v27_profile_gap_max", 1.0e-2),
        ("v32_segment_volume_gap_max", 1.0e-2),
    ):
        value = float(candidate[field])
        add(field, value, "<=", limit, value <= limit)
    return rows, all(bool(row["passed"]) for row in rows)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def load_station_samples(
    case_dir: Path, start_exclusive: float, end_inclusive: float
) -> tuple[dict[str, list[object]], dict[float, tuple[str, str]], tuple[float, float]]:
    stations = {station.code: station for station in PRIMARY_STATIONS if station.code in STATION_CODES}
    simulations = parse_wl(case_dir / "wl.csv", [station.segment for station in stations.values()])
    _, qphysical = read_npt_with_header(case_dir / "InputFiles" / "BHT" / "BHTOUTFLOW.npt")
    strict_start = math.nextafter(start_exclusive, math.inf)
    samples: dict[str, list[object]] = {}
    for code, station in stations.items():
        observations = read_npt_with_header(observation_path(DEFAULT_OBSERVATIONS, code))[1]
        samples[code] = build_station_samples(
            station,
            observations,
            simulations[station.segment],
            qphysical,
            strict_start,
            end_inclusive,
        )
    sample_times = [sample.jday for sample in samples["BHT"]]
    regime_index, thresholds = build_regime_index(
        qphysical, start_exclusive, end_inclusive, sample_times
    )
    return samples, regime_index, thresholds


def filter_samples(
    samples: list[object], regime_index: dict[float, tuple[str, str]], kind: str, label: str
) -> list[object]:
    position = 0 if kind == "flow" else 1
    return [
        sample
        for sample in samples
        if regime_index[round(sample.jday, 8)][position] == label
    ]


def summarize_regimes(
    label: str,
    samples: dict[str, list[object]],
    regime_index: dict[float, tuple[str, str]],
    thresholds: tuple[float, float],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    station_rows: list[dict[str, object]] = []
    interval_rows: list[dict[str, object]] = []
    for kind, regimes in (("flow", ("low", "middle", "high")), ("trend", ("rising", "steady", "falling"))):
        for regime in regimes:
            selected = {
                code: filter_samples(rows, regime_index, kind, regime)
                for code, rows in samples.items()
            }
            for code in STATION_CODES:
                row = {
                    "case": label,
                    "regime_type": kind,
                    "regime": regime,
                    "flow_q33_m3s": thresholds[0],
                    "flow_q67_m3s": thresholds[1],
                }
                row.update(summarize_station(selected[code], 0))
                station_rows.append(row)
            for downstream, upstream in INTERVALS:
                row = {
                    "case": label,
                    "regime_type": kind,
                    "regime": regime,
                    "flow_q33_m3s": thresholds[0],
                    "flow_q67_m3s": thresholds[1],
                }
                row.update(summarize_interval(selected[downstream], selected[upstream]))
                interval_rows.append(row)
    return station_rows, interval_rows


def evaluate_regime_improvement(
    station_rows: list[dict[str, object]],
    interval_rows: list[dict[str, object]],
    candidate_label: str = "v38_neff_0725",
) -> tuple[list[dict[str, object]], bool]:
    rows: list[dict[str, object]] = []
    keys = sorted({(str(row["regime_type"]), str(row["regime"])) for row in station_rows})
    for kind, regime in keys:
        bht = {
            str(row["case"]): row
            for row in station_rows
            if row["regime_type"] == kind and row["regime"] == regime and row["station_code"] == "BHT"
        }
        head = {
            str(row["case"]): row
            for row in interval_rows
            if row["regime_type"] == kind and row["regime"] == regime and row["interval"] == "XLD->BHT"
        }
        for metric, source, field in (
            ("bht_rmse", bht, "rmse_m"),
            ("xld_bht_head_rmse", head, "head_rmse_m"),
        ):
            baseline = float(source["baseline"][field])
            candidate = float(source[candidate_label][field])
            value = reduction(baseline, candidate)
            rows.append(
                {
                    "regime_type": kind,
                    "regime": regime,
                    "metric": metric,
                    "baseline_rmse_m": baseline,
                    "candidate_rmse_m": candidate,
                    "reduction_fraction": value,
                    "passed": value > 0.0,
                }
            )
    return rows, all(bool(row["passed"]) for row in rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-case", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--candidate-case", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--start-exclusive", type=float, default=CALIBRATION_END)
    parser.add_argument("--end", type=float, default=HOLDOUT_END)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    dlx = parse_dlx_rows(read_csv_rows(DEFAULT_BATHYMETRY))
    holdout_rows: list[dict[str, object]] = []
    station_regime_rows: list[dict[str, object]] = []
    interval_regime_rows: list[dict[str, object]] = []
    strict_start = math.nextafter(args.start_exclusive, math.inf)
    for label, case_dir, interface in (
        ("baseline", args.baseline_case, 6),
        ("v38_neff_0725", args.candidate_case, 28),
    ):
        result = smoke.evaluate(case_dir)
        assert_domain_run(result, center_distance_m(dlx, 2, interface))
        _, _, station_rows, interval_rows, _ = run_analysis(
            case_dir,
            DEFAULT_OBSERVATIONS,
            DEFAULT_AUDIT,
            DEFAULT_GAPS,
            args.output / label / "holdout",
            strict_start,
            args.end,
        )
        holdout_rows.append(metric_row(label, result, station_rows, interval_rows))
        samples, regime_index, thresholds = load_station_samples(
            case_dir, args.start_exclusive, args.end
        )
        stations, intervals = summarize_regimes(label, samples, regime_index, thresholds)
        station_regime_rows.extend(stations)
        interval_regime_rows.extend(intervals)

    baseline, candidate = holdout_rows
    acceptance_rows, full_pass = evaluate_acceptance(baseline, candidate)
    regime_rows, regime_pass = evaluate_regime_improvement(station_regime_rows, interval_regime_rows)
    acceptance_rows.append(
        {
            "gate": "bht_and_total_head_improve_in_every_regime",
            "value": int(regime_pass),
            "operator": "==",
            "limit": 1,
            "passed": regime_pass,
        }
    )
    write_csv(args.output / "holdout_summary.csv", holdout_rows)
    write_csv(args.output / "station_regime_metrics.csv", station_regime_rows)
    write_csv(args.output / "interval_regime_metrics.csv", interval_regime_rows)
    write_csv(args.output / "regime_improvement.csv", regime_rows)
    write_csv(args.output / "acceptance_gates.csv", acceptance_rows)
    passed = full_pass and regime_pass
    print(f"V40 holdout acceptance: {'PASS' if passed else 'FAIL'}")
    print(f"Output: {args.output}")
    if not passed:
        raise AssertionError("V40 holdout acceptance gates failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
