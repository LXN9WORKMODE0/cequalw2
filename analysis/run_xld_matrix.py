from __future__ import annotations

import csv
import math
import re
import shutil
import statistics
import subprocess
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_CASE = REPO_ROOT / "cases" / "xld_2021_base"
WORK_ROOT = REPO_ROOT / "analysis" / ".runs" / "xld_multifactor"
CASES_ROOT = WORK_ROOT / "cases"
RESULTS_ROOT = WORK_ROOT / "results"
DEFAULT_EXE = REPO_ROOT / "w2source_v455_2_11_2026" / "build_console" / "w2_v455_console.exe"
SCREEN_START = 44430.0
SCREEN_END = 44458.0
FULL_END = 44484.0
OBS_PATH = SOURCE_CASE / "el_obs2021.npt"
BASELINE_CASE_ID = "B0"
MAX_WORKERS = 2
CASE_TIMEOUT_SECONDS = 90 * 60
PRE_TIMEOUT_SECONDS = 10 * 60
SVG_WIDTH = 900
SVG_HEIGHT = 380
TRIBS = ["XXH", "NLJ", "JYH", "MGH", "XSJH"]
DOMINANT_TRIBS = ["XXH", "NLJ", "MGH"]
MAR_TRIB = {"XXH": 60.42, "NLJ": 121.0, "JYH": 9.6, "MGH": 65.485, "XSJH": 27.18}
SEG_DIST_KM = {2: 1.555, 27: 24.725, 58: 49.875, 122: 106.685, 222: 196.035}
PROFILE_DATES = [
    datetime(2021, 8, 28).date(),
    datetime(2021, 9, 5).date(),
    datetime(2021, 9, 10).date(),
    datetime(2021, 9, 15).date(),
    datetime(2021, 10, 10).date(),
]
SUMMARY_FIELDS = [
    "case_id",
    "base_case",
    "run_window",
    "dt_mode",
    "bht_mode",
    "trib_mode",
    "geom_zone",
    "mann_scale",
    "area_scale",
    "seg222_rmse",
    "seg222_bias",
    "sep10_14_bias",
    "worst_daily_bias",
    "seg2_valid_jday",
    "h2_222_0905",
    "h2_222_0910",
    "h27_222_0910",
    "volerror_max",
    "notes",
]
OUTPUT_IGNORE = shutil.ignore_patterns(
    "wl.csv",
    "flowbal.csv",
    "w2.wrn",
    "w2.err",
    "XLD.w2l",
    "XLD_cpl.opt",
    "XLD_snp.opt",
    "XLD_spr.csv",
    "XLD_tsr_*.csv",
    "q_XLD_wdo_122.csv",
    "qwo_layers_122_.csv",
    "t_XLD_wdo_122.csv",
    "*.bak",
)


@dataclass
class CaseSpec:
    case_id: str
    stage: str
    base_case: str
    run_end: float
    dt_mode: str
    bht_mode: str
    trib_mode: str
    geom_zone: str = ""
    mann_scale: float = 1.0
    area_scale: float = 1.0
    notes: str = ""
    needs_pre: bool = False


def serial_to_dt(jday: float) -> datetime:
    return datetime(1899, 12, 30) + timedelta(days=float(jday))


def dt_to_serial(dt: datetime) -> float:
    return (dt - datetime(1899, 12, 30)).total_seconds() / 86400.0


def trim_float(value: float) -> str:
    if value != value or math.isinf(value):
        return ""
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def norm_header(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def open_text(path: Path):
    for enc in ("utf-8-sig", "gbk", "latin-1"):
        try:
            return open(path, "r", encoding=enc, errors="ignore", newline="")
        except OSError:
            continue
    return open(path, "r", encoding="latin-1", errors="ignore", newline="")


def read_csv_rows(path: Path) -> list[list[str]]:
    with open_text(path) as handle:
        return list(csv.reader(handle))


def write_csv_rows(path: Path, rows: list[list[str]]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerows(rows)


def read_two_col_csv(path: Path, header_rows: int) -> tuple[list[str], list[tuple[float, float]]]:
    rows = read_csv_rows(path)
    header = [",".join(row).rstrip(",") for row in rows[:header_rows]]
    data: list[tuple[float, float]] = []
    for row in rows[header_rows:]:
        if len(row) < 2:
            continue
        try:
            data.append((float(row[0]), float(row[1])))
        except ValueError:
            continue
    return header, data


def write_two_col_csv(path: Path, header: list[str], data: list[tuple[float, float]]) -> None:
    with open(path, "w", encoding="gbk", newline="") as handle:
        for line in header:
            handle.write(f"{line}\n")
        writer = csv.writer(handle)
        for x, y in data:
            writer.writerow([trim_float(x), trim_float(y)])


def read_npt_series(path: Path) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    with open_text(path) as handle:
        for line in handle:
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                out.append((float(parts[0]), float(parts[1])))
            except ValueError:
                continue
    return out


def interpolate(x: float, xp: list[float], fp: list[float]) -> float:
    if x <= xp[0]:
        return fp[0]
    if x >= xp[-1]:
        return fp[-1]
    lo, hi = 0, len(xp) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if xp[mid] <= x:
            lo = mid
        else:
            hi = mid
    x0, x1 = xp[lo], xp[hi]
    y0, y1 = fp[lo], fp[hi]
    if x1 == x0:
        return y0
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)


def ensure_dirs() -> None:
    for path in [WORK_ROOT, CASES_ROOT, RESULTS_ROOT]:
        path.mkdir(parents=True, exist_ok=True)


def save_summary(path: Path, rows: list[dict[str, str]]) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def parse_summary(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with open_text(path) as handle:
        return list(csv.DictReader(handle))


def merge_rows(existing: list[dict[str, str]], new_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    keyed = {row["case_id"]: row for row in existing}
    for row in new_rows:
        keyed[row["case_id"]] = row
    return sorted(keyed.values(), key=lambda row: row["case_id"])


def load_observations() -> tuple[list[float], list[float]]:
    obs = read_npt_series(OBS_PATH)
    return [j for j, _ in obs], [v for _, v in obs]


def update_tmend(w2_path: Path, tmend: float) -> None:
    with open_text(w2_path) as handle:
        lines = handle.readlines()
    for idx, line in enumerate(lines[:-1]):
        if line.startswith("TMSTRT"):
            parts = lines[idx + 1].rstrip("\r\n").split(",")
            if len(parts) < 2:
                raise RuntimeError(f"TMEND row malformed in {w2_path}")
            parts[1] = trim_float(tmend)
            lines[idx + 1] = ",".join(parts) + "\n"
            with open(w2_path, "w", encoding="gbk", newline="") as handle:
                handle.writelines(lines)
            return
    raise RuntimeError(f"TMSTRT/TMEND not found in {w2_path}")


def load_waterbalance_distributed() -> dict[str, list[tuple[float, float]]]:
    base = SOURCE_CASE / "fixtures" / "distributed_flow"
    result = {}
    _, result["BHT"] = read_two_col_csv(base / "DT_QIN_BHT.csv", 3)
    for trib in TRIBS:
        _, result[trib] = read_two_col_csv(base / f"DT_QIN_{trib}.csv", 3)
    return result


def load_dynamic_bht() -> list[tuple[float, float]]:
    _, data = read_two_col_csv(SOURCE_CASE / "InputFiles" / "BHT" / "DT_QIN_BHT.csv", 3)
    return data


def load_current_trib_distributed() -> dict[str, list[tuple[float, float]]]:
    result = {}
    for trib in TRIBS:
        _, result[trib] = read_two_col_csv(SOURCE_CASE / "InputFiles" / "TRIB" / f"DT_QIN_{trib}.csv", 3)
    return result


def load_qwb() -> list[tuple[float, float]]:
    data: list[tuple[float, float]] = []
    with open_text(SOURCE_CASE / "fixtures" / "distributed_flow" / "qwb.opt") as handle:
        for idx, line in enumerate(handle):
            if idx < 3:
                continue
            parts = [part.strip().strip(",") for part in line.split(",")]
            parts = [part for part in parts if part]
            if len(parts) < 2:
                continue
            try:
                data.append((float(parts[0]), float(parts[1])))
            except ValueError:
                continue
    return data


def scale_series(data: list[tuple[float, float]], factor: float) -> list[tuple[float, float]]:
    return [(x, y * factor) for x, y in data]


def zero_series(data: list[tuple[float, float]]) -> list[tuple[float, float]]:
    return [(x, 0.0) for x, _ in data]


def moving_average_by_time(data: list[tuple[float, float]], half_window_days: float) -> list[tuple[float, float]]:
    times = [x for x, _ in data]
    values = [y for _, y in data]
    out: list[tuple[float, float]] = []
    for i, t in enumerate(times):
        left = t - half_window_days
        right = t + half_window_days
        total = 0.0
        count = 0
        j = i
        while j >= 0 and times[j] >= left:
            total += values[j]
            count += 1
            j -= 1
        j = i + 1
        while j < len(times) and times[j] <= right:
            total += values[j]
            count += 1
            j += 1
        out.append((t, total / count if count else values[i]))
    original_mean = statistics.mean(values)
    smoothed_mean = statistics.mean(y for _, y in out)
    if abs(smoothed_mean) > 1e-12:
        factor = original_mean / smoothed_mean
        out = [(x, y * factor) for x, y in out]
    return out


def repartition_qwb(main_factor: float) -> dict[str, list[tuple[float, float]]]:
    qwb = load_qwb()
    total = sum(MAR_TRIB.values())
    result = {"BHT": [(x, y * main_factor) for x, y in qwb]}
    for trib in TRIBS:
        share = (1.0 - main_factor) * MAR_TRIB[trib] / total
        result[trib] = [(x, y * share) for x, y in qwb]
    return result


def bht_daily_factors() -> dict[tuple[int, int], dict[datetime.date, float]]:
    series = read_npt_series(SOURCE_CASE / "InputFiles" / "BHT" / "BHTOUTFLOW.npt")
    grouped = defaultdict(lambda: defaultdict(list))
    for j, flow in series:
        day = serial_to_dt(j).date()
        grouped[(day.year, day.month)][day].append(flow)
    out = {}
    for ym, per_day in grouped.items():
        day_means = {day: statistics.mean(vals) for day, vals in per_day.items()}
        month_mean = statistics.mean(day_means.values())
        out[ym] = {day: val / month_mean if month_mean else 1.0 for day, val in day_means.items()}
    return out


def reshape_qin_by_bht(data: list[tuple[float, float]]) -> list[tuple[float, float]]:
    factors = bht_daily_factors()
    grouped = defaultdict(list)
    for j, flow in data:
        dt = serial_to_dt(j)
        grouped[(dt.year, dt.month)].append((j, flow))
    out: list[tuple[float, float]] = []
    for ym, items in grouped.items():
        raw = [factors.get(ym, {}).get(serial_to_dt(j).date(), 1.0) for j, _ in items]
        mean_factor = statistics.mean(raw) if raw else 1.0
        for (j, flow), factor in zip(items, raw):
            out.append((j, flow * (factor / mean_factor if mean_factor else 1.0)))
    out.sort(key=lambda item: item[0])
    return out


def write_bht_distributed(case_dir: Path, data: list[tuple[float, float]]) -> None:
    header, _ = read_two_col_csv(case_dir / "InputFiles" / "BHT" / "DT_QIN_BHT_AVG.csv", 3)
    write_two_col_csv(case_dir / "InputFiles" / "BHT" / "DT_QIN_BHT_AVG.csv", header, data)


def write_trib_distributed(case_dir: Path, trib: str, data: list[tuple[float, float]]) -> None:
    path = case_dir / "InputFiles" / "TRIB" / f"DT_QIN_{trib}.csv"
    header, _ = read_two_col_csv(path, 3)
    write_two_col_csv(path, header, data)


def apply_geometry(case_dir: Path, spec: CaseSpec) -> None:
    if not spec.geom_zone:
        return
    zone_end = 58 if spec.geom_zone == "2-58" else 122
    target_segments = {seg for seg in range(2, zone_end + 1)}
    path = case_dir / "InputFiles" / "BTH" / "DIXING20250226.csv"
    rows = read_csv_rows(path)
    seg_row = mann_row = layer_row = None
    for idx, row in enumerate(rows):
        head = row[0].strip() if row else ""
        if head.startswith("SEG:"):
            seg_row = idx
        elif head == "MANN":
            mann_row = idx
        elif head == "LAYER":
            layer_row = idx
    if seg_row is None or mann_row is None or layer_row is None:
        raise RuntimeError("geometry anchors not found")
    seg_map = {}
    for col, cell in enumerate(rows[seg_row][1:], start=1):
        try:
            seg_map[int(cell.strip())] = col
        except ValueError:
            continue
    target_cols = [seg_map[s] for s in sorted(target_segments) if s in seg_map]
    if abs(spec.mann_scale - 1.0) > 1e-12:
        row = rows[mann_row]
        for col in target_cols:
            try:
                row[col] = trim_float(float(row[col]) * spec.mann_scale)
            except ValueError:
                continue
    if abs(spec.area_scale - 1.0) > 1e-12:
        for idx in range(layer_row + 1, len(rows)):
            row = rows[idx]
            if not row:
                continue
            try:
                float(row[0].strip())
            except ValueError:
                continue
            for col in target_cols:
                if col >= len(row):
                    continue
                try:
                    row[col] = trim_float(float(row[col]) * spec.area_scale)
                except ValueError:
                    continue
    write_csv_rows(path, rows)


def apply_qin_case(case_dir: Path, case_id: str) -> None:
    trib_modes = {
        "T1": ("scale", 0.8, set(TRIBS)),
        "T2": ("scale", 1.2, set(TRIBS)),
        "T3": ("reshape", 1.0, set(TRIBS)),
        "T4": ("reshape", 1.0, set(DOMINANT_TRIBS)),
    }
    if case_id not in trib_modes:
        return
    mode, factor, targets = trib_modes[case_id]
    for trib in TRIBS:
        path = case_dir / "InputFiles" / "TRIB" / f"QIN_{trib}.csv"
        header, data = read_two_col_csv(path, 1)
        if trib in targets:
            if mode == "scale":
                data = scale_series(data, factor)
            else:
                data = reshape_qin_by_bht(data)
        write_two_col_csv(path, header, data)


def apply_distributed(case_dir: Path, case_id: str) -> None:
    dynamic_bht = load_dynamic_bht()
    current_trib = load_current_trib_distributed()
    bht_data = dynamic_bht
    trib_data = current_trib
    if case_id == "B1":
        bht_data = zero_series(dynamic_bht)
        trib_data = {trib: zero_series(data) for trib, data in current_trib.items()}
    elif case_id == "D2":
        trib_data = {trib: zero_series(data) for trib, data in current_trib.items()}
    elif case_id == "D3":
        bht_data = zero_series(dynamic_bht)
    elif case_id == "D4":
        bht_data = scale_series(dynamic_bht, 0.5)
        trib_data = {trib: scale_series(data, 0.5) for trib, data in current_trib.items()}
    elif case_id == "D5":
        bht_data = moving_average_by_time(dynamic_bht, 0.125)
        trib_data = {trib: moving_average_by_time(data, 0.125) for trib, data in current_trib.items()}
    elif case_id == "D6":
        repart = repartition_qwb(0.3)
        bht_data = repart["BHT"]
        trib_data = {trib: repart[trib] for trib in TRIBS}
    elif case_id == "D7":
        repart = repartition_qwb(0.7)
        bht_data = repart["BHT"]
        trib_data = {trib: repart[trib] for trib in TRIBS}
    elif case_id.startswith("G") or case_id.startswith("T"):
        bht_data = zero_series(dynamic_bht)
        trib_data = {trib: zero_series(data) for trib, data in current_trib.items()}
    write_bht_distributed(case_dir, bht_data)
    for trib in TRIBS:
        write_trib_distributed(case_dir, trib, trib_data[trib])


def copy_case_tree(dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(SOURCE_CASE, dst, ignore=OUTPUT_IGNORE)
    stage_model_exe(dst)


def stage_model_exe(case_dir: Path) -> None:
    if not DEFAULT_EXE.is_file():
        raise FileNotFoundError(f"Build the console model first; executable not found: {DEFAULT_EXE}")
    shutil.copy2(DEFAULT_EXE, case_dir / "w2_v455_console.exe")


def prepare_case(spec: CaseSpec, best_geom: str | None = None, best_dist: str | None = None, best_no_dist: str | None = None) -> Path:
    case_dir = CASES_ROOT / spec.stage / spec.case_id
    if (case_dir / "_complete.flag").exists():
        return case_dir
    copy_case_tree(case_dir)
    update_tmend(case_dir / "w2_con.csv", spec.run_end)
    case_logic = logical_case_id(spec.case_id)
    if case_logic.startswith("G"):
        apply_distributed(case_dir, "B1")
        apply_geometry(case_dir, spec)
    elif case_logic.startswith("T"):
        apply_distributed(case_dir, "B1")
        if best_geom and best_geom in CASE_LIBRARY:
            apply_geometry(case_dir, CASE_LIBRARY[best_geom])
        apply_qin_case(case_dir, case_logic)
    elif case_logic.startswith("I"):
        if case_logic == "I1" and best_dist:
            apply_distributed(case_dir, best_dist)
        elif case_logic == "I2":
            apply_distributed(case_dir, "B1")
            if best_geom and best_geom in CASE_LIBRARY:
                apply_geometry(case_dir, CASE_LIBRARY[best_geom])
            if best_no_dist and best_no_dist.startswith("T"):
                apply_qin_case(case_dir, best_no_dist)
        elif case_logic == "I3":
            if best_dist:
                apply_distributed(case_dir, best_dist)
            if best_geom and best_geom in CASE_LIBRARY:
                apply_geometry(case_dir, CASE_LIBRARY[best_geom])
        elif case_logic == "I4":
            if best_dist:
                apply_distributed(case_dir, best_dist)
            if best_geom and best_geom in CASE_LIBRARY:
                apply_geometry(case_dir, CASE_LIBRARY[best_geom])
            if best_no_dist and best_no_dist.startswith("T"):
                apply_qin_case(case_dir, best_no_dist)
    else:
        apply_distributed(case_dir, case_logic)
    return case_dir


def run_exe(exe: str, cwd: Path, timeout: int, log_name: str) -> None:
    exe_path = cwd / exe
    with open(cwd / log_name, "w", encoding="utf-8") as handle:
        proc = subprocess.run([str(exe_path)], cwd=str(cwd), stdout=handle, stderr=subprocess.STDOUT, timeout=timeout, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"{exe} failed in {cwd} with exit code {proc.returncode}")


def run_case(spec: CaseSpec, best_geom: str | None = None, best_dist: str | None = None, best_no_dist: str | None = None) -> Path:
    case_dir = prepare_case(spec, best_geom, best_dist, best_no_dist)
    flag = case_dir / "_complete.flag"
    if flag.exists():
        return case_dir
    run_exe("w2_v455_console.exe", case_dir, CASE_TIMEOUT_SECONDS, "model.log")
    flag.write_text(datetime.now().isoformat(), encoding="utf-8")
    return case_dir


def read_wl(case_dir: Path, segs: list[int]) -> dict[int, list[tuple[float, float]]]:
    rows = read_csv_rows(case_dir / "wl.csv")
    header = [norm_header(h) for h in rows[0]]
    j_idx = header.index("JDAY")
    idx = {seg: header.index(f"SEG {seg}") for seg in segs}
    out = {seg: [] for seg in segs}
    for row in rows[1:]:
        try:
            j = float(row[j_idx])
        except (ValueError, IndexError):
            continue
        for seg, col in idx.items():
            if col >= len(row):
                continue
            try:
                value = float(row[col])
            except ValueError:
                continue
            if value > -900:
                out[seg].append((j, value))
    return out


def nearest_daily_value(series: list[tuple[float, float]], date: datetime.date):
    if not series:
        return None
    target = datetime.combine(date, datetime.min.time())
    return min(series, key=lambda item: abs((serial_to_dt(item[0]) - target).total_seconds()))


def max_abs_volerror(path: Path) -> float:
    rows = read_csv_rows(path)
    idx = [cell.strip() for cell in rows[0]].index("%VOLerror")
    vals = []
    for row in rows[1:]:
        if idx >= len(row):
            continue
        try:
            vals.append(abs(float(row[idx])))
        except ValueError:
            continue
    return max(vals) if vals else float("nan")


def daily_means(series: list[tuple[float, float]]) -> dict[datetime.date, float]:
    grouped = defaultdict(list)
    for j, value in series:
        grouped[serial_to_dt(j).date()].append(value)
    return {day: statistics.mean(values) for day, values in grouped.items()}


def load_daily_trib_total(case_dir: Path) -> dict[datetime.date, float]:
    daily = defaultdict(float)
    for trib in TRIBS:
        _, qin = read_two_col_csv(case_dir / "InputFiles" / "TRIB" / f"QIN_{trib}.csv", 1)
        _, dt_qin = read_two_col_csv(case_dir / "InputFiles" / "TRIB" / f"DT_QIN_{trib}.csv", 3)
        dt_map = {j: v for j, v in dt_qin}
        grouped = defaultdict(list)
        for j, value in qin:
            grouped[serial_to_dt(j).date()].append(value + dt_map.get(j, 0.0))
        for day, values in grouped.items():
            daily[day] += statistics.mean(values)
    _, bht = read_two_col_csv(case_dir / "InputFiles" / "BHT" / "DT_QIN_BHT_AVG.csv", 3)
    grouped = defaultdict(list)
    for j, value in bht:
        grouped[serial_to_dt(j).date()].append(value)
    for day, values in grouped.items():
        daily[day] += statistics.mean(values)
    return dict(daily)


def svg_polyline(points, color, xmin, xmax, ymin, ymax):
    if not points:
        return ""
    chunks = []
    for x, y in points:
        px = 50 + (x - xmin) / (xmax - xmin) * (SVG_WIDTH - 100) if xmax > xmin else SVG_WIDTH / 2
        py = 30 + (ymax - y) / (ymax - ymin) * (SVG_HEIGHT - 60) if ymax > ymin else SVG_HEIGHT / 2
        chunks.append(f"{px:.2f},{py:.2f}")
    return f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{" ".join(chunks)}" />'


def write_waterlevel_svg(case_id: str, case_dir: Path, path: Path) -> None:
    obs_j, obs_v = load_observations()
    seg222 = read_wl(case_dir, [222])[222]
    if not seg222:
        return
    obs_points = [(j, interpolate(j, obs_j, obs_v)) for j, _ in seg222]
    model_points = seg222
    all_y = [v for _, v in obs_points] + [v for _, v in model_points]
    ymin = min(all_y) - 0.5
    ymax = max(all_y) + 0.5
    xmin = model_points[0][0]
    xmax = model_points[-1][0]
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{SVG_HEIGHT}">',
        f'<rect x="0" y="0" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" fill="white" stroke="#ddd" />',
        f'<text x="20" y="20" font-size="16" font-family="Arial">SEG 222 Water Level Comparison - {case_id}</text>',
        svg_polyline(obs_points, "#1f77b4", xmin, xmax, ymin, ymax),
        svg_polyline(model_points, "#d62728", xmin, xmax, ymin, ymax),
        '<text x="60" y="40" fill="#1f77b4" font-size="12" font-family="Arial">obs</text>',
        '<text x="120" y="40" fill="#d62728" font-size="12" font-family="Arial">model</text>',
        "</svg>",
    ]
    path.write_text("\n".join(svg), encoding="utf-8")


def write_profile_svg(case_id: str, wl: dict[int, list[tuple[float, float]]], run_end: float, path: Path) -> None:
    profiles = []
    for date in PROFILE_DATES:
        if dt_to_serial(datetime.combine(date, datetime.min.time())) > run_end:
            continue
        row = []
        for seg in sorted(SEG_DIST_KM):
            point = nearest_daily_value(wl.get(seg, []), date)
            if point is not None:
                row.append((SEG_DIST_KM[seg], point[1]))
        if row:
            profiles.append((date.isoformat(), row))
    if not profiles:
        return
    all_y = [y for _, row in profiles for _, y in row]
    ymin = min(all_y) - 0.5
    ymax = max(all_y) + 0.5
    xmin = min(SEG_DIST_KM.values())
    xmax = max(SEG_DIST_KM.values())
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{SVG_HEIGHT}">',
        f'<rect x="0" y="0" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" fill="white" stroke="#ddd" />',
        f'<text x="20" y="20" font-size="16" font-family="Arial">Key Water Surface Profiles - {case_id}</text>',
    ]
    for idx, (label, row) in enumerate(profiles):
        svg.append(svg_polyline(row, colors[idx % len(colors)], xmin, xmax, ymin, ymax))
        svg.append(f'<text x="{60 + idx * 120}" y="40" fill="{colors[idx % len(colors)]}" font-size="12" font-family="Arial">{label}</text>')
    svg.append("</svg>")
    path.write_text("\n".join(svg), encoding="utf-8")


def write_case_outputs(case_id: str, case_dir: Path, run_end: float, errors: list[tuple[float, float]], wl: dict[int, list[tuple[float, float]]]) -> None:
    case_out = RESULTS_ROOT / case_id
    case_out.mkdir(parents=True, exist_ok=True)
    with open(case_out / "seg222_error.csv", "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["jday", "datetime", "error_m"])
        for j, err in errors:
            writer.writerow([trim_float(j), serial_to_dt(j).isoformat(sep=" "), trim_float(err)])
    main = daily_means(read_npt_series(case_dir / "InputFiles" / "BHT" / "BHTOUTFLOW.npt"))
    outflow = daily_means(read_npt_series(case_dir / "InputFiles" / "XLDOUTFLOW.npt"))
    trib = load_daily_trib_total(case_dir)
    days = sorted(set(main) | set(outflow) | set(trib))
    with open(case_out / "daily_flows.csv", "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "main_in", "trib_total", "outflow", "net"])
        for day in days:
            mi = main.get(day, 0.0)
            tr = trib.get(day, 0.0)
            of = outflow.get(day, 0.0)
            writer.writerow([day.isoformat(), trim_float(mi), trim_float(tr), trim_float(of), trim_float(mi + tr - of)])
    with open_text(case_dir / "w2.wrn") as src, open(case_out / "w2_events.txt", "w", encoding="utf-8") as dst:
        for line in src:
            if any(key in line for key in ("Add layer", "Subtract layer", "Add segments", "Subtract segments")):
                dst.write(line)
    write_waterlevel_svg(case_id, case_dir, case_out / "seg222_compare.svg")
    write_profile_svg(case_id, wl, run_end, case_out / "profiles.svg")


def compute_case_metrics(spec: CaseSpec, case_dir: Path) -> dict[str, str]:
    obs_j, obs_v = load_observations()
    wl = read_wl(case_dir, [2, 27, 58, 122, 222])
    seg222 = [(j, v) for j, v in wl[222] if SCREEN_START <= j <= spec.run_end]
    errors = [(j, v - interpolate(j, obs_j, obs_v)) for j, v in seg222]
    rmse = math.sqrt(sum(err * err for _, err in errors) / len(errors)) if errors else float("nan")
    bias = statistics.mean(err for _, err in errors) if errors else float("nan")
    daily_err = daily_means(errors)
    sep = [value for day, value in daily_err.items() if datetime(2021, 9, 10).date() <= day <= datetime(2021, 9, 14).date()]
    sep_bias = statistics.mean(sep) if sep else float("nan")
    worst_daily = min(daily_err.values()) if daily_err else float("nan")
    seg2_valid = wl[2][0][0] if wl[2] else float("nan")
    def diff(seg_a, seg_b, date):
        a = nearest_daily_value(wl[seg_a], date)
        b = nearest_daily_value(wl[seg_b], date)
        if a is None or b is None:
            return float("nan")
        return a[1] - b[1]
    row = {
        "case_id": logical_case_id(spec.case_id),
        "base_case": spec.base_case,
        "run_window": "screen" if spec.run_end <= SCREEN_END else "full",
        "dt_mode": spec.dt_mode,
        "bht_mode": spec.bht_mode,
        "trib_mode": spec.trib_mode,
        "geom_zone": spec.geom_zone,
        "mann_scale": trim_float(spec.mann_scale),
        "area_scale": trim_float(spec.area_scale),
        "seg222_rmse": trim_float(rmse),
        "seg222_bias": trim_float(bias),
        "sep10_14_bias": trim_float(sep_bias),
        "worst_daily_bias": trim_float(worst_daily),
        "seg2_valid_jday": trim_float(seg2_valid),
        "h2_222_0905": trim_float(diff(2, 222, datetime(2021, 9, 5).date())),
        "h2_222_0910": trim_float(diff(2, 222, datetime(2021, 9, 10).date())),
        "h27_222_0910": trim_float(diff(27, 222, datetime(2021, 9, 10).date())),
        "volerror_max": trim_float(max_abs_volerror(case_dir / "flowbal.csv")),
        "notes": spec.notes,
    }
    write_case_outputs(spec.case_id, case_dir, spec.run_end, errors, wl)
    return row


def float_or_inf(text: str) -> float:
    try:
        return float(text)
    except (TypeError, ValueError):
        return float("inf")


def pick_best(rows: list[dict[str, str]], category: str) -> str:
    filtered = []
    for row in rows:
        cid = row["case_id"]
        if category == "distributed" and not cid.startswith("D"):
            continue
        if category == "geometry" and not (cid == "B1" or cid.startswith("G")):
            continue
        if category == "no_distributed" and not (cid == "B1" or cid.startswith("G") or cid.startswith("T")):
            continue
        filtered.append(row)
    if not filtered:
        return "B1"
    filtered.sort(key=lambda row: (float_or_inf(row["seg222_rmse"]), abs(float_or_inf(row["sep10_14_bias"])), -float_or_inf(row["h2_222_0905"]), 0 if row["case_id"] in ("B1", "G1", "G2", "G3", "G4", "G5", "G6", "T1", "T2", "T3", "T4") else 1))
    return filtered[0]["case_id"]


def write_ranking(screen_rows: list[dict[str, str]], full_rows: list[dict[str, str]]) -> None:
    best_d = pick_best(screen_rows, "distributed")
    best_g = pick_best(screen_rows, "geometry")
    best_n = pick_best(screen_rows, "no_distributed")
    lines = [
        "# XLD 多因素测试排序说明",
        "",
        f"- 最佳 distributed 候选：`{best_d}`",
        f"- 最佳几何候选：`{best_g}`",
        f"- 最佳无 distributed 候选：`{best_n}`",
        "",
        "## Screen 排序",
        "",
        "| case | RMSE | Bias | Sep10-14 Bias | Worst Daily | H2-222 09/05 | H2-222 09/10 | Notes |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    ordered = sorted(screen_rows, key=lambda row: (float_or_inf(row["seg222_rmse"]), abs(float_or_inf(row["sep10_14_bias"])), -float_or_inf(row["h2_222_0905"])))
    for row in ordered:
        lines.append(f"| {row['case_id']} | {row['seg222_rmse']} | {row['seg222_bias']} | {row['sep10_14_bias']} | {row['worst_daily_bias']} | {row['h2_222_0905']} | {row['h2_222_0910']} | {row['notes']} |")
    lines.extend(["", "## Full 验证", "", "| case | RMSE | Bias | Sep10-14 Bias | Worst Daily | Notes |", "| --- | ---: | ---: | ---: | ---: | --- |"])
    for row in sorted(full_rows, key=lambda item: item["case_id"]):
        lines.append(f"| {row['case_id']} | {row['seg222_rmse']} | {row['seg222_bias']} | {row['sep10_14_bias']} | {row['worst_daily_bias']} | {row['notes']} |")
    (RESULTS_ROOT / "ranking.md").write_text("\n".join(lines), encoding="utf-8")


def make_case_library() -> dict[str, CaseSpec]:
    return {
        "B0": CaseSpec("B0", "baseline", "", FULL_END, "baseline", "avg", "dynamic", notes="current actual case"),
        "B1": CaseSpec("B1", "distributed", "B0", SCREEN_END, "screen", "zero", "zero", notes="all distributed off"),
        "D1": CaseSpec("D1", "distributed", "B0", SCREEN_END, "screen", "dynamic", "dynamic", notes="BHT dynamic"),
        "D2": CaseSpec("D2", "distributed", "B0", SCREEN_END, "screen", "dynamic", "zero", notes="BHT dynamic, trib zero"),
        "D3": CaseSpec("D3", "distributed", "B0", SCREEN_END, "screen", "zero", "dynamic", notes="BHT zero, trib dynamic"),
        "D4": CaseSpec("D4", "distributed", "B0", SCREEN_END, "screen", "dynamic*0.5", "dynamic*0.5", notes="all dynamic scaled 0.5"),
        "D5": CaseSpec("D5", "distributed", "B0", SCREEN_END, "screen", "dynamic smooth 6h", "dynamic smooth 6h", notes="all dynamic smoothed"),
        "D6": CaseSpec("D6", "distributed", "B0", SCREEN_END, "screen", "qwb repart 0.3", "qwb repart 0.3", notes="main factor 0.3"),
        "D7": CaseSpec("D7", "distributed", "B0", SCREEN_END, "screen", "qwb repart 0.7", "qwb repart 0.7", notes="main factor 0.7"),
        "G1": CaseSpec("G1", "geom", "B1", SCREEN_END, "screen", "zero", "zero", geom_zone="2-58", mann_scale=1.2, notes="MANN x1.2", needs_pre=True),
        "G2": CaseSpec("G2", "geom", "B1", SCREEN_END, "screen", "zero", "zero", geom_zone="2-58", mann_scale=0.8, notes="MANN x0.8", needs_pre=True),
        "G3": CaseSpec("G3", "geom", "B1", SCREEN_END, "screen", "zero", "zero", geom_zone="2-58", area_scale=1.1, notes="AREA x1.1", needs_pre=True),
        "G4": CaseSpec("G4", "geom", "B1", SCREEN_END, "screen", "zero", "zero", geom_zone="2-58", area_scale=0.9, notes="AREA x0.9", needs_pre=True),
        "G5": CaseSpec("G5", "geom", "B1", SCREEN_END, "screen", "zero", "zero", geom_zone="2-58", mann_scale=1.2, area_scale=0.9, notes="MANN x1.2 + AREA x0.9", needs_pre=True),
        "G6": CaseSpec("G6", "geom", "B1", SCREEN_END, "screen", "zero", "zero", geom_zone="2-122", mann_scale=1.2, area_scale=0.9, notes="MANN x1.2 + AREA x0.9 on 2-122", needs_pre=True),
        "T1": CaseSpec("T1", "trib", "best_geom", SCREEN_END, "screen", "zero", "QIN x0.8", notes="QIN x0.8", needs_pre=True),
        "T2": CaseSpec("T2", "trib", "best_geom", SCREEN_END, "screen", "zero", "QIN x1.2", notes="QIN x1.2", needs_pre=True),
        "T3": CaseSpec("T3", "trib", "best_geom", SCREEN_END, "screen", "zero", "reshape all", notes="reshape all tributaries", needs_pre=True),
        "T4": CaseSpec("T4", "trib", "best_geom", SCREEN_END, "screen", "zero", "reshape dominant", notes="reshape XXH/NLJ/MGH", needs_pre=True),
        "I1": CaseSpec("I1", "interaction", "best_d", SCREEN_END, "screen", "best_d", "best_d", notes="best distributed candidate"),
        "I2": CaseSpec("I2", "interaction", "best_t", SCREEN_END, "screen", "zero", "best_t", notes="best no distributed candidate", needs_pre=True),
        "I3": CaseSpec("I3", "interaction", "best_d+best_g", SCREEN_END, "screen", "best_d", "best_d", notes="distributed + geometry", needs_pre=True),
        "I4": CaseSpec("I4", "interaction", "best_t+best_d", SCREEN_END, "screen", "best_d", "best_t+best_d", notes="trib + distributed", needs_pre=True),
        "I1_full": CaseSpec("I1_full", "validation", "best_d", FULL_END, "full", "best_d", "best_d", notes="full validation of best distributed"),
        "I2_full": CaseSpec("I2_full", "validation", "best_t", FULL_END, "full", "zero", "best_t", notes="full validation of best no distributed", needs_pre=True),
        "I4_full": CaseSpec("I4_full", "validation", "best_t+best_d", FULL_END, "full", "best_d", "best_t+best_d", notes="full validation of combined", needs_pre=True),
    }


CASE_LIBRARY = make_case_library()


def logical_case_id(case_id: str) -> str:
    return case_id[:-5] if case_id.endswith("_full") else case_id


def baseline_row(run_end: float, case_dir: Path) -> dict[str, str]:
    spec = CaseSpec("B0", "baseline", "", run_end, "baseline", "avg", "dynamic", notes="current actual case")
    return compute_case_metrics(spec, case_dir)


def run_phase(specs: list[CaseSpec], best_geom: str | None = None, best_dist: str | None = None, best_no_dist: str | None = None) -> list[dict[str, str]]:
    rows = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {executor.submit(run_case, spec, best_geom, best_dist, best_no_dist): spec for spec in specs}
        for future in as_completed(future_map):
            spec = future_map[future]
            case_dir = future.result()
            rows.append(compute_case_metrics(spec, case_dir))
    rows.sort(key=lambda row: row["case_id"])
    return rows


def main() -> int:
    ensure_dirs()
    baseline_case = run_case(CASE_LIBRARY["B0"])
    screen_rows = merge_rows(parse_summary(RESULTS_ROOT / "summary_screen.csv"), [baseline_row(SCREEN_END, baseline_case)])
    full_rows = merge_rows(parse_summary(RESULTS_ROOT / "summary_full.csv"), [baseline_row(FULL_END, baseline_case)])
    save_summary(RESULTS_ROOT / "summary_screen.csv", screen_rows)
    save_summary(RESULTS_ROOT / "summary_full.csv", full_rows)

    screen_rows = merge_rows(screen_rows, run_phase([CASE_LIBRARY[cid] for cid in ["B1", "D1", "D2", "D3", "D4", "D5", "D6", "D7"]]))
    save_summary(RESULTS_ROOT / "summary_screen.csv", screen_rows)
    best_dist = pick_best(screen_rows, "distributed")

    screen_rows = merge_rows(screen_rows, run_phase([CASE_LIBRARY[cid] for cid in ["G1", "G2", "G3", "G4", "G5", "G6"]]))
    save_summary(RESULTS_ROOT / "summary_screen.csv", screen_rows)
    best_geom = pick_best(screen_rows, "geometry")

    screen_rows = merge_rows(screen_rows, run_phase([CASE_LIBRARY[cid] for cid in ["T1", "T2", "T3", "T4"]], best_geom=best_geom))
    save_summary(RESULTS_ROOT / "summary_screen.csv", screen_rows)
    best_no_dist = pick_best(screen_rows, "no_distributed")

    screen_rows = merge_rows(screen_rows, run_phase([CASE_LIBRARY[cid] for cid in ["I1", "I2", "I3", "I4"]], best_geom=best_geom, best_dist=best_dist, best_no_dist=best_no_dist))
    save_summary(RESULTS_ROOT / "summary_screen.csv", screen_rows)

    full_rows = merge_rows(full_rows, run_phase([CASE_LIBRARY[cid] for cid in ["I1_full", "I2_full", "I4_full"]], best_geom=best_geom, best_dist=best_dist, best_no_dist=best_no_dist))
    save_summary(RESULTS_ROOT / "summary_full.csv", full_rows)
    write_ranking(screen_rows, full_rows)
    print("Completed XLD multifactor experiment matrix.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
