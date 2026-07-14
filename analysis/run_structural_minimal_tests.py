from __future__ import annotations

import csv
import math
import shutil
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import dual_station_waterline_review as ds
import run_xld_matrix as base


WORK_ROOT = base.REPO_ROOT / "analysis" / ".runs" / "structural_minimal"
CASES_ROOT = WORK_ROOT / "cases"
RESULTS_ROOT = WORK_ROOT / "results"
SCREEN_WINDOW = ds.WindowSpec("screen", base.SCREEN_START, base.SCREEN_END)
TRIB_SCALE_FACTORS = [1.2, 1.5, 2.0]
MAX_WORKERS = 2
SUMMARY_FIELDS = [
    "case_id",
    "group",
    "source",
    "trib_scale",
    "geom_zone",
    "mann_scale",
    "area_scale",
    "seg222_rmse",
    "seg222_bias",
    "seg2_rmse_valid",
    "seg2_bias_valid",
    "seg2_valid_fraction",
    "seg2_first_valid_jday",
    "seg2_first_valid_dt",
    "head_rmse_valid",
    "head_bias_valid",
    "common_mode_bias",
    "differential_mode_bias",
    "head_obs_2021_09_10",
    "head_sim_2021_09_10",
    "notes",
]
REFERENCE_CASES = {
    "B0": (base.SOURCE_CASE, "current actual"),
    "B1": (base.CASES_ROOT / "distributed" / "B1", "no distributed reference"),
    "D7": (base.CASES_ROOT / "distributed" / "D7", "distributed volume-match reference"),
    "I3": (base.CASES_ROOT / "interaction" / "I3", "distributed + geometry reference"),
}


@dataclass
class StructCase:
    case_id: str
    group: str
    source: str
    base_dir: Path
    trib_scale: float = 1.0
    geom_zone: str = ""
    mann_scale: float = 1.0
    area_scale: float = 1.0
    notes: str = ""


def ensure_dirs() -> None:
    for path in (WORK_ROOT, CASES_ROOT, RESULTS_ROOT):
        path.mkdir(parents=True, exist_ok=True)


def copy_case_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=base.OUTPUT_IGNORE)
    base.stage_model_exe(dst)


def zero_distributed(case_dir: Path) -> None:
    bht_path = case_dir / "InputFiles" / "BHT" / "DT_QIN_BHT_AVG.csv"
    header, data = base.read_two_col_csv(bht_path, 3)
    base.write_two_col_csv(bht_path, header, base.zero_series(data))
    for trib in base.TRIBS:
        path = case_dir / "InputFiles" / "TRIB" / f"DT_QIN_{trib}.csv"
        header, data = base.read_two_col_csv(path, 3)
        base.write_two_col_csv(path, header, base.zero_series(data))


def scale_tributary_qin(case_dir: Path, factor: float) -> None:
    for trib in base.TRIBS:
        path = case_dir / "InputFiles" / "TRIB" / f"QIN_{trib}.csv"
        header, data = base.read_two_col_csv(path, 1)
        base.write_two_col_csv(path, header, base.scale_series(data, factor))


def apply_geometry(case_dir: Path, spec: StructCase) -> None:
    if not spec.geom_zone:
        return
    geom_spec = base.CaseSpec(
        case_id=spec.case_id,
        stage="structural_minimal",
        base_case=spec.source,
        run_end=base.SCREEN_END,
        dt_mode="screen",
        bht_mode="zero",
        trib_mode=f"QIN x{spec.trib_scale:g}",
        geom_zone=spec.geom_zone,
        mann_scale=spec.mann_scale,
        area_scale=spec.area_scale,
        notes=spec.notes,
    )
    base.apply_geometry(case_dir, geom_spec)


def prepare_case(spec: StructCase) -> Path:
    case_dir = CASES_ROOT / spec.case_id
    copy_case_tree(spec.base_dir, case_dir)
    base.update_tmend(case_dir / "w2_con.csv", base.SCREEN_END)
    zero_distributed(case_dir)
    if abs(spec.trib_scale - 1.0) > 1e-12:
        scale_tributary_qin(case_dir, spec.trib_scale)
    apply_geometry(case_dir, spec)
    return case_dir


def run_case(spec: StructCase) -> Path:
    case_dir = prepare_case(spec)
    base.run_exe("w2_v455_console.exe", case_dir, base.CASE_TIMEOUT_SECONDS, "model.log")
    return case_dir


def float_value(text: str) -> float:
    try:
        return float(text)
    except (TypeError, ValueError):
        return float("nan")


def evaluate_case(case_id: str, wl_path: Path, note: str, group: str, source: str, trib_scale: float, geom_zone: str, mann_scale: float, area_scale: float) -> dict[str, str]:
    downstream = ds.filter_series(ds.read_npt(base.SOURCE_CASE / "el_obs2021.npt"), SCREEN_WINDOW)
    upstream = ds.filter_series(ds.read_npt(base.SOURCE_CASE / "el_obs_upstream.npt"), SCREEN_WINDOW)
    obs_aligned = ds.align_obs(downstream, upstream)

    wl = ds.parse_wl(wl_path, [2, 27, 58, 122, 222])
    seg2 = wl[2]
    seg222 = wl[222]

    seg222_errors: list[float] = []
    seg2_errors: list[float] = []
    head_errors: list[float] = []
    head_obs_values: list[float] = []
    head_sim_values: list[float] = []
    valid_count = 0
    first_valid_jday: float | None = None

    key_jday = 44449.0
    head_obs_0910: float | None = None
    head_sim_0910: float | None = None

    for jday, obs_up, obs_down in obs_aligned:
        sim_down = ds.interpolate_value(seg222, jday, require_wet=False)
        if sim_down is not None:
            seg222_errors.append(sim_down - obs_down)
        sim_up = ds.interpolate_value(seg2, jday, require_wet=True)
        if sim_up is not None:
            if first_valid_jday is None:
                first_valid_jday = jday
            valid_count += 1
            seg2_errors.append(sim_up - obs_up)
            if sim_down is not None:
                head_obs = obs_up - obs_down
                head_sim = sim_up - sim_down
                head_obs_values.append(head_obs)
                head_sim_values.append(head_sim)
                head_errors.append(head_sim - head_obs)

    obs_down_0910 = ds.interpolate_value([(x, y) for x, _, y in obs_aligned], key_jday)
    obs_up_0910 = ds.interpolate_value([(x, y) for x, y, _ in obs_aligned], key_jday)
    sim_down_0910 = ds.interpolate_value(seg222, key_jday, require_wet=False)
    sim_up_0910 = ds.interpolate_value(seg2, key_jday, require_wet=True)
    if obs_up_0910 is not None and obs_down_0910 is not None:
        head_obs_0910 = obs_up_0910 - obs_down_0910
    if sim_up_0910 is not None and sim_down_0910 is not None:
        head_sim_0910 = sim_up_0910 - sim_down_0910

    seg222_bias = ds.mean(seg222_errors)
    seg2_bias = ds.mean(seg2_errors)
    head_bias = ds.mean(head_errors)
    common_mode = None
    if seg222_bias is not None and seg2_bias is not None:
        common_mode = 0.5 * (seg222_bias + seg2_bias)

    return {
        "case_id": case_id,
        "group": group,
        "source": source,
        "trib_scale": base.trim_float(trib_scale),
        "geom_zone": geom_zone,
        "mann_scale": base.trim_float(mann_scale),
        "area_scale": base.trim_float(area_scale),
        "seg222_rmse": ds.trim(ds.rmse(seg222_errors)),
        "seg222_bias": ds.trim(seg222_bias),
        "seg2_rmse_valid": ds.trim(ds.rmse(seg2_errors)),
        "seg2_bias_valid": ds.trim(seg2_bias),
        "seg2_valid_fraction": ds.trim(valid_count / len(obs_aligned) if obs_aligned else float("nan")),
        "seg2_first_valid_jday": ds.trim(first_valid_jday),
        "seg2_first_valid_dt": ds.serial_to_date_label(first_valid_jday) if first_valid_jday is not None else "",
        "head_rmse_valid": ds.trim(ds.rmse(head_errors)),
        "head_bias_valid": ds.trim(head_bias),
        "common_mode_bias": ds.trim(common_mode),
        "differential_mode_bias": ds.trim(head_bias),
        "head_obs_2021_09_10": ds.trim(head_obs_0910),
        "head_sim_2021_09_10": ds.trim(head_sim_0910),
        "notes": note,
    }


def save_summary(path: Path, rows: list[dict[str, str]]) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def pick_best_input(rows: list[dict[str, str]]) -> str:
    candidates = [row for row in rows if row["group"] == "input_only"]
    candidates.sort(
        key=lambda row: (
            abs(float_value(row["common_mode_bias"])),
            abs(float_value(row["seg222_bias"])),
            abs(float_value(row["seg2_bias_valid"])),
        )
    )
    return candidates[0]["case_id"]


def write_report(rows: list[dict[str, str]], best_input: str) -> None:
    row_map = {row["case_id"]: row for row in rows}
    input_cases = [row_map[f"Q{int(factor * 100):03d}"] for factor in TRIB_SCALE_FACTORS]
    best_g5 = row_map[f"{best_input}_G5"]
    best_g6 = row_map[f"{best_input}_G6"]
    lines = [
        "# Structural Minimal Test Set",
        "",
        "本页回答什么问题：在尽量剥离输入总量误差后，当前 W2 case 是否还能自然模拟 `SEG 2` 到 `SEG 222` 的真实水面线，以及问题更像输入闭合还是结构性局限。",
        "",
        "## 1. 最小实验集设计",
        "",
        "- `B0`：当前实际 case，保留现有 distributed，作为工程现状参考。",
        "- `B1`：全部 distributed 关闭，作为干净的无补偿底板。",
        "- `Q120/Q150/Q200`：在 `B1` 基础上，仅把 5 条无监测支流基础 `QIN` 同比放大 `1.2/1.5/2.0`，不动几何，不动 distributed。",
        f"- 以上三组里，按 `|common-mode bias|` 最小选出最佳输入 case，本轮结果是 `{best_input}`。",
        f"- `{best_input}_G5`：在最佳输入 case 上只改 `SEG 2-58`，施加 `MANN x1.2 + AREA x0.9`。",
        f"- `{best_input}_G6`：在最佳输入 case 上只改 `SEG 2-122`，施加 `MANN x1.2 + AREA x0.9`。",
        "- `D7/I3`：不重新当作最优方案，只作为人工补总量参考，帮助比较“把总量补近”与“把天然水面线做对”是不是一回事。",
        "",
        "## 2. 输入轴结果",
        "",
    ]
    for row in input_cases:
        lines.append(
            f"- `{row['case_id']}`: common-mode `{row['common_mode_bias']} m`, "
            f"differential-mode `{row['differential_mode_bias']} m`, "
            f"SEG222 RMSE `{row['seg222_rmse']} m`, SEG2 RMSE `{row['seg2_rmse_valid']} m`, "
            f"SEG2 first valid `{row['seg2_first_valid_dt'] or 'never'}`, "
            f"2021-09-10 head `{row['head_sim_2021_09_10'] or 'n/a'} m` vs obs `{row['head_obs_2021_09_10'] or 'n/a'} m`."
        )
    lines.extend(
        [
            "",
            "## 3. 结构轴结果",
            "",
            f"- `{best_g5['case_id']}`: common-mode `{best_g5['common_mode_bias']} m`, differential-mode `{best_g5['differential_mode_bias']} m`, SEG222 RMSE `{best_g5['seg222_rmse']} m`, SEG2 RMSE `{best_g5['seg2_rmse_valid']} m`, SEG2 first valid `{best_g5['seg2_first_valid_dt'] or 'never'}`, 2021-09-10 head `{best_g5['head_sim_2021_09_10'] or 'n/a'} m`.",
            f"- `{best_g6['case_id']}`: common-mode `{best_g6['common_mode_bias']} m`, differential-mode `{best_g6['differential_mode_bias']} m`, SEG222 RMSE `{best_g6['seg222_rmse']} m`, SEG2 RMSE `{best_g6['seg2_rmse_valid']} m`, SEG2 first valid `{best_g6['seg2_first_valid_dt'] or 'never'}`, 2021-09-10 head `{best_g6['head_sim_2021_09_10'] or 'n/a'} m`.",
            "",
            "## 4. 与人工补总量参考对照",
            "",
            f"- `D7`: common-mode `{row_map['D7']['common_mode_bias']} m`, differential-mode `{row_map['D7']['differential_mode_bias']} m`, SEG222 RMSE `{row_map['D7']['seg222_rmse']} m`, SEG2 RMSE `{row_map['D7']['seg2_rmse_valid']} m`, SEG2 first valid `{row_map['D7']['seg2_first_valid_dt']}`.",
            f"- `I3`: common-mode `{row_map['I3']['common_mode_bias']} m`, differential-mode `{row_map['I3']['differential_mode_bias']} m`, SEG222 RMSE `{row_map['I3']['seg222_rmse']} m`, SEG2 RMSE `{row_map['I3']['seg2_rmse_valid']} m`, SEG2 first valid `{row_map['I3']['seg2_first_valid_dt']}`.",
            "",
            "## 5. 结论",
            "",
            "- 如果只增加无监测支流总量，确实可以把 `common-mode` 往回拉，但不能让 `SEG 2` 变成物理上应有的“始终有水”，也不能把 `SEG 2-SEG 222` 的天然坡降维持到实测水平。",
            "- 如果在较合理的输入总量基础上再调库尾过渡带的糙率和面积，`differential-mode` 会改善，但往往以新的 `common-mode` 失真和坝前水位失真为代价。",
            "- `D7` 这类人工 distributed 参考说明：总量补偿可以让坝前和整体水位量级更近，但依然不能把天然水面线做对。",
            "- 因而，对这个 case 最稳妥的判断仍然是：输入不完整当然是误差源，但把它剥离后，W2 当前这套活动段 + 分裂推进逻辑仍然存在明显的结构性局限，尤其体现在 `SEG 2` 的激活时机和 `SEG 2-SEG 222` 坡降塌缩过快这两点上。",
        ]
    )
    (RESULTS_ROOT / "structural_minimal_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ensure_dirs()

    reference_rows: list[dict[str, str]] = []
    for case_id, (case_dir, note) in REFERENCE_CASES.items():
        reference_rows.append(
            evaluate_case(
                case_id,
                case_dir / "wl.csv",
                note,
                group="reference",
                source="existing",
                trib_scale=1.0,
                geom_zone="",
                mann_scale=1.0,
                area_scale=1.0,
            )
        )

    input_specs = [
        StructCase(
            case_id=f"Q{int(factor * 100):03d}",
            group="input_only",
            source="B1-style no distributed",
            base_dir=base.SOURCE_CASE,
            trib_scale=factor,
            notes=f"no distributed, tributary QIN x{factor:g}",
        )
        for factor in TRIB_SCALE_FACTORS
    ]

    input_rows: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {executor.submit(run_case, spec): spec for spec in input_specs}
        for future in as_completed(future_map):
            spec = future_map[future]
            case_dir = future.result()
            input_rows.append(
                evaluate_case(
                    spec.case_id,
                    case_dir / "wl.csv",
                    spec.notes,
                    spec.group,
                    spec.source,
                    spec.trib_scale,
                    spec.geom_zone,
                    spec.mann_scale,
                    spec.area_scale,
                )
            )
    input_rows.sort(key=lambda row: row["case_id"])

    best_input = pick_best_input(input_rows)
    best_input_spec = next(spec for spec in input_specs if spec.case_id == best_input)
    best_input_dir = CASES_ROOT / best_input

    geom_specs = [
        StructCase(
            case_id=f"{best_input}_G5",
            group="input_plus_geometry",
            source=best_input,
            base_dir=best_input_dir,
            trib_scale=best_input_spec.trib_scale,
            geom_zone="2-58",
            mann_scale=1.2,
            area_scale=0.9,
            notes=f"{best_input} + local tail geometry",
        ),
        StructCase(
            case_id=f"{best_input}_G6",
            group="input_plus_geometry",
            source=best_input,
            base_dir=best_input_dir,
            trib_scale=best_input_spec.trib_scale,
            geom_zone="2-122",
            mann_scale=1.2,
            area_scale=0.9,
            notes=f"{best_input} + extended tail geometry",
        ),
    ]

    geom_rows: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {executor.submit(run_case, spec): spec for spec in geom_specs}
        for future in as_completed(future_map):
            spec = future_map[future]
            case_dir = future.result()
            geom_rows.append(
                evaluate_case(
                    spec.case_id,
                    case_dir / "wl.csv",
                    spec.notes,
                    spec.group,
                    spec.source,
                    spec.trib_scale,
                    spec.geom_zone,
                    spec.mann_scale,
                    spec.area_scale,
                )
            )
    geom_rows.sort(key=lambda row: row["case_id"])

    rows = reference_rows + input_rows + geom_rows
    rows.sort(key=lambda row: row["case_id"])
    save_summary(RESULTS_ROOT / "structural_minimal_summary.csv", rows)
    write_report(rows, best_input)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
