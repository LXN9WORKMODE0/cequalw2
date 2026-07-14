from __future__ import annotations

import csv
import math
import re
import statistics
from bisect import bisect_left
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ACTUAL_CASE = REPO_ROOT / "cases" / "xld_2021_base"
MULTI_ROOT = REPO_ROOT / "analysis" / ".runs" / "xld_multifactor"
OUT_ROOT = MULTI_ROOT / "dual_station_review"
SCREEN_START = 44430.0
SCREEN_END = 44458.0
FULL_END = 44484.0
SVG_W = 1200
SVG_H = 980
PLOT_CASES = ["B0", "D1", "D7", "G6", "T2", "I3", "I4"]
PLOT_COLORS = {
    "OBS": "#111111",
    "B0": "#1f77b4",
    "D1": "#2ca02c",
    "D7": "#d62728",
    "G6": "#9467bd",
    "T2": "#8c564b",
    "I3": "#ff7f0e",
    "I4": "#17becf",
}
LABELS = {
    "B0": "B0 current actual",
    "B1": "B1 no distributed",
    "D1": "D1 dynamic distributed",
    "D5": "D5 smoothed distributed",
    "D6": "D6 qwb repart 0.3",
    "D7": "D7 qwb repart 0.7",
    "G6": "G6 MANN x1.2 + AREA x0.9",
    "T2": "T2 G6 + QIN x1.2",
    "I1": "I1 best distributed",
    "I3": "I3 distributed + geometry",
    "I4": "I4 distributed + trib",
}
SUMMARY_FIELDS = [
    "case_id",
    "window",
    "seg222_rmse",
    "seg222_bias",
    "seg2_rmse_valid",
    "seg2_bias_valid",
    "seg2_valid_fraction",
    "seg2_first_valid_jday",
    "seg2_first_valid_dt",
    "head_rmse_valid",
    "head_bias_valid",
    "head_obs_mean",
    "head_sim_mean_valid",
    "head_obs_2021_08_22",
    "head_sim_2021_08_22",
    "head_obs_2021_08_28",
    "head_sim_2021_08_28",
    "head_obs_2021_09_05",
    "head_sim_2021_09_05",
    "head_obs_2021_09_10",
    "head_sim_2021_09_10",
    "notes",
]


@dataclass
class WindowSpec:
    name: str
    start: float
    end: float


def serial_to_date_label(jday: float) -> str:
    import datetime as dt

    origin = dt.datetime(1899, 12, 30)
    value = origin + dt.timedelta(days=float(jday))
    return value.strftime("%Y-%m-%d %H:%M")


def trim(value: float | None) -> str:
    if value is None or math.isnan(value) or math.isinf(value):
        return ""
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def mean(values: list[float]) -> float | None:
    return statistics.mean(values) if values else None


def rmse(values: list[float]) -> float | None:
    if not values:
        return None
    return math.sqrt(sum(v * v for v in values) / len(values))


def read_npt(path: Path) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                out.append((float(parts[0]), float(parts[1])))
            except ValueError:
                continue
    return out


def parse_wl(path: Path, segments: list[int]) -> dict[int, list[tuple[float, float]]]:
    with open(path, "r", encoding="utf-8", errors="ignore", newline="") as handle:
        reader = csv.reader(handle)
        rows = iter(reader)
        header = next(rows)
        seg_cols: dict[int, int] = {}
        for idx, name in enumerate(header):
            m = re.match(r"\s*SEG\s*(\d+)\s*", name)
            if m:
                seg = int(m.group(1))
                if seg in segments:
                    seg_cols[seg] = idx
        result = {seg: [] for seg in segments}
        for row in rows:
            if not row:
                continue
            try:
                jday = float(row[0])
            except ValueError:
                continue
            for seg in segments:
                idx = seg_cols.get(seg)
                if idx is None or idx >= len(row):
                    continue
                try:
                    value = float(row[idx])
                except ValueError:
                    continue
                result[seg].append((jday, value))
    return result


def filter_series(data: list[tuple[float, float]], window: WindowSpec) -> list[tuple[float, float]]:
    return [(x, y) for x, y in data if window.start <= x <= window.end]


def interpolate_value(series: list[tuple[float, float]], x: float, require_wet: bool = False) -> float | None:
    if not series:
        return None
    xs = [p[0] for p in series]
    ys = [p[1] for p in series]
    if x < xs[0] or x > xs[-1]:
        return None
    idx = bisect_left(xs, x)
    if idx < len(xs) and abs(xs[idx] - x) < 1e-9:
        y = ys[idx]
        if require_wet and y <= -900.0:
            return None
        return y
    if idx == 0 or idx >= len(xs):
        return None
    x0, y0 = xs[idx - 1], ys[idx - 1]
    x1, y1 = xs[idx], ys[idx]
    if require_wet and (y0 <= -900.0 or y1 <= -900.0):
        return None
    if x1 == x0:
        y = y0
    else:
        y = y0 + (x - x0) * (y1 - y0) / (x1 - x0)
    if require_wet and y <= -900.0:
        return None
    return y


def case_wl_path(case_id: str, window_name: str) -> Path:
    if window_name == "screen":
        if case_id == "B0":
            return MULTI_ROOT / "cases" / "baseline" / "B0" / "wl.csv"
        if case_id in {"B1", "D1", "D2", "D3", "D4", "D5", "D6", "D7"}:
            return MULTI_ROOT / "cases" / "distributed" / case_id / "wl.csv"
        if case_id.startswith("G"):
            return MULTI_ROOT / "cases" / "geom" / case_id / "wl.csv"
        if case_id.startswith("T"):
            return MULTI_ROOT / "cases" / "trib" / case_id / "wl.csv"
        if case_id.startswith("I"):
            return MULTI_ROOT / "cases" / "interaction" / case_id / "wl.csv"
    else:
        if case_id == "B0":
            return MULTI_ROOT / "cases" / "baseline" / "B0" / "wl.csv"
        return MULTI_ROOT / "cases" / "validation" / f"{case_id}_full" / "wl.csv"
    raise FileNotFoundError(f"No case mapping for {case_id} / {window_name}")


def load_case_ids(summary_path: Path) -> list[str]:
    with open(summary_path, "r", encoding="utf-8-sig", newline="") as handle:
        return [row["case_id"] for row in csv.DictReader(handle)]


def obs_timeseries(window: WindowSpec) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    downstream = filter_series(read_npt(ACTUAL_CASE / "el_obs2021.npt"), window)
    upstream = filter_series(read_npt(ACTUAL_CASE / "el_obs_upstream.npt"), window)
    return downstream, upstream


def align_obs(downstream: list[tuple[float, float]], upstream: list[tuple[float, float]]) -> list[tuple[float, float, float]]:
    up_x = [x for x, _ in upstream]
    up_y = [y for _, y in upstream]
    out: list[tuple[float, float, float]] = []
    for x, y_down in downstream:
        if not up_x:
            continue
        if x < up_x[0] or x > up_x[-1]:
            continue
        y_up = interpolate_value(upstream, x)
        if y_up is None:
            continue
        out.append((x, y_up, y_down))
    return out


def evaluate_case(case_id: str, window: WindowSpec, obs_aligned: list[tuple[float, float, float]]) -> dict[str, str]:
    wl = parse_wl(case_wl_path(case_id, window.name), [2, 27, 58, 122, 222])
    seg2 = wl[2]
    seg222 = wl[222]

    seg222_errors: list[float] = []
    seg2_errors: list[float] = []
    head_errors: list[float] = []
    head_obs_values: list[float] = []
    head_sim_values: list[float] = []
    valid_count = 0
    first_valid_jday: float | None = None

    key_targets = {
        "2021_08_22": 44430.0,
        "2021_08_28": 44436.0,
        "2021_09_05": 44444.0,
        "2021_09_10": 44449.0,
    }
    key_values: dict[str, float | None] = {}

    for jday, obs_up, obs_down in obs_aligned:
        sim_down = interpolate_value(seg222, jday, require_wet=False)
        if sim_down is not None:
            seg222_errors.append(sim_down - obs_down)
        sim_up = interpolate_value(seg2, jday, require_wet=True)
        if sim_up is not None:
            if first_valid_jday is None:
                first_valid_jday = jday
            valid_count += 1
            seg2_errors.append(sim_up - obs_up)
            head_obs = obs_up - obs_down
            head_sim = sim_up - sim_down if sim_down is not None else None
            if head_sim is not None:
                head_obs_values.append(head_obs)
                head_sim_values.append(head_sim)
                head_errors.append(head_sim - head_obs)

    total_count = len(obs_aligned)
    for tag, key_jday in key_targets.items():
        obs_down = interpolate_value([(x, y) for x, _, y in obs_aligned], key_jday)
        obs_up = interpolate_value([(x, y) for x, y, _ in obs_aligned], key_jday)
        sim_down = interpolate_value(seg222, key_jday, require_wet=False)
        sim_up = interpolate_value(seg2, key_jday, require_wet=True)
        key_values[f"head_obs_{tag}"] = None if obs_up is None or obs_down is None else obs_up - obs_down
        key_values[f"head_sim_{tag}"] = None if sim_up is None or sim_down is None else sim_up - sim_down

    return {
        "case_id": case_id,
        "window": window.name,
        "seg222_rmse": trim(rmse(seg222_errors)),
        "seg222_bias": trim(mean(seg222_errors)),
        "seg2_rmse_valid": trim(rmse(seg2_errors)),
        "seg2_bias_valid": trim(mean(seg2_errors)),
        "seg2_valid_fraction": trim(valid_count / total_count if total_count else float("nan")),
        "seg2_first_valid_jday": trim(first_valid_jday),
        "seg2_first_valid_dt": serial_to_date_label(first_valid_jday) if first_valid_jday is not None else "",
        "head_rmse_valid": trim(rmse(head_errors)),
        "head_bias_valid": trim(mean(head_errors)),
        "head_obs_mean": trim(mean(head_obs_values)),
        "head_sim_mean_valid": trim(mean(head_sim_values)),
        "head_obs_2021_08_22": trim(key_values["head_obs_2021_08_22"]),
        "head_sim_2021_08_22": trim(key_values["head_sim_2021_08_22"]),
        "head_obs_2021_08_28": trim(key_values["head_obs_2021_08_28"]),
        "head_sim_2021_08_28": trim(key_values["head_sim_2021_08_28"]),
        "head_obs_2021_09_05": trim(key_values["head_obs_2021_09_05"]),
        "head_sim_2021_09_05": trim(key_values["head_sim_2021_09_05"]),
        "head_obs_2021_09_10": trim(key_values["head_obs_2021_09_10"]),
        "head_sim_2021_09_10": trim(key_values["head_sim_2021_09_10"]),
        "notes": LABELS.get(case_id, ""),
    }


def save_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def value_range(series_groups: list[list[tuple[float, float]]]) -> tuple[float, float]:
    values = [y for group in series_groups for _, y in group if y > -900.0]
    if not values:
        return 0.0, 1.0
    vmin = min(values)
    vmax = max(values)
    pad = max((vmax - vmin) * 0.06, 0.5)
    return vmin - pad, vmax + pad


def scale_x(x: float, x0: float, x1: float, left: float, width: float) -> float:
    if x1 == x0:
        return left
    return left + (x - x0) * width / (x1 - x0)


def scale_y(y: float, y0: float, y1: float, top: float, height: float) -> float:
    if y1 == y0:
        return top + height / 2
    return top + (y1 - y) * height / (y1 - y0)


def svg_polyline(series: list[tuple[float, float]], x0: float, x1: float, y0: float, y1: float, left: float, top: float, width: float, height: float) -> str:
    chunks: list[str] = []
    current: list[str] = []
    for x, y in series:
        if y <= -900.0 or x < x0 or x > x1:
            if len(current) >= 2:
                chunks.append(" ".join(current))
            current = []
            continue
        current.append(f"{scale_x(x, x0, x1, left, width):.2f},{scale_y(y, y0, y1, top, height):.2f}")
    if len(current) >= 2:
        chunks.append(" ".join(current))
    return "".join(f'<polyline fill="none" stroke-linecap="round" stroke-linejoin="round" points="{pts}"/>' for pts in chunks)


def plot_series() -> None:
    window = WindowSpec("screen", SCREEN_START, SCREEN_END)
    down_obs, up_obs = obs_timeseries(window)
    aligned = align_obs(down_obs, up_obs)
    obs_down = [(x, y) for x, _, y in aligned]
    obs_up = [(x, y) for x, y, _ in aligned]
    obs_head = [(x, y_up - y_down) for x, y_up, y_down in aligned]

    case_series: dict[str, dict[str, list[tuple[float, float]]]] = {}
    for case_id in PLOT_CASES:
        wl = parse_wl(case_wl_path(case_id, window.name), [2, 222])
        up: list[tuple[float, float]] = []
        down: list[tuple[float, float]] = []
        head: list[tuple[float, float]] = []
        for x, _, _ in aligned:
            sim_up = interpolate_value(wl[2], x, require_wet=True)
            sim_down = interpolate_value(wl[222], x, require_wet=False)
            if sim_down is not None:
                down.append((x, sim_down))
            if sim_up is not None:
                up.append((x, sim_up))
            if sim_up is not None and sim_down is not None:
                head.append((x, sim_up - sim_down))
            else:
                head.append((x, -999.0))
        case_series[case_id] = {"up": up, "down": down, "head": head}

    panels = [
        ("Upstream SEG 2 vs el_obs_upstream", obs_up, [case_series[c]["up"] for c in PLOT_CASES]),
        ("Downstream SEG 222 vs el_obs2021", obs_down, [case_series[c]["down"] for c in PLOT_CASES]),
        ("Head Difference SEG 2 - SEG 222", obs_head, [case_series[c]["head"] for c in PLOT_CASES]),
    ]

    left = 80
    top0 = 70
    panel_h = 240
    panel_gap = 55
    width = 950
    svg: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}" viewBox="0 0 {SVG_W} {SVG_H}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Consolas,Segoe UI,sans-serif;fill:#111} .axis{stroke:#999;stroke-width:1} .obs{stroke:#111;stroke-width:2.5} .case{stroke-width:1.8;fill:none} .label{font-size:14px} .small{font-size:12px;fill:#555}</style>',
        '<text x="80" y="34" font-size="20">XLD Dual-Station Waterline Review (screen window)</text>',
        '<text x="80" y="54" class="small">Obs: SEG 2 upstream + SEG 222 dam front. Compare level fit and head-difference fit separately.</text>',
    ]

    for idx, (title, obs_series, sim_groups) in enumerate(panels):
        top = top0 + idx * (panel_h + panel_gap)
        y0, y1 = value_range([obs_series] + sim_groups)
        svg.append(f'<text x="{left}" y="{top - 14}" class="label">{title}</text>')
        svg.append(f'<rect x="{left}" y="{top}" width="{width}" height="{panel_h}" fill="none" class="axis"/>')
        for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
            yv = y0 + (y1 - y0) * frac
            py = scale_y(yv, y0, y1, top, panel_h)
            svg.append(f'<line x1="{left}" y1="{py:.2f}" x2="{left + width}" y2="{py:.2f}" stroke="#eee"/>')
            svg.append(f'<text x="{left - 10}" y="{py + 4:.2f}" text-anchor="end" class="small">{yv:.2f}</text>')
        for step in range(0, 29, 4):
            xj = SCREEN_START + step
            px = scale_x(xj, SCREEN_START, SCREEN_END, left, width)
            svg.append(f'<line x1="{px:.2f}" y1="{top}" x2="{px:.2f}" y2="{top + panel_h}" stroke="#f2f2f2"/>')
            svg.append(f'<text x="{px:.2f}" y="{top + panel_h + 18}" text-anchor="middle" class="small">{serial_to_date_label(xj)[:10]}</text>')

        svg.append(f'<g class="obs">{svg_polyline(obs_series, SCREEN_START, SCREEN_END, y0, y1, left, top, width, panel_h)}</g>')
        for case_id in PLOT_CASES:
            color = PLOT_COLORS[case_id]
            svg.append(f'<g class="case" stroke="{color}">{svg_polyline(case_series[case_id]["up" if idx == 0 else "down" if idx == 1 else "head"], SCREEN_START, SCREEN_END, y0, y1, left, top, width, panel_h)}</g>')

    legend_x = 1055
    legend_y = 110
    legend_items = [("OBS", "Observed")] + [(cid, LABELS.get(cid, cid)) for cid in PLOT_CASES]
    for i, (cid, label) in enumerate(legend_items):
        y = legend_y + i * 24
        color = PLOT_COLORS[cid]
        svg.append(f'<line x1="{legend_x}" y1="{y}" x2="{legend_x + 26}" y2="{y}" stroke="{color}" stroke-width="3"/>')
        svg.append(f'<text x="{legend_x + 34}" y="{y + 4}" class="small">{label}</text>')

    svg.append("</svg>")
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "dual_station_screen.svg").write_text("".join(svg), encoding="utf-8")


def build_report(screen_rows: list[dict[str, str]], full_rows: list[dict[str, str]]) -> None:
    screen_map = {row["case_id"]: row for row in screen_rows}
    full_map = {row["case_id"]: row for row in full_rows}

    def line(case_id: str) -> str:
        row = screen_map[case_id]
        return (
            f"- `{case_id}`: SEG222 RMSE `{row['seg222_rmse']} m`, "
            f"SEG2 valid RMSE `{row['seg2_rmse_valid'] or 'n/a'} m`, "
            f"SEG2 valid fraction `{row['seg2_valid_fraction'] or 'n/a'}`, "
            f"head RMSE `{row['head_rmse_valid'] or 'n/a'} m`, "
            f"SEG2 first valid `{row['seg2_first_valid_dt'] or 'never'}`."
        )

    text = [
        "# Dual-Station Waterline Review",
        "",
        "本页回答什么问题：在已跑过的 XLD case 中，哪些方案只是把坝前 `SEG 222` 水位贴近实测，哪些方案同时也让库尾 `SEG 2` 和 `SEG 2-SEG 222` 的水面差更接近真实水面线。",
        "",
        "## 1. 前提",
        "",
        "- 本分析把 `el_obs2021.npt` 视为坝前 `SEG 222` 实测水位，把 `el_obs_upstream.npt` 视为库尾 `SEG 2` 实测水位。",
        "- 结论成立的前提是这两个实测文件与模型输出使用同一高程基准，且用户给出的 `SEG 2 / SEG 222` 对应关系正确。",
        "- 若这两个前提任一不成立，本页结论只能作为定位问题的线索，不能直接作为水动力优劣判断。",
        "",
        "## 2. 关键判断",
        "",
        "- `distributed` 方案确实能显著改善坝前 `SEG 222`，但不能据此判定水面线合理。",
        "- 从双站点结果看，当前各方案不是单一偏差，而是两个问题叠加：`SEG 2` 过晚淹没，以及一旦成水后 `SEG 2-SEG 222` 水面差又塌得过快。",
        "- 也就是说，模型既没有把库尾回水足够早地传到上游，也没有把成水后的纵向坡度维持在实测水平上。",
        "- 这意味着前一次只看坝前水位得到的结论不完整。坝前贴合不能替代水面线贴合。",
        "",
        "## 3. 代表性 case",
        "",
        line("B0"),
        line("D1"),
        line("D7"),
        line("G6"),
        line("T2"),
        line("I3"),
        line("I4"),
        "",
        "## 4. 直接结论",
        "",
        f"- 观测两点水面差在 `2021-08-22` 为 `{screen_map['B0']['head_obs_2021_08_22']} m`，到 `2021-09-10` 仍有 `{screen_map['B0']['head_obs_2021_09_10']} m`。这说明实测并不是快速平库，而是存在持续的纵向水面坡降。",
        f"- 当前实际 case `B0` 直到 `{screen_map['B0']['seg2_first_valid_dt']}` 才在 `SEG 2` 形成连续水面；在此之前，库尾观测已经处于高水位。这说明回水淹没前沿到达库尾的时机被明显推迟了。",
        f"- `D7` 虽然把坝前 RMSE 压到了 `{screen_map['D7']['seg222_rmse']} m`，但它的库尾首次成水面时间是 `{screen_map['D7']['seg2_first_valid_dt']}`，而且 `2021-09-10` 的模拟两点水面差只有 `{screen_map['D7']['head_sim_2021_09_10'] or 'n/a'} m`。这说明 distributed 更像是在补总水量和坝前水位，不是在修正真实回水传播。",
        f"- `G6` 把坡度做陡了一些，`2021-09-10` 两点水面差到了 `{screen_map['G6']['head_sim_2021_09_10'] or 'n/a'} m`，但坝前 RMSE 恶化到 `{screen_map['G6']['seg222_rmse']} m`。这说明单独调糙率/面积是在改坡度，不是在同时修正整体蓄量和边界传播。",
        f"- `T2` 是“增大支流流量”的代表试验之一，但在本轮设定下仍不能同时满足两端：坝前 RMSE `{screen_map['T2']['seg222_rmse']} m`，有效库尾 RMSE `{screen_map['T2']['seg2_rmse_valid'] or 'n/a'} m`，两点水面差 RMSE `{screen_map['T2']['head_rmse_valid'] or 'n/a'} m`。",
        f"- `I3/I4` 说明把 distributed 与几何或支流调整叠加后，并没有自然得到更合理的双站点水面线；至少在当前参数幅度内，这两类修正不是简单互补关系。",
        f"- 从目标拆分看，`D1/D7` 最擅长修坝前，`G5/G6/T2` 这类方案更擅长把两点水面差做大，但没有任何 case 同时把坝前、库尾和水面差三个目标一起压到合理水平。",
        "",
        "## 5. 工程解释",
        "",
        "- 如果一个方案只把坝前水位贴住，但库尾仍长期偏低或甚至不成连续水面，那么这个方案不能被解释为“水动力更合理”，只能被解释为“局部水位或总体库容被调对了”。",
        "- 如果一个方案让库尾终于提前成水，但成水后的水面差仍明显小于实测，那么它修到的是淹没时机，不是纵向动量和摩阻平衡本身。",
        "- 如果糙率或面积调整能把两点水面差拉大，但同时把坝前整体抬错很多，那么问题也不是单一糙率，而是边界来水、回水传播和蓄量响应同时存在偏差。",
        "- 因此，判断 distributed 是否合理，不能只看坝前；必须同时看 `SEG 2` 与 `SEG 222`，以及它们之间的水面差时序。",
        "",
        "## 6. 当前最稳妥的结论",
        "",
        "- 当前已跑 case 里，没有任何一个方案可以被认定为“既合理再现坝前水位，又合理再现库尾-坝前真实水面线”。",
        "- `distributed` 的主要作用是改善坝前和总体水位量级，但它没有解决上游回水传播偏慢、库尾抬升不足的问题。",
        "- 仅靠当前幅度的糙率/面积调整，也没有把双站点水面线修正到合理水平。",
        "- 若下一步继续做，建议把试验目标从“坝前 RMSE 最小”改成“坝前 + 库尾 + 两点水面差三目标同时约束”。",
        "",
        "## 7. 文件",
        "",
        "- 屏幕窗口双站点评分：[dual_station_screen_summary.csv](dual_station_screen_summary.csv)",
        "- 完整窗口双站点评分：[dual_station_full_summary.csv](dual_station_full_summary.csv)",
        "- 三联图：[dual_station_screen.svg](dual_station_screen.svg)",
    ]
    (OUT_ROOT / "dual_station_review.md").write_text("\n".join(text), encoding="utf-8")


def main() -> None:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)

    screen_window = WindowSpec("screen", SCREEN_START, SCREEN_END)
    full_window = WindowSpec("full", SCREEN_START, FULL_END)

    screen_cases = load_case_ids(MULTI_ROOT / "results" / "summary_screen.csv")
    full_cases = load_case_ids(MULTI_ROOT / "results" / "summary_full.csv")

    down_screen, up_screen = obs_timeseries(screen_window)
    down_full, up_full = obs_timeseries(full_window)
    aligned_screen = align_obs(down_screen, up_screen)
    aligned_full = align_obs(down_full, up_full)

    screen_rows = [evaluate_case(case_id, screen_window, aligned_screen) for case_id in screen_cases]
    full_rows = [evaluate_case(case_id, full_window, aligned_full) for case_id in full_cases]

    save_csv(OUT_ROOT / "dual_station_screen_summary.csv", screen_rows)
    save_csv(OUT_ROOT / "dual_station_full_summary.csv", full_rows)
    plot_series()
    build_report(screen_rows, full_rows)


if __name__ == "__main__":
    main()
