from __future__ import annotations

import argparse
import csv
import math
import re
import statistics
from bisect import bisect_left
from dataclasses import asdict, dataclass
from pathlib import Path

from analyze_v24_residual_structure import build_samples


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASE = REPO_ROOT / "analysis" / ".runs" / "v21_bht_redistribution_scan" / "redistribute_bht_a00_case"
PATTERN = re.compile(
    r"\[V29_ACCEPTED_TAIL\].*?JB=\s*(?P<jb>\d+)"
    r".*?JDAY=\s*(?P<jday>[-+0-9.eE]+).*?DT=\s*(?P<dt>[-+0-9.eE]+)"
    r".*?QPHYS=\s*(?P<qphys>[-+0-9.eE]+).*?QSTATE=\s*(?P<qstate>[-+0-9.eE]+)"
    r".*?QTARGET=\s*(?P<qtarget>[-+0-9.eE]+).*?QMAX=\s*(?P<qmax>[-+0-9.eE]+)"
    r".*?STORAGE=\s*(?P<storage>[-+0-9.eE]+).*?WUP=\s*(?P<wup>[-+0-9.eE]+)"
    r".*?WDN=\s*(?P<wdn>[-+0-9.eE]+).*?DVUP=\s*(?P<dvup>[-+0-9.eE]+)"
    r".*?DVDN=\s*(?P<dvdn>[-+0-9.eE]+).*?CAP=\s*(?P<cap>[TF])",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class AcceptedTailState:
    jday: float
    dt: float
    qphys: float
    qstate: float
    qtarget: float
    qmax: float
    storage: float
    wup: float
    wdn: float
    dvup: float
    dvdn: float
    cap: bool


def parse_accepted_tail(text: str, branch: int = 1) -> list[AcceptedTailState]:
    rows: list[AcceptedTailState] = []
    for line in text.splitlines():
        if "[V29_ACCEPTED_TAIL]" not in line:
            continue
        match = PATTERN.search(line)
        if match is None:
            continue
        if int(match.group("jb")) != branch:
            continue
        rows.append(
            AcceptedTailState(
                jday=float(match.group("jday")),
                dt=float(match.group("dt")),
                qphys=float(match.group("qphys")),
                qstate=float(match.group("qstate")),
                qtarget=float(match.group("qtarget")),
                qmax=float(match.group("qmax")),
                storage=float(match.group("storage")),
                wup=float(match.group("wup")),
                wdn=float(match.group("wdn")),
                dvup=float(match.group("dvup")),
                dvdn=float(match.group("dvdn")),
                cap=match.group("cap").upper() == "T",
            )
        )
    return sorted(rows, key=lambda row: row.jday)


def correlation(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2 or len(xs) != len(ys):
        return float("nan")
    xmean = statistics.mean(xs)
    ymean = statistics.mean(ys)
    xvar = sum((value - xmean) ** 2 for value in xs)
    yvar = sum((value - ymean) ** 2 for value in ys)
    if xvar <= 0.0 or yvar <= 0.0:
        return float("nan")
    return sum((x - xmean) * (y - ymean) for x, y in zip(xs, ys)) / math.sqrt(xvar * yvar)


def slope(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2 or len(xs) != len(ys):
        return float("nan")
    xmean = statistics.mean(xs)
    ymean = statistics.mean(ys)
    denominator = sum((value - xmean) ** 2 for value in xs)
    if denominator <= 0.0:
        return float("nan")
    return sum((x - xmean) * (y - ymean) for x, y in zip(xs, ys)) / denominator


def quantile(values: list[float], fraction: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    position = fraction * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] + weight * (ordered[upper] - ordered[lower])


def interpolate(points: list[tuple[float, float]], x: float) -> float | None:
    if not points or x < points[0][0] or x > points[-1][0]:
        return None
    xs = [point[0] for point in points]
    index = bisect_left(xs, x)
    if index == 0:
        return points[0][1]
    if index >= len(points):
        return points[-1][1]
    x1, y1 = points[index - 1]
    x2, y2 = points[index]
    if x2 == x1:
        return y2
    fraction = (x - x1) / (x2 - x1)
    return y1 + fraction * (y2 - y1)


def elapsed_times_days(rows: list[AcceptedTailState]) -> list[float]:
    if not rows:
        return []
    elapsed = [0.0]
    for row in rows[1:]:
        elapsed.append(elapsed[-1] + row.dt / 86400.0)
    return elapsed


def interpolate_arrays(xs: list[float], ys: list[float], x: float) -> float | None:
    if not xs or len(xs) != len(ys) or x < xs[0] or x > xs[-1]:
        return None
    index = bisect_left(xs, x)
    if index == 0:
        return ys[0]
    if index >= len(xs):
        return ys[-1]
    x1, x2 = xs[index - 1], xs[index]
    y1, y2 = ys[index - 1], ys[index]
    if x2 == x1:
        return y2
    return y1 + (x - x1) * (y2 - y1) / (x2 - x1)


def best_lag_days(
    rows: list[AcceptedTailState],
    response: list[float],
    forcing: list[float],
    max_lag: float = 1.0,
    step: float = 0.05,
) -> tuple[float, float]:
    times = elapsed_times_days(rows)
    if len(times) != len(response) or len(times) != len(forcing):
        return float("nan"), float("nan")
    best_lag = float("nan")
    best_corr = float("nan")
    count = int(round(2.0 * max_lag / step))
    for index in range(count + 1):
        lag = -max_lag + index * step
        states: list[float] = []
        inputs: list[float] = []
        for time, state in zip(times, response):
            value = interpolate_arrays(times, forcing, time - lag)
            if value is not None:
                states.append(state)
                inputs.append(value)
        corr = correlation(states, inputs)
        if math.isnan(corr):
            continue
        if math.isnan(best_corr) or corr > best_corr:
            best_lag = lag
            best_corr = corr
    return best_lag, best_corr


def best_response_lag_days(rows: list[AcceptedTailState], max_lag: float = 1.0, step: float = 0.05) -> tuple[float, float]:
    return best_lag_days(
        rows,
        [row.qstate for row in rows],
        [row.qphys for row in rows],
        max_lag,
        step,
    )


def hold_statistics(rows: list[AcceptedTailState], tolerance: float = 1.0e-6) -> tuple[int, float, float]:
    if len(rows) < 2:
        return 0, 0.0, 0.0
    held = 0
    max_hold_days = 0.0
    times = elapsed_times_days(rows)
    hold_start = times[0]
    for index, (previous, current) in enumerate(zip(rows, rows[1:]), start=1):
        if abs(current.qstate - previous.qstate) <= tolerance:
            held += 1
        else:
            max_hold_days = max(max_hold_days, times[index - 1] - hold_start)
            hold_start = times[index]
    max_hold_days = max(max_hold_days, times[-1] - hold_start)
    return held, held / (len(rows) - 1), max_hold_days


def aligned_head_decomposition(case_dir: Path, rows: list[AcceptedTailState]) -> dict[str, float | int]:
    endpoint_tolerance = max(row.dt for row in rows) / 86400.0
    samples = build_samples(case_dir, rows[0].jday, rows[-1].jday + endpoint_tolerance)
    wup_points = [(row.jday, row.wup) for row in rows]
    wdn_points = [(row.jday, row.wdn) for row in rows]
    wup_points.append((rows[-1].jday + endpoint_tolerance, rows[-1].wup))
    wdn_points.append((rows[-1].jday + endpoint_tolerance, rows[-1].wdn))
    flows: list[float] = []
    observed_upstream: list[float] = []
    upstream: list[float] = []
    interface: list[float] = []
    reservoir_station: list[float] = []
    for sample in samples:
        wup = interpolate(wup_points, sample.jday)
        wdn = interpolate(wdn_points, sample.jday)
        if wup is None or wdn is None:
            continue
        flows.append(sample.qphys)
        observed_upstream.append(sample.obs_seg2)
        upstream.append(wup)
        interface.append(wdn)
        reservoir_station.append(sample.sim_seg222)
    tail_head = [up - down for up, down in zip(upstream, interface)]
    reservoir_head = [down - station for down, station in zip(interface, reservoir_station)]
    total_head = [up - station for up, station in zip(upstream, reservoir_station)]
    return {
        "aligned_count": len(flows),
        "aligned_obs_wup_per_qphys_slope": slope(flows, observed_upstream),
        "aligned_wup_per_qphys_slope": slope(flows, upstream),
        "aligned_wdn_per_qphys_slope": slope(flows, interface),
        "aligned_seg222_per_qphys_slope": slope(flows, reservoir_station),
        "aligned_tail_head_per_qphys_slope": slope(flows, tail_head),
        "aligned_reservoir_head_per_qphys_slope": slope(flows, reservoir_head),
        "aligned_total_head_per_qphys_slope": slope(flows, total_head),
    }


def summarize(rows: list[AcceptedTailState]) -> dict[str, float | int]:
    if not rows:
        raise ValueError("No accepted V29 tail states found")
    qphys = [row.qphys for row in rows]
    qstate = [row.qstate for row in rows]
    qtarget = [row.qtarget for row in rows]
    wup = [row.wup for row in rows]
    wdn = [row.wdn for row in rows]
    head = [upstream - downstream for upstream, downstream in zip(wup, wdn)]
    storage = [row.storage for row in rows]
    dvup = [row.dvup for row in rows]
    dvdn = [row.dvdn for row in rows]
    required_fmann_scales = [row.qtarget / row.qstate for row in rows if row.qstate > 1.0]
    state_physical_gap = [state - physical for state, physical in zip(qstate, qphys)]
    state_target_gap = [state - target for state, target in zip(qstate, qtarget)]
    held_count, held_fraction, max_hold_days = hold_statistics(rows)
    best_lag, best_lag_corr = best_response_lag_days(rows)
    target_lag, target_lag_corr = best_lag_days(rows, qstate, qtarget)
    return {
        "count": len(rows),
        "start_jday": rows[0].jday,
        "end_jday": rows[-1].jday,
        "qphys_mean": statistics.mean(qphys),
        "qstate_mean": statistics.mean(qstate),
        "qtarget_mean": statistics.mean(qtarget),
        "qstate_qphys_corr": correlation(qphys, qstate),
        "qstate_qtarget_corr": correlation(qtarget, qstate),
        "qtarget_qphys_corr": correlation(qphys, qtarget),
        "qstate_per_qphys_slope": slope(qphys, qstate),
        "qtarget_per_qphys_slope": slope(qphys, qtarget),
        "wup_per_qphys_slope": slope(qphys, wup),
        "wdn_per_qphys_slope": slope(qphys, wdn),
        "head_per_qphys_slope": slope(qphys, head),
        "storage_per_qphys_slope": slope(qphys, storage),
        "profile_dvup_mean": statistics.mean(dvup),
        "profile_dvdn_mean": statistics.mean(dvdn),
        "constant_storage_wup_per_wdn_mean": statistics.mean(-down / up for up, down in zip(dvup, dvdn)),
        "wup_per_qstate_slope": slope(qstate, wup),
        "required_fmann_scale_mean": statistics.mean(required_fmann_scales),
        "required_fmann_scale_median": statistics.median(required_fmann_scales),
        "required_fmann_scale_p10": quantile(required_fmann_scales, 0.10),
        "required_fmann_scale_p90": quantile(required_fmann_scales, 0.90),
        "required_fmann_scale_within_20pct_fraction": sum(0.8 <= value <= 1.2 for value in required_fmann_scales) / len(required_fmann_scales),
        "qstate_minus_qphys_mean": statistics.mean(state_physical_gap),
        "qstate_minus_qphys_rmse": math.sqrt(statistics.mean(value * value for value in state_physical_gap)),
        "qstate_minus_qtarget_mean": statistics.mean(state_target_gap),
        "qstate_minus_qtarget_rmse": math.sqrt(statistics.mean(value * value for value in state_target_gap)),
        "cap_count": sum(row.cap for row in rows),
        "cap_fraction": sum(row.cap for row in rows) / len(rows),
        "held_transition_count": held_count,
        "held_transition_fraction": held_fraction,
        "max_qstate_hold_days": max_hold_days,
        "best_qstate_response_lag_days": best_lag,
        "best_qstate_response_lag_corr": best_lag_corr,
        "best_qtarget_response_lag_days": target_lag,
        "best_qtarget_response_lag_corr": target_lag_corr,
    }


def write_outputs(case_dir: Path, rows: list[AcceptedTailState], summary: dict[str, float | int]) -> None:
    with (case_dir / "v29_accepted_tail_samples.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(rows[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(row) for row in rows)
    with (case_dir / "v29_qstate_response_summary.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value"])
        writer.writerows(summary.items())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze accepted V29 tail Q-state response diagnostics.")
    parser.add_argument("--case", type=Path, default=DEFAULT_CASE)
    parser.add_argument("--branch", type=int, default=1)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    warn_path = args.case / "w2.wrn"
    rows = parse_accepted_tail(warn_path.read_text(encoding="utf-8", errors="ignore"), args.branch)
    summary = summarize(rows)
    summary.update(aligned_head_decomposition(args.case, rows))
    summary["profile_chain_wup_per_qphys_slope"] = (
        summary["storage_per_qphys_slope"]
        - summary["profile_dvdn_mean"] * summary["wdn_per_qphys_slope"]
    ) / summary["profile_dvup_mean"]
    summary["storage_slope_required_for_observed_wup"] = (
        summary["profile_dvup_mean"] * summary["aligned_obs_wup_per_qphys_slope"]
        + summary["profile_dvdn_mean"] * summary["aligned_wdn_per_qphys_slope"]
    )
    summary["storage_response_fraction_of_observed_requirement"] = (
        summary["storage_per_qphys_slope"] / summary["storage_slope_required_for_observed_wup"]
    )
    write_outputs(args.case, rows, summary)
    for key, value in summary.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
