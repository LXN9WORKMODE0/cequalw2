from __future__ import annotations

import argparse
import csv
import math
import re
import shutil
import statistics
from bisect import bisect_left
from dataclasses import dataclass
from pathlib import Path

import run_w2_v0_v1_smoke as smoke


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_CASE = REPO_ROOT / "cases" / "xld_2021_base"
WORK_ROOT = REPO_ROOT / "analysis" / ".runs" / "v21_bht_redistribution_scan"
DEFAULT_EXE = REPO_ROOT / "w2source_v455_2_11_2026" / "build_console" / "w2_v455_console.exe"
DEFAULT_TMEND = 44436.5
WINDOW_START = 44430.0
TRIBS = ["XXH", "NLJ", "JYH", "MGH", "XSJH"]
V10_PATTERN = re.compile(
    r"\[V10_TAIL_REACH\].*?JB=(?P<jb>\d+).*?QPHYS=(?P<qphys>[-+0-9.eE]+).*?QOUT=(?P<qout>[-+0-9.eE]+)",
    re.IGNORECASE,
)
V22_BOUNDARY_FLUX_PATTERN = re.compile(
    r"\[V22_BOUNDARY_FLUX\].*?JB=(?P<jb>\d+).*?QIN=(?P<qin>[-+0-9.eE]+).*?QEFF=(?P<qeff>[-+0-9.eE]+)"
    r".*?QDT_SUM=(?P<qdt_sum>[-+0-9.eE]+).*?QSS_SUM=(?P<qss_sum>[-+0-9.eE]+).*?TAIL_Q=(?P<tail_q>[-+0-9.eE]+)",
    re.IGNORECASE,
)
V23_Q_UPDATE_MODE_PATTERN = re.compile(r"\[V23_Q_UPDATE_MODE\].*?MODE=(?P<mode>\S+)", re.IGNORECASE)


@dataclass
class DualStationMetrics:
    seg2_bias: float
    seg2_rmse: float
    seg222_bias: float
    seg222_rmse: float
    head_bias: float
    head_rmse: float
    seg2_valid_count: int
    seg222_valid_count: int


def read_npt_with_header(path: Path, header_lines: int = 3) -> tuple[list[str], list[tuple[float, float]]]:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    header = lines[:header_lines]
    data: list[tuple[float, float]] = []
    for line in lines[header_lines:]:
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            data.append((float(parts[0]), float(parts[1])))
        except ValueError:
            continue
    return header, data


def write_npt_with_header(path: Path, header: list[str], data: list[tuple[float, float]]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        for line in header:
            handle.write(f"{line}\n")
        for x, y in data:
            handle.write(f"{trim_npt_float(x):>8} {trim_npt_float(y):>8}\n")


def read_two_col_csv(path: Path, header_rows: int = 3) -> tuple[list[list[str]], list[tuple[float, float]]]:
    with open(path, "r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
        rows = list(csv.reader(handle))
    header = rows[:header_rows]
    data: list[tuple[float, float]] = []
    for row in rows[header_rows:]:
        if len(row) < 2:
            continue
        try:
            data.append((float(row[0]), float(row[1])))
        except ValueError:
            continue
    return header, data


def write_two_col_csv(path: Path, header: list[list[str]], data: list[tuple[float, float]]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(header)
        for x, y in data:
            writer.writerow([trim_float(x), trim_float(y)])


def trim_float(value: float) -> str:
    if not math.isfinite(value):
        return ""
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def trim_npt_float(value: float) -> str:
    text = trim_float(value)
    if text and "." not in text and "e" not in text.lower():
        return f"{text}."
    return text


def interpolate_series(series: list[tuple[float, float]], x: float) -> float:
    if not series:
        return 0.0
    xs = [item[0] for item in series]
    idx = bisect_left(xs, x)
    if idx < len(series) and abs(series[idx][0] - x) < 1e-9:
        return series[idx][1]
    if idx == 0:
        return series[0][1]
    if idx >= len(series):
        return series[-1][1]
    x0, y0 = series[idx - 1]
    x1, y1 = series[idx]
    if x1 == x0:
        return y0
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)


def redistribute_bht_series(
    bht: list[tuple[float, float]], distributed: list[tuple[float, float]], alpha: float
) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    if alpha < 0.0 or alpha > 1.0:
        raise ValueError("alpha must be between 0 and 1")
    moved_bht = [(x, y + alpha * max(interpolate_series(distributed, x), 0.0)) for x, y in bht]
    moved_distributed = [(x, y - alpha * max(y, 0.0)) for x, y in distributed]
    return moved_bht, moved_distributed


def redistribute_bht_with_sources(
    bht: list[tuple[float, float]], sources: list[list[tuple[float, float]]], alpha: float
) -> tuple[list[tuple[float, float]], list[list[tuple[float, float]]]]:
    if alpha < 0.0 or alpha > 1.0:
        raise ValueError("alpha must be between 0 and 1")
    moved_bht = []
    for x, y in bht:
        moved = sum(alpha * max(interpolate_series(source, x), 0.0) for source in sources)
        moved_bht.append((x, y + moved))
    moved_sources = [[(x, y - alpha * max(y, 0.0)) for x, y in source] for source in sources]
    return moved_bht, moved_sources


def active_distributed_paths(case_dir: Path, scope: str) -> list[Path]:
    bht_path = case_dir / "InputFiles" / "BHT" / "DT_QIN_BHT_AVG.csv"
    if scope == "bht":
        return [bht_path]
    if scope == "all":
        return [bht_path] + [case_dir / "InputFiles" / "TRIB" / f"DT_QIN_{trib}.csv" for trib in TRIBS]
    raise ValueError(f"Unsupported scope: {scope}")


def update_bht_inputs(case_dir: Path, alpha: float, scope: str) -> dict[str, float]:
    bht_path = case_dir / "InputFiles" / "BHT" / "BHTOUTFLOW.npt"
    bht_header, bht = read_npt_with_header(bht_path)
    dist_paths = active_distributed_paths(case_dir, scope)
    headers: list[list[list[str]]] = []
    sources: list[list[tuple[float, float]]] = []
    for path in dist_paths:
        header, data = read_two_col_csv(path)
        headers.append(header)
        sources.append(data)
    if scope == "bht":
        moved_bht, first_source = redistribute_bht_series(bht, sources[0], alpha)
        moved_sources = [first_source]
    else:
        moved_bht, moved_sources = redistribute_bht_with_sources(bht, sources, alpha)
    write_npt_with_header(bht_path, bht_header, moved_bht)
    for path, header, data in zip(dist_paths, headers, moved_sources):
        write_two_col_csv(path, header, data)
    positive = []
    for source in sources:
        positive.extend(max(y, 0.0) for x, y in source if WINDOW_START <= x <= DEFAULT_TMEND)
    moved = [alpha * value for value in positive]
    return {
        "positive_dt_mean": statistics.mean(positive) if positive else float("nan"),
        "moved_dt_mean": statistics.mean(moved) if moved else float("nan"),
        "moved_dt_max": max(moved) if moved else float("nan"),
    }


def prepare_case(alpha: float, exe_path: Path, tmend: float, force: bool, scope: str) -> tuple[Path, dict[str, float]]:
    tag = f"a{int(round(alpha * 100)):02d}"
    case_dir = WORK_ROOT / f"redistribute_{scope}_{tag}_case"
    if case_dir.exists():
        if not force:
            return case_dir, {
                "positive_dt_mean": float("nan"),
                "moved_dt_mean": float("nan"),
                "moved_dt_max": float("nan"),
            }
        smoke.remove_tree(case_dir)
    shutil.copytree(SOURCE_CASE, case_dir, ignore=smoke.OUTPUT_IGNORE)
    smoke.update_tmend(case_dir / "w2_con.csv", tmend)
    smoke.stage_exe(case_dir, exe_path)
    moved_stats = update_bht_inputs(case_dir, alpha, scope)
    return case_dir, moved_stats


def parse_wl(path: Path, segments: list[int]) -> dict[int, list[tuple[float, float]]]:
    with open(path, "r", encoding="utf-8", errors="ignore", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        cols: dict[int, int] = {}
        for idx, name in enumerate(header):
            match = re.match(r"\s*SEG\s*(\d+)", name)
            if match and int(match.group(1)) in segments:
                cols[int(match.group(1))] = idx
        out = {seg: [] for seg in segments}
        for row in reader:
            if not row:
                continue
            try:
                jday = float(row[0])
            except ValueError:
                continue
            for seg, idx in cols.items():
                if idx >= len(row):
                    continue
                try:
                    out[seg].append((jday, float(row[idx])))
                except ValueError:
                    continue
    return out


def read_obs(path: Path) -> list[tuple[float, float]]:
    _, data = read_npt_with_header(path, 0)
    return data


def rmse(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values) / len(values)) if values else float("nan")


def mean(values: list[float]) -> float:
    return statistics.mean(values) if values else float("nan")


def dual_station_metrics(case_dir: Path, tmend: float) -> DualStationMetrics:
    wl = parse_wl(case_dir / "wl.csv", [2, 222])
    obs_down = [(x, y) for x, y in read_obs(SOURCE_CASE / "el_obs2021.npt") if WINDOW_START <= x <= tmend]
    obs_up = read_obs(SOURCE_CASE / "el_obs_upstream.npt")
    seg2_errors: list[float] = []
    seg222_errors: list[float] = []
    head_errors: list[float] = []
    for jday, obs222 in obs_down:
        sim222 = interpolate_series(wl[222], jday)
        obs2 = interpolate_series(obs_up, jday)
        sim2 = interpolate_series(wl[2], jday)
        if sim222 > -900.0:
            seg222_errors.append(sim222 - obs222)
        if sim2 > -900.0:
            seg2_errors.append(sim2 - obs2)
            if sim222 > -900.0:
                head_errors.append((sim2 - sim222) - (obs2 - obs222))
    return DualStationMetrics(
        seg2_bias=mean(seg2_errors),
        seg2_rmse=rmse(seg2_errors),
        seg222_bias=mean(seg222_errors),
        seg222_rmse=rmse(seg222_errors),
        head_bias=mean(head_errors),
        head_rmse=rmse(head_errors),
        seg2_valid_count=len(seg2_errors),
        seg222_valid_count=len(seg222_errors),
    )


def tail_flow_stats(warn_path: Path, branch: int = 1) -> dict[str, float]:
    qphys: list[float] = []
    qout: list[float] = []
    with open(warn_path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            match = V10_PATTERN.search(line)
            if not match:
                continue
            if int(match.group("jb")) != branch:
                continue
            qphys.append(float(match.group("qphys")))
            qout.append(float(match.group("qout")))
    diffs = [out - phys for phys, out in zip(qphys, qout)]
    return {
        "v10_count": len(qphys),
        "v10_qphys_mean": mean(qphys),
        "v10_qout_mean": mean(qout),
        "v10_qout_minus_qphys_mean": mean(diffs),
        "v10_qout_minus_qphys_min": min(diffs) if diffs else float("nan"),
        "v10_qout_minus_qphys_max": max(diffs) if diffs else float("nan"),
    }


def parse_boundary_flux_stats(warn_path: Path, branch: int = 1) -> dict[str, float]:
    qin: list[float] = []
    qeff: list[float] = []
    qdt_sum: list[float] = []
    qss_sum: list[float] = []
    tail_q: list[float] = []
    with open(warn_path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            match = V22_BOUNDARY_FLUX_PATTERN.search(line)
            if not match:
                continue
            if int(match.group("jb")) != branch:
                continue
            qin.append(float(match.group("qin")))
            qeff.append(float(match.group("qeff")))
            qdt_sum.append(float(match.group("qdt_sum")))
            qss_sum.append(float(match.group("qss_sum")))
            tail_q.append(float(match.group("tail_q")))
    return {
        "v22_count": len(qin),
        "v22_qin_mean": mean(qin),
        "v22_qeff_mean": mean(qeff),
        "v22_qdt_sum_mean": mean(qdt_sum),
        "v22_qss_sum_mean": mean(qss_sum),
        "v22_tail_q_mean": mean(tail_q),
    }


def parse_q_update_mode(warn_path: Path) -> str:
    with open(warn_path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            match = V23_Q_UPDATE_MODE_PATTERN.search(line)
            if match:
                return match.group("mode").upper()
    return ""


def parse_interface_mass_stats(warn_path: Path, branch: int = 1) -> dict[str, float]:
    matches = []
    with open(warn_path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            match = smoke.V24_INTERFACE_MASS_PATTERN.search(line)
            if match and int(match.group("jb")) == branch:
                matches.append(match)
    return {
        "v24_count": len(matches),
        "v24_tail_mass_resid_max": max((abs(float(match.group("rtail"))) for match in matches), default=0.0),
        "v24_flux_gap_max": max((abs(float(match.group("rflux"))) for match in matches), default=0.0),
        "v24_combined_mass_resid_max": max((abs(float(match.group("rcomb"))) for match in matches), default=0.0),
        "v24_segment_q_loss_max": max((abs(float(match.group("segloss"))) for match in matches), default=0.0),
    }


def parse_interface_commit_stats(warn_path: Path, branch: int = 1) -> dict[str, float | int]:
    matches = []
    with open(warn_path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            match = smoke.V24_INTERFACE_COMMIT_PATTERN.search(line)
            if match and int(match.group("jb")) == branch:
                matches.append(match)
    return {
        "v24_commit_count": len(matches),
        "v24_commit_q_gap_max": max(
            (abs(float(match.group("qres")) - float(match.group("qcommit"))) for match in matches),
            default=0.0,
        ),
        "v24_commit_eta_applied_max": max(
            (abs(float(match.group("deta_applied"))) for match in matches),
            default=0.0,
        ),
        "v24_commit_all_evaluated": int(
            bool(matches) and all(match.group("evaluated").upper() == "T" for match in matches)
        ),
    }


def result_row(
    alpha: float,
    case_dir: Path,
    smoke_result: smoke.SmokeResult,
    moved_stats: dict[str, float],
    tmend: float,
    scope: str,
) -> dict[str, str]:
    dual = dual_station_metrics(case_dir, tmend)
    tail = tail_flow_stats(smoke_result.warn_path)
    values: dict[str, float | int | str] = {
        "case": case_dir.name,
        "tmend": tmend,
        "scope": scope,
        "alpha": alpha,
        "moved_dt_mean": moved_stats["moved_dt_mean"],
        "moved_dt_max": moved_stats["moved_dt_max"],
        "tail_eta_max": smoke_result.tail_iface_resid_max_eta,
        "tail_q_max": smoke_result.tail_iface_resid_max_q,
        "seg2_bias": dual.seg2_bias,
        "seg2_rmse": dual.seg2_rmse,
        "seg222_bias": dual.seg222_bias,
        "seg222_rmse": dual.seg222_rmse,
        "head_bias": dual.head_bias,
        "head_rmse": dual.head_rmse,
        "tail_predictor_pass_count": smoke_result.tail_predictor_pass_count,
        "tail_corrector_pass_count": smoke_result.tail_corrector_pass_count,
        "tail_predictor_skip_count": smoke_result.tail_predictor_skip_count,
        "v23_q_update_mode": parse_q_update_mode(smoke_result.warn_path),
        "warn_path": str(smoke_result.warn_path),
    }
    values.update(tail)
    values.update(parse_boundary_flux_stats(smoke_result.warn_path))
    values.update(parse_interface_mass_stats(smoke_result.warn_path))
    values.update(parse_interface_commit_stats(smoke_result.warn_path))
    return {key: trim_float(value) if isinstance(value, float) else str(value) for key, value in values.items()}


def write_scan_summary(rows: list[dict[str, str]]) -> Path:
    path = WORK_ROOT / "bht_redistribution_scan_summary.csv"
    fieldnames = [
        "case",
        "tmend",
        "scope",
        "alpha",
        "moved_dt_mean",
        "moved_dt_max",
        "tail_eta_max",
        "tail_q_max",
        "seg2_bias",
        "seg2_rmse",
        "seg222_bias",
        "seg222_rmse",
        "head_bias",
        "head_rmse",
        "tail_predictor_pass_count",
        "tail_corrector_pass_count",
        "tail_predictor_skip_count",
        "v10_count",
        "v10_qphys_mean",
        "v10_qout_mean",
        "v10_qout_minus_qphys_mean",
        "v10_qout_minus_qphys_min",
        "v10_qout_minus_qphys_max",
        "v22_count",
        "v22_qin_mean",
        "v22_qeff_mean",
        "v22_qdt_sum_mean",
        "v22_qss_sum_mean",
        "v22_tail_q_mean",
        "v23_q_update_mode",
        "v24_count",
        "v24_tail_mass_resid_max",
        "v24_flux_gap_max",
        "v24_combined_mass_resid_max",
        "v24_segment_q_loss_max",
        "v24_commit_count",
        "v24_commit_q_gap_max",
        "v24_commit_eta_applied_max",
        "v24_commit_all_evaluated",
        "warn_path",
    ]
    merged: dict[str, dict[str, str]] = {}
    if path.exists():
        with open(path, "r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                merged[row["case"]] = row
    for row in rows:
        merged[row["case"]] = row
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged[key] for key in sorted(merged))
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run small BHT distributed-to-physical redistribution scans for V21.")
    parser.add_argument("--alphas", nargs="+", type=float, default=[0.05, 0.10, 0.15])
    parser.add_argument("--tmend", type=float, default=DEFAULT_TMEND)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--scope", choices=["bht", "all"], default="bht")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--prepare-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    for alpha in args.alphas:
        case_dir, moved_stats = prepare_case(alpha, args.exe, args.tmend, args.force, args.scope)
        if args.prepare_only:
            continue
        print(f"Running {case_dir.name} (alpha={alpha})", flush=True)
        smoke.run_case(case_dir)
        result = smoke.evaluate(case_dir)
        smoke.assert_v24_conservation(result)
        rows.append(result_row(alpha, case_dir, result, moved_stats, args.tmend, args.scope))
    if rows:
        summary = write_scan_summary(rows)
        print(f"Summary: {summary}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
