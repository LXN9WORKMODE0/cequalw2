#!/usr/bin/env python3
"""Diagnose the time/flow structure of the remaining V24 water-level errors."""

from __future__ import annotations

import argparse
import csv
import math
import re
import statistics
from dataclasses import dataclass
from pathlib import Path

from run_v21_bht_redistribution_scan import (
    WINDOW_START,
    interpolate_series,
    parse_wl,
    read_npt_with_header,
    read_obs,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASE = ROOT / "analysis" / ".runs" / "v21_bht_redistribution_scan" / "redistribute_bht_a00_case"
DEFAULT_TMEND = 44436.5
V10_STAGE_PATTERN = re.compile(
    r"\[V10_TAIL_REACH\].*?JB=(?P<jb>\d+).*?QPHYS=(?P<qphys>[-+0-9.eE]+)"
    r".*?QOUT=(?P<qout>[-+0-9.eE]+).*?VOL=(?P<vol>[-+0-9.eE]+)"
    r".*?WSE_HYD=(?P<wse_hyd>[-+0-9.eE]+).*?WSE_STOR=(?P<wse_stor>[-+0-9.eE]+)",
    re.IGNORECASE,
)
@dataclass(frozen=True)
class ResidualSample:
    jday: float
    qphys: float
    obs_seg2: float
    sim_seg2: float
    obs_seg222: float
    sim_seg222: float

    @property
    def seg2_error(self) -> float:
        return self.sim_seg2 - self.obs_seg2

    @property
    def seg222_error(self) -> float:
        return self.sim_seg222 - self.obs_seg222

    @property
    def obs_head(self) -> float:
        return self.obs_seg2 - self.obs_seg222

    @property
    def sim_head(self) -> float:
        return self.sim_seg2 - self.sim_seg222

    @property
    def head_error(self) -> float:
        return self.sim_head - self.obs_head


def mean(values: list[float]) -> float:
    return statistics.mean(values) if values else float("nan")


def rmse(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values) / len(values)) if values else float("nan")


def population_std(values: list[float]) -> float:
    return statistics.pstdev(values) if values else float("nan")


def pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return float("nan")
    xmean = mean(xs)
    ymean = mean(ys)
    xvar = sum((value - xmean) ** 2 for value in xs)
    yvar = sum((value - ymean) ** 2 for value in ys)
    if xvar <= 0.0 or yvar <= 0.0:
        return float("nan")
    return sum((x - xmean) * (y - ymean) for x, y in zip(xs, ys)) / math.sqrt(xvar * yvar)


def linear_slope(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return float("nan")
    xmean = mean(xs)
    ymean = mean(ys)
    denominator = sum((value - xmean) ** 2 for value in xs)
    if denominator <= 0.0:
        return float("nan")
    return sum((x - xmean) * (y - ymean) for x, y in zip(xs, ys)) / denominator


def error_metrics(samples: list[ResidualSample]) -> dict[str, float | int]:
    seg2_errors = [sample.seg2_error for sample in samples]
    seg222_errors = [sample.seg222_error for sample in samples]
    head_errors = [sample.head_error for sample in samples]
    return {
        "count": len(samples),
        "seg2_bias": mean(seg2_errors),
        "seg2_rmse": rmse(seg2_errors),
        "seg2_std": population_std(seg2_errors),
        "seg222_bias": mean(seg222_errors),
        "seg222_rmse": rmse(seg222_errors),
        "seg222_std": population_std(seg222_errors),
        "head_bias": mean(head_errors),
        "head_rmse": rmse(head_errors),
        "head_std": population_std(head_errors),
    }


def summarize_samples(samples: list[ResidualSample]) -> dict[str, float | int]:
    summary = error_metrics(samples)
    times = [sample.jday for sample in samples]
    flows = [sample.qphys for sample in samples]
    downstream_stages = [sample.obs_seg222 for sample in samples]
    observed_heads = [sample.obs_head for sample in samples]
    simulated_heads = [sample.sim_head for sample in samples]
    observed_seg2 = [sample.obs_seg2 for sample in samples]
    simulated_seg2 = [sample.sim_seg2 for sample in samples]
    simulated_seg222 = [sample.sim_seg222 for sample in samples]
    seg2_errors = [sample.seg2_error for sample in samples]
    seg222_errors = [sample.seg222_error for sample in samples]
    head_errors = [sample.head_error for sample in samples]
    summary.update(
        {
            "qphys_mean": mean(flows),
            "qphys_min": min(flows) if flows else float("nan"),
            "qphys_max": max(flows) if flows else float("nan"),
            "corr_seg2_error_qphys": pearson(seg2_errors, flows),
            "corr_seg222_error_qphys": pearson(seg222_errors, flows),
            "corr_head_error_qphys": pearson(head_errors, flows),
            "corr_seg2_error_downstream_stage": pearson(seg2_errors, downstream_stages),
            "corr_head_error_observed_head": pearson(head_errors, observed_heads),
            "corr_seg2_error_seg222_error": pearson(seg2_errors, seg222_errors),
            "obs_seg2_q_slope_m_per_m3s": linear_slope(flows, observed_seg2),
            "sim_seg2_q_slope_m_per_m3s": linear_slope(flows, simulated_seg2),
            "obs_seg222_q_slope_m_per_m3s": linear_slope(flows, downstream_stages),
            "sim_seg222_q_slope_m_per_m3s": linear_slope(flows, simulated_seg222),
            "obs_head_q_slope_m_per_m3s": linear_slope(flows, observed_heads),
            "sim_head_q_slope_m_per_m3s": linear_slope(flows, simulated_heads),
            "seg2_error_trend_m_per_day": linear_slope(times, seg2_errors),
            "seg222_error_trend_m_per_day": linear_slope(times, seg222_errors),
            "head_error_trend_m_per_day": linear_slope(times, head_errors),
        }
    )
    if samples:
        seg2_min = min(samples, key=lambda sample: sample.seg2_error)
        seg2_max = max(samples, key=lambda sample: sample.seg2_error)
        head_min = min(samples, key=lambda sample: sample.head_error)
        head_max = max(samples, key=lambda sample: sample.head_error)
        summary.update(
            {
                "seg2_error_min": seg2_min.seg2_error,
                "seg2_error_min_jday": seg2_min.jday,
                "seg2_error_max": seg2_max.seg2_error,
                "seg2_error_max_jday": seg2_max.jday,
                "head_error_min": head_min.head_error,
                "head_error_min_jday": head_min.jday,
                "head_error_max": head_max.head_error,
                "head_error_max_jday": head_max.jday,
            }
        )
    return summary


def build_samples(case_dir: Path, start: float, tmend: float) -> list[ResidualSample]:
    wl = parse_wl(case_dir / "wl.csv", [2, 222])
    obs_down = [(x, y) for x, y in read_obs(ROOT / "cases" / "xld_2021_base" / "el_obs2021.npt") if start <= x <= tmend]
    obs_up = read_obs(ROOT / "cases" / "xld_2021_base" / "el_obs_upstream.npt")
    _, qphys = read_npt_with_header(case_dir / "InputFiles" / "BHT" / "BHTOUTFLOW.npt")
    samples: list[ResidualSample] = []
    for jday, obs_seg222 in obs_down:
        sample = ResidualSample(
            jday=jday,
            qphys=interpolate_series(qphys, jday),
            obs_seg2=interpolate_series(obs_up, jday),
            sim_seg2=interpolate_series(wl[2], jday),
            obs_seg222=obs_seg222,
            sim_seg222=interpolate_series(wl[222], jday),
        )
        if min(sample.sim_seg2, sample.sim_seg222, sample.obs_seg2, sample.obs_seg222) <= -900.0:
            continue
        samples.append(sample)
    return samples


def summarize_tail_stage_markers(warn_path: Path, branch: int = 1) -> dict[str, float | int]:
    qphys: list[float] = []
    qout: list[float] = []
    wse_hyd: list[float] = []
    with open(warn_path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            match = V10_STAGE_PATTERN.search(line)
            if not match or int(match.group("jb")) != branch:
                continue
            qphys.append(float(match.group("qphys")))
            qout.append(float(match.group("qout")))
            wse_hyd.append(float(match.group("wse_hyd")))
    return {
        "v10_all_call_count": len(qphys),
        "v10_wse_hyd_min": min(wse_hyd) if wse_hyd else float("nan"),
        "v10_wse_hyd_max": max(wse_hyd) if wse_hyd else float("nan"),
        "v10_wse_hyd_range": max(wse_hyd)-min(wse_hyd) if wse_hyd else float("nan"),
        "v10_wse_hyd_qphys_slope_m_per_m3s": linear_slope(qphys, wse_hyd),
        "v10_wse_hyd_qout_slope_m_per_m3s": linear_slope(qout, wse_hyd),
    }

def daily_groups(samples: list[ResidualSample]) -> list[tuple[int, list[ResidualSample]]]:
    groups: dict[int, list[ResidualSample]] = {}
    for sample in samples:
        groups.setdefault(math.floor(sample.jday), []).append(sample)
    return [(day, groups[day]) for day in sorted(groups)]


def flow_quantile_groups(samples: list[ResidualSample], group_count: int = 4) -> list[tuple[int, list[ResidualSample]]]:
    ordered = sorted(samples, key=lambda sample: sample.qphys)
    groups: list[tuple[int, list[ResidualSample]]] = []
    for index in range(group_count):
        start = index * len(ordered) // group_count
        end = (index + 1) * len(ordered) // group_count
        if start < end:
            groups.append((index + 1, ordered[start:end]))
    return groups


def write_samples(path: Path, samples: list[ResidualSample]) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "jday",
                "qphys",
                "obs_seg2",
                "sim_seg2",
                "seg2_error",
                "obs_seg222",
                "sim_seg222",
                "seg222_error",
                "obs_head",
                "sim_head",
                "head_error",
            ]
        )
        for sample in samples:
            writer.writerow(
                [
                    sample.jday,
                    sample.qphys,
                    sample.obs_seg2,
                    sample.sim_seg2,
                    sample.seg2_error,
                    sample.obs_seg222,
                    sample.sim_seg222,
                    sample.seg222_error,
                    sample.obs_head,
                    sample.sim_head,
                    sample.head_error,
                ]
            )


def write_group_metrics(path: Path, group_name: str, groups: list[tuple[int, list[ResidualSample]]]) -> None:
    fieldnames = [
        group_name,
        "count",
        "qphys_min",
        "qphys_mean",
        "qphys_max",
        "seg2_bias",
        "seg2_rmse",
        "seg2_std",
        "seg222_bias",
        "seg222_rmse",
        "seg222_std",
        "head_bias",
        "head_rmse",
        "head_std",
    ]
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for group, samples in groups:
            flows = [sample.qphys for sample in samples]
            row: dict[str, float | int] = {
                group_name: group,
                "qphys_min": min(flows),
                "qphys_mean": mean(flows),
                "qphys_max": max(flows),
            }
            row.update(error_metrics(samples))
            writer.writerow(row)


def write_summary(path: Path, summary: dict[str, float | int]) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value"])
        for key, value in summary.items():
            writer.writerow([key, value])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, default=DEFAULT_CASE)
    parser.add_argument("--start", type=float, default=WINDOW_START)
    parser.add_argument("--tmend", type=float, default=DEFAULT_TMEND)
    parser.add_argument("--output-dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    case_dir = args.case.resolve()
    output_dir = args.output_dir.resolve() if args.output_dir else case_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    samples = build_samples(case_dir, args.start, args.tmend)
    if not samples:
        raise RuntimeError("No aligned V24 residual samples were found")
    summary = summarize_samples(samples)
    summary.update(summarize_tail_stage_markers(case_dir / "w2.wrn"))
    write_samples(output_dir / "v24_residual_samples.csv", samples)
    write_group_metrics(output_dir / "v24_residual_daily.csv", "day", daily_groups(samples))
    write_group_metrics(output_dir / "v24_residual_flow_quartiles.csv", "flow_quartile", flow_quantile_groups(samples))
    write_summary(output_dir / "v24_residual_summary.csv", summary)
    for key, value in summary.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
