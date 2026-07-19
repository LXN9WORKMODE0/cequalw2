#!/usr/bin/env python3
"""Summarize the V37 shadow macro-interface flow target."""

from __future__ import annotations

import argparse
import csv
import math
import re
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path

from analyze_v29_qstate_response import correlation, quantile, slope
from run_v21_bht_redistribution_scan import interpolate_series, read_npt_with_header


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASE = ROOT / "analysis" / ".runs" / "v37_macro_target" / "case"
DEFAULT_OBSERVATIONS = ROOT / "outputs" / "xld_waterlevel_inputs_2021_2023" / "2021"
BASELINE_MANNING_N = 0.03
PATTERN = re.compile(
    r"\[V37_MACRO_TARGET\].*?JB=\s*(?P<jb>\d+).*?ISEG=\s*(?P<iseg>\d+)"
    r".*?JDAY=\s*(?P<jday>[-+0-9.eE]+).*?QPHYS=\s*(?P<qphys>[-+0-9.eE]+)"
    r".*?QCOMMIT=\s*(?P<qcommit>[-+0-9.eE]+)"
    r".*?QTARGET=\s*(?P<qtarget>[-+0-9.eE]+).*?QAGG=\s*(?P<qaggregate>[-+0-9.eE]+)"
    r".*?WUP=\s*(?P<wup>[-+0-9.eE]+).*?WIFACE=\s*(?P<wiface>[-+0-9.eE]+)"
    r".*?DX=\s*(?P<dx>[-+0-9.eE]+).*?RCOEFF=\s*(?P<rcoeff>[-+0-9.eE]+)"
    r".*?RFRIC=\s*(?P<rfric>[-+0-9.eE]+).*?RVEL=\s*(?P<rvel>[-+0-9.eE]+)"
    r".*?VALID=\s*(?P<valid>[TF])",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class MacroTarget:
    interface_segment: int
    jday: float
    qphys: float
    qcommit: float
    qtarget: float
    qaggregate: float
    wup: float
    wiface: float
    dx: float
    resistance_coefficient: float
    friction_coefficient: float
    velocity_coefficient: float
    valid: bool


def parse_macro_targets(text: str, branch: int = 1) -> list[MacroTarget]:
    rows: list[MacroTarget] = []
    for line in text.splitlines():
        if "[V37_MACRO_TARGET]" not in line:
            continue
        match = PATTERN.search(line)
        if match is None or int(match.group("jb")) != branch:
            continue
        rows.append(
            MacroTarget(
                interface_segment=int(match.group("iseg")),
                jday=float(match.group("jday")),
                qphys=float(match.group("qphys")),
                qcommit=float(match.group("qcommit")),
                qtarget=float(match.group("qtarget")),
                qaggregate=float(match.group("qaggregate")),
                wup=float(match.group("wup")),
                wiface=float(match.group("wiface")),
                dx=float(match.group("dx")),
                resistance_coefficient=float(match.group("rcoeff")),
                friction_coefficient=float(match.group("rfric")),
                velocity_coefficient=float(match.group("rvel")),
                valid=match.group("valid").upper() == "T",
            )
        )
    return rows


def summarize(rows: list[MacroTarget]) -> dict[str, float | int]:
    if not rows:
        raise ValueError("No V37 macro targets found")
    qphys = [row.qphys for row in rows]
    qcommit = [row.qcommit for row in rows]
    qtarget = [row.qtarget for row in rows]
    qaggregate = [row.qaggregate for row in rows if row.valid]
    qaggregate_commit = [row.qcommit for row in rows if row.valid]
    qaggregate_physical = [row.qphys for row in rows if row.valid]
    heads = [row.wup - row.wiface for row in rows]
    target_commit_ratios = [row.qtarget / row.qcommit for row in rows if abs(row.qcommit) > 1.0]
    target_physical_ratios = [row.qtarget / row.qphys for row in rows if abs(row.qphys) > 1.0]
    target_commit_gaps = [target - commit for target, commit in zip(qtarget, qcommit)]
    aggregate_commit_ratios = [
        target / commit for target, commit in zip(qaggregate, qaggregate_commit) if abs(commit) > 1.0
    ]
    required_manning = [
        BASELINE_MANNING_N
        * math.sqrt(max((row.wup - row.wiface) / row.qphys**2 - row.velocity_coefficient, 0.0) / row.friction_coefficient)
        for row in rows
        if row.valid and abs(row.qphys) > 1.0 and row.friction_coefficient > 0.0
    ]
    return {
        "count": len(rows),
        "interface_segment": rows[0].interface_segment,
        "dx_min_m": min(row.dx for row in rows),
        "dx_max_m": max(row.dx for row in rows),
        "head_mean_m": statistics.mean(heads),
        "head_min_m": min(heads),
        "head_max_m": max(heads),
        "qphys_mean_m3s": statistics.mean(qphys),
        "qcommit_mean_m3s": statistics.mean(qcommit),
        "qtarget_mean_m3s": statistics.mean(qtarget),
        "qtarget_qcommit_corr": correlation(qcommit, qtarget),
        "qtarget_qphys_corr": correlation(qphys, qtarget),
        "qtarget_per_qphys_slope": slope(qphys, qtarget),
        "qtarget_minus_qcommit_mean_m3s": statistics.mean(target_commit_gaps),
        "qtarget_minus_qcommit_rmse_m3s": math.sqrt(
            statistics.mean(value * value for value in target_commit_gaps)
        ),
        "qtarget_qcommit_ratio_median": statistics.median(target_commit_ratios),
        "qtarget_qcommit_ratio_p10": quantile(target_commit_ratios, 0.10),
        "qtarget_qcommit_ratio_p90": quantile(target_commit_ratios, 0.90),
        "qtarget_qcommit_ratio_within_20pct_fraction": sum(
            0.8 <= value <= 1.2 for value in target_commit_ratios
        )
        / len(target_commit_ratios),
        "qtarget_qphys_ratio_median": statistics.median(target_physical_ratios),
        "aggregate_valid_count": len(qaggregate),
        "qaggregate_mean_m3s": statistics.mean(qaggregate),
        "qaggregate_qcommit_corr": correlation(qaggregate_commit, qaggregate),
        "qaggregate_qphys_corr": correlation(qaggregate_physical, qaggregate),
        "qaggregate_per_qphys_slope": slope(qaggregate_physical, qaggregate),
        "qaggregate_qcommit_ratio_median": statistics.median(aggregate_commit_ratios),
        "qaggregate_qcommit_ratio_p10": quantile(aggregate_commit_ratios, 0.10),
        "qaggregate_qcommit_ratio_p90": quantile(aggregate_commit_ratios, 0.90),
        "qaggregate_qcommit_ratio_within_20pct_fraction": sum(
            0.8 <= value <= 1.2 for value in aggregate_commit_ratios
        )
        / len(aggregate_commit_ratios),
        "aggregate_required_uniform_manning_median": statistics.median(required_manning),
        "aggregate_required_uniform_manning_p10": quantile(required_manning, 0.10),
        "aggregate_required_uniform_manning_p90": quantile(required_manning, 0.90),
    }


def observation_head_check(rows: list[MacroTarget], observation_root: Path) -> dict[str, float | int]:
    """Adjust only macro head to observations; section conveyance stays unchanged."""
    _, bht = read_npt_with_header(observation_root / "el_obs_bht_2021.npt")
    _, sj = read_npt_with_header(observation_root / "el_obs_sj_2021.npt")
    sj_by_time = {round(jday, 8): stage for jday, stage in sj}
    series = {
        "head": [(row.jday, row.wup - row.wiface) for row in rows],
        "qtarget": [(row.jday, row.qtarget) for row in rows],
        "qaggregate": [(row.jday, row.qaggregate) for row in rows],
        "qphys": [(row.jday, row.qphys) for row in rows],
        "rfric": [(row.jday, row.friction_coefficient) for row in rows],
        "rvel": [(row.jday, row.velocity_coefficient) for row in rows],
    }
    observed_heads: list[float] = []
    simulated_heads: list[float] = []
    adjusted_ratios: list[float] = []
    aggregate_adjusted_ratios: list[float] = []
    observed_required_manning: list[float] = []
    for jday, bht_stage in bht:
        key = round(jday, 8)
        if key not in sj_by_time or jday < rows[0].jday or jday > rows[-1].jday:
            continue
        observed_head = bht_stage - sj_by_time[key]
        simulated_head = interpolate_series(series["head"], jday)
        qphys = interpolate_series(series["qphys"], jday)
        qtarget = interpolate_series(series["qtarget"], jday)
        qaggregate = interpolate_series(series["qaggregate"], jday)
        rfric = interpolate_series(series["rfric"], jday)
        rvel = interpolate_series(series["rvel"], jday)
        if observed_head <= 0.0 or simulated_head <= 0.0 or abs(qphys) <= 1.0:
            continue
        adjusted_target = qtarget * math.sqrt(observed_head / simulated_head)
        observed_heads.append(observed_head)
        simulated_heads.append(simulated_head)
        adjusted_ratios.append(adjusted_target / qphys)
        aggregate_adjusted_ratios.append(qaggregate * math.sqrt(observed_head / simulated_head) / qphys)
        required_scale_squared = (observed_head / qphys**2 - rvel) / rfric
        if required_scale_squared > 0.0:
            observed_required_manning.append(BASELINE_MANNING_N * math.sqrt(required_scale_squared))
    if not adjusted_ratios:
        raise ValueError("No observation-aligned V37 macro targets found")
    return {
        "observed_head_check_count": len(adjusted_ratios),
        "observed_bht_sj_head_mean_m": statistics.mean(observed_heads),
        "simulated_bht_sj_head_at_observations_mean_m": statistics.mean(simulated_heads),
        "observed_head_only_qtarget_qphys_ratio_median": statistics.median(adjusted_ratios),
        "observed_head_only_qtarget_qphys_ratio_p10": quantile(adjusted_ratios, 0.10),
        "observed_head_only_qtarget_qphys_ratio_p90": quantile(adjusted_ratios, 0.90),
        "observed_head_only_qtarget_qphys_ratio_within_20pct_fraction": sum(
            0.8 <= value <= 1.2 for value in adjusted_ratios
        )
        / len(adjusted_ratios),
        "observed_head_only_qaggregate_qphys_ratio_median": statistics.median(aggregate_adjusted_ratios),
        "observed_head_only_qaggregate_qphys_ratio_p10": quantile(aggregate_adjusted_ratios, 0.10),
        "observed_head_only_qaggregate_qphys_ratio_p90": quantile(aggregate_adjusted_ratios, 0.90),
        "observed_head_only_qaggregate_qphys_ratio_within_20pct_fraction": sum(
            0.8 <= value <= 1.2 for value in aggregate_adjusted_ratios
        )
        / len(aggregate_adjusted_ratios),
        "observed_head_required_uniform_manning_median": statistics.median(observed_required_manning),
        "observed_head_required_uniform_manning_p10": quantile(observed_required_manning, 0.10),
        "observed_head_required_uniform_manning_p90": quantile(observed_required_manning, 0.90),
    }


def write_outputs(output_dir: Path, rows: list[MacroTarget], summary: dict[str, float | int]) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    samples_path = output_dir / "macro_target_samples.csv"
    summary_path = output_dir / "macro_target_summary.csv"
    with samples_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)
    with summary_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value"])
        writer.writerows(summary.items())
    return samples_path, summary_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, default=DEFAULT_CASE)
    parser.add_argument("--branch", type=int, default=1)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--observations", type=Path, default=DEFAULT_OBSERVATIONS)
    args = parser.parse_args()
    rows = parse_macro_targets((args.case / "w2.wrn").read_text(encoding="utf-8", errors="ignore"), args.branch)
    summary = summarize(rows)
    summary.update(observation_head_check(rows, args.observations))
    write_outputs(args.output or args.case / "v37_macro_target", rows, summary)
    for key, value in summary.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
