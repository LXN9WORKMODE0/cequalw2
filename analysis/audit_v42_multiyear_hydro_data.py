#!/usr/bin/env python3
"""Audit the raw 2020-2025 XLD water-level and discharge workbooks.

The script is deliberately read-only with respect to the source workbooks. It
writes compact, auditable CSV summaries under analysis/verification/v42_*.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


WATER_LEVEL_COLUMNS = {
    "BHT_WL": "TD白鹤滩坝下水位(白鹤滩站)",
    "XLD_WL": "TD溪洛渡坝上水位(马家河站)",
    "SJ_WL": "TD山江水位",
    "SLB_WL": "TD双龙坝水位",
    "YMT_WL": "TD幺米沱水位",
    "HH_WL": "TD黄华水位",
    "SS_WL": "TD双狮水位",
}

FLOW_COLUMNS = {
    "BHT_Q_TD": "TD白鹤滩出库流量",
    "BHT_Q_SW": "SW白鹤滩出库流量",
    "XLD_Q_TD": "TD溪洛渡出库流量",
    "XLD_Q_SW": "SW溪洛渡出库流量",
}

YEARS = tuple(range(2020, 2026))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--water-level-workbook",
        type=Path,
        default=Path("XLD库区水位2020-2025.xlsx"),
    )
    parser.add_argument(
        "--flow-workbook",
        type=Path,
        default=Path("XLD库区流量2020-2025.xlsx"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("analysis/verification/v42_multiyear_data_audit"),
    )
    return parser.parse_args()


def read_timeseries_workbook(path: Path, mapping: dict[str, str]) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name=0, dtype=object)
    timestamps = pd.to_datetime(raw["时间"], format="%Y-%m-%d %H", errors="coerce")
    data = raw.loc[timestamps.notna(), ["时间", *mapping.values()]].copy()
    data.index = pd.DatetimeIndex(timestamps[timestamps.notna()], name="timestamp")
    data = data.drop(columns="时间")
    inverse = {source: code for code, source in mapping.items()}
    data = data.rename(columns=inverse)
    for column in data.columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    return data.sort_index()


def longest_true_run(mask: pd.Series) -> int:
    values = mask.to_numpy(dtype=bool)
    if not values.any():
        return 0
    padded = np.concatenate(([False], values, [False]))
    changes = np.flatnonzero(padded[1:] != padded[:-1])
    return int(np.max(changes[1::2] - changes[::2]))


def numeric_summary(series: pd.Series, valid: pd.Series) -> dict[str, object]:
    chosen = series[valid]
    if chosen.empty:
        return {
            "valid_min": np.nan,
            "valid_p05": np.nan,
            "valid_median": np.nan,
            "valid_p95": np.nan,
            "valid_max": np.nan,
            "valid_mean": np.nan,
            "first_valid": "",
            "last_valid": "",
        }
    return {
        "valid_min": float(chosen.min()),
        "valid_p05": float(chosen.quantile(0.05)),
        "valid_median": float(chosen.median()),
        "valid_p95": float(chosen.quantile(0.95)),
        "valid_max": float(chosen.max()),
        "valid_mean": float(chosen.mean()),
        "first_valid": chosen.index.min().isoformat(sep=" "),
        "last_valid": chosen.index.max().isoformat(sep=" "),
    }


def build_quality_masks(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    valid = pd.DataFrame(index=data.index)
    reasons = pd.DataFrame(index=data.index)
    for column in data.columns:
        series = data[column]
        if column.endswith("_WL"):
            in_range = series.between(500.0, 650.0, inclusive="both")
        else:
            in_range = series.between(0.0, 50000.0, inclusive="both")
        valid[column] = series.notna() & in_range
        reason = pd.Series("valid", index=data.index, dtype="string")
        reason.loc[series.isna()] = "missing_or_nonnumeric"
        reason.loc[series.notna() & ~in_range] = "out_of_range"
        if column.endswith("_Q") or "_Q_" in column:
            reason.loc[series == 0.0] = "zero_flow_review"
        reasons[column] = reason
    return valid, reasons


def audit_time_axis(data: pd.DataFrame, source: str) -> dict[str, object]:
    duplicate_count = int(data.index.duplicated().sum())
    start = data.index.min()
    end = data.index.max()
    expected = pd.date_range(start, end, freq="h")
    missing_timestamps = expected.difference(data.index)
    nonhourly = data.index.to_series().diff().dropna()
    nonhourly_count = int((nonhourly != pd.Timedelta(hours=1)).sum())
    return {
        "source": source,
        "row_count": int(len(data)),
        "start": start.isoformat(sep=" "),
        "end": end.isoformat(sep=" "),
        "expected_inclusive_rows": int(len(expected)),
        "duplicate_timestamp_count": duplicate_count,
        "missing_timestamp_count": int(len(missing_timestamps)),
        "nonhourly_step_count": nonhourly_count,
    }


def audit_columns(
    data: pd.DataFrame,
    valid: pd.DataFrame,
    reasons: pd.DataFrame,
    source: str,
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for year in YEARS:
        year_mask = data.index.year == year
        expected = int(year_mask.sum())
        for column in data.columns:
            series = data.loc[year_mask, column]
            column_valid = valid.loc[year_mask, column]
            column_reason = reasons.loc[year_mask, column]
            bad = ~column_valid
            records.append(
                {
                    "source": source,
                    "year": year,
                    "variable": column,
                    "expected_hours": expected,
                    "numeric_hours": int(series.notna().sum()),
                    "valid_hours": int(column_valid.sum()),
                    "valid_percent": float(100.0 * column_valid.mean()),
                    "missing_or_nonnumeric": int(
                        (column_reason == "missing_or_nonnumeric").sum()
                    ),
                    "out_of_range": int((column_reason == "out_of_range").sum()),
                    "zero_flow_review": int(
                        (column_reason == "zero_flow_review").sum()
                    ),
                    "longest_invalid_gap_hours": longest_true_run(bad),
                    **numeric_summary(series, column_valid),
                }
            )
    return pd.DataFrame.from_records(records)


def compare_flow_sources(flow: pd.DataFrame, valid: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for year in YEARS:
        year_mask = flow.index.year == year
        for location in ("BHT", "XLD"):
            td = f"{location}_Q_TD"
            sw = f"{location}_Q_SW"
            overlap = year_mask & valid[td] & valid[sw]
            delta = flow.loc[overlap, td] - flow.loc[overlap, sw]
            if delta.empty:
                records.append(
                    {
                        "year": year,
                        "location": location,
                        "overlap_hours": 0,
                        "td_minus_sw_bias_m3s": np.nan,
                        "td_minus_sw_rmse_m3s": np.nan,
                        "p95_absolute_difference_m3s": np.nan,
                        "correlation": np.nan,
                    }
                )
                continue
            records.append(
                {
                    "year": year,
                    "location": location,
                    "overlap_hours": int(len(delta)),
                    "td_minus_sw_bias_m3s": float(delta.mean()),
                    "td_minus_sw_rmse_m3s": float(np.sqrt(np.mean(delta**2))),
                    "p95_absolute_difference_m3s": float(delta.abs().quantile(0.95)),
                    "correlation": float(
                        flow.loc[overlap, [td, sw]].corr().iloc[0, 1]
                    ),
                }
            )
    return pd.DataFrame.from_records(records)


def audit_overlap(
    combined: pd.DataFrame, valid: pd.DataFrame
) -> pd.DataFrame:
    contracts = {
        "macro_endpoints": ["BHT_Q_TD", "BHT_WL", "SJ_WL"],
        "macro_plus_xld_boundary": ["BHT_Q_TD", "BHT_WL", "SJ_WL", "XLD_WL"],
        "full_waterline": [
            "BHT_Q_TD",
            "BHT_WL",
            "SJ_WL",
            "YMT_WL",
            "SLB_WL",
            "HH_WL",
            "SS_WL",
            "XLD_WL",
        ],
        "flow_balance_observed": ["BHT_Q_TD", "XLD_Q_SW"],
    }
    records: list[dict[str, object]] = []
    for year in YEARS:
        year_mask = combined.index.year == year
        for contract, variables in contracts.items():
            mask = year_mask.copy()
            for variable in variables:
                mask &= valid[variable].to_numpy(dtype=bool)
            timestamps = combined.index[mask]
            records.append(
                {
                    "year": year,
                    "contract": contract,
                    "required_variables": "+".join(variables),
                    "common_valid_hours": int(mask.sum()),
                    "year_hours": int(year_mask.sum()),
                    "coverage_percent": float(100.0 * mask[year_mask].mean()),
                    "first_common": timestamps.min().isoformat(sep=" ")
                    if len(timestamps)
                    else "",
                    "last_common": timestamps.max().isoformat(sep=" ")
                    if len(timestamps)
                    else "",
                    "longest_common_run_hours": longest_true_run(pd.Series(mask, index=combined.index)),
                }
            )
    return pd.DataFrame.from_records(records)


def longest_valid_run(mask: pd.Series) -> int:
    return longest_true_run(mask)


def fix_overlap_longest_run(overlap: pd.DataFrame, combined: pd.DataFrame, valid: pd.DataFrame) -> None:
    for row_index, row in overlap.iterrows():
        variables = str(row["required_variables"]).split("+")
        year_mask = combined.index.year == int(row["year"])
        mask = pd.Series(year_mask, index=combined.index)
        for variable in variables:
            mask &= valid[variable]
        overlap.loc[row_index, "longest_common_run_hours"] = longest_valid_run(mask)


def audit_heads(combined: pd.DataFrame, valid: pd.DataFrame) -> pd.DataFrame:
    pairs = {
        "BHT_minus_SJ": ("BHT_WL", "SJ_WL"),
        "BHT_minus_XLD": ("BHT_WL", "XLD_WL"),
        "SJ_minus_XLD": ("SJ_WL", "XLD_WL"),
    }
    records: list[dict[str, object]] = []
    for year in YEARS:
        year_mask = combined.index.year == year
        for name, (upstream, downstream) in pairs.items():
            mask = year_mask & valid[upstream] & valid[downstream]
            head = combined.loc[mask, upstream] - combined.loc[mask, downstream]
            if head.empty:
                records.append(
                    {
                        "year": year,
                        "head_pair": name,
                        "valid_hours": 0,
                        "nonpositive_hours": 0,
                        "near_zero_le_0p05m_hours": 0,
                        "min_head_m": np.nan,
                        "p05_head_m": np.nan,
                        "median_head_m": np.nan,
                        "p95_head_m": np.nan,
                        "max_head_m": np.nan,
                    }
                )
                continue
            records.append(
                {
                    "year": year,
                    "head_pair": name,
                    "valid_hours": int(len(head)),
                    "nonpositive_hours": int((head <= 0.0).sum()),
                    "near_zero_le_0p05m_hours": int((head <= 0.05).sum()),
                    "min_head_m": float(head.min()),
                    "p05_head_m": float(head.quantile(0.05)),
                    "median_head_m": float(head.median()),
                    "p95_head_m": float(head.quantile(0.95)),
                    "max_head_m": float(head.max()),
                }
            )
    return pd.DataFrame.from_records(records)


def audit_regime_coverage(combined: pd.DataFrame, valid: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for year in YEARS:
        year_mask = combined.index.year == year
        for stage_column in ("SJ_WL", "XLD_WL"):
            mask = year_mask & valid["BHT_Q_TD"] & valid[stage_column]
            subset = combined.loc[mask, ["BHT_Q_TD", stage_column]].dropna()
            if len(subset) < 12:
                continue
            q_median = float(subset["BHT_Q_TD"].median())
            stage_median = float(subset[stage_column].median())
            q_class = np.where(subset["BHT_Q_TD"] <= q_median, "low_q", "high_q")
            stage_class = np.where(
                subset[stage_column] <= stage_median, "low_stage", "high_stage"
            )
            grouped = (
                pd.DataFrame(
                    {
                        "q_class": q_class,
                        "stage_class": stage_class,
                    },
                    index=subset.index,
                )
                .groupby(["q_class", "stage_class"], observed=True)
                .size()
            )
            for q_label in ("low_q", "high_q"):
                for stage_label in ("low_stage", "high_stage"):
                    count = int(grouped.get((q_label, stage_label), 0))
                    records.append(
                        {
                            "year": year,
                            "stage_variable": stage_column,
                            "q_threshold_m3s": q_median,
                            "stage_threshold_m": stage_median,
                            "q_class": q_label,
                            "stage_class": stage_label,
                            "hours": count,
                            "percent_of_overlap": float(100.0 * count / len(subset)),
                        }
                    )
    return pd.DataFrame.from_records(records)


def main() -> None:
    args = parse_args()
    water = read_timeseries_workbook(args.water_level_workbook, WATER_LEVEL_COLUMNS)
    flow = read_timeseries_workbook(args.flow_workbook, FLOW_COLUMNS)

    audit_start = pd.Timestamp("2020-01-01 00:00:00")
    audit_end = pd.Timestamp("2025-12-31 23:00:00")
    expected_index = pd.date_range(audit_start, audit_end, freq="h")
    water_period = water.reindex(expected_index)
    flow_period = flow.reindex(expected_index)
    combined = pd.concat([water_period, flow_period], axis=1)

    water_valid, water_reasons = build_quality_masks(water_period)
    flow_valid, flow_reasons = build_quality_masks(flow_period)
    valid = pd.concat([water_valid, flow_valid], axis=1)

    time_axis = pd.DataFrame.from_records(
        [
            audit_time_axis(water, args.water_level_workbook.name),
            audit_time_axis(flow, args.flow_workbook.name),
        ]
    )
    column_audit = pd.concat(
        [
            audit_columns(
                water_period, water_valid, water_reasons, args.water_level_workbook.name
            ),
            audit_columns(flow_period, flow_valid, flow_reasons, args.flow_workbook.name),
        ],
        ignore_index=True,
    )
    source_compare = compare_flow_sources(flow_period, flow_valid)
    overlap = audit_overlap(combined, valid)
    fix_overlap_longest_run(overlap, combined, valid)
    heads = audit_heads(combined, valid)
    regimes = audit_regime_coverage(combined, valid)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "time_axis_audit.csv": time_axis,
        "year_variable_audit.csv": column_audit,
        "flow_source_comparison.csv": source_compare,
        "common_overlap_audit.csv": overlap,
        "observed_head_audit.csv": heads,
        "regime_coverage.csv": regimes,
    }
    for name, frame in outputs.items():
        frame.to_csv(args.output_dir / name, index=False, encoding="utf-8-sig")

    summary = {
        "source_workbooks": [
            str(args.water_level_workbook),
            str(args.flow_workbook),
        ],
        "audit_period": [str(audit_start), str(audit_end)],
        "expected_hours": int(len(expected_index)),
        "raw_workbooks_modified": False,
        "quality_bounds": {
            "water_level_m": [500.0, 650.0],
            "flow_m3s": [0.0, 50000.0],
            "zero_flow": "retained in range but flagged for review",
        },
        "files": list(outputs),
    }
    (args.output_dir / "audit_manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(time_axis.to_string(index=False))
    print("\nCommon overlap:")
    print(overlap.to_string(index=False))
    print("\nObserved heads:")
    print(heads.to_string(index=False))


if __name__ == "__main__":
    main()
