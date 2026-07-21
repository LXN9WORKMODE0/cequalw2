#!/usr/bin/env python3
"""Cross-year validation of the optional BHT-SJ active macro closure.

This analysis deliberately freezes the V41 candidate interval.  It does not
calibrate on 2022-2025 data.  Raw workbooks are read only; all derived tables
are written to ``analysis/verification/v42_multiyear_macro_closure``.

The primary validation is a quasi-steady hydraulic mapping:

    observed BHT discharge + observed downstream stage -> predicted BHT stage

The downstream stage at model segment 28 is interpolated between the SJ
(segment 26) and YMT (segment 57) gauges.  This keeps the validation boundary
independent of the BHT stage being predicted.  Results based on treating SJ as
the interface directly are also emitted as a boundary-location sensitivity.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from audit_v42_multiyear_hydro_data import (
    FLOW_COLUMNS,
    WATER_LEVEL_COLUMNS,
    read_timeseries_workbook,
)


G = 9.81
YEARS = tuple(range(2020, 2026))
NEFF_VALUES = (0.0700, 0.0725, 0.0750)
PRIMARY_NEFF = 0.0725
DOMAIN_US = 2
DOMAIN_DS = 27
INTERFACE_SEG = 28
SJ_SEG = 26
YMT_SEG = 57
MAX_STAGE_RISE_M = 25.0


@dataclass(frozen=True)
class TailGeometry:
    """Minimal zero-slope CE-QUAL-W2 geometry needed by the macro closure."""

    dlx: np.ndarray
    h: np.ndarray
    width: np.ndarray
    elevation: np.ndarray
    kb: np.ndarray
    kbi: np.ndarray
    suffix_area: np.ndarray

    @classmethod
    def from_bathymetry(cls, path: Path, elbot: float = 358.0) -> "TailGeometry":
        rows: list[list[str]] | None = None
        for encoding in ("utf-8-sig", "gb18030"):
            try:
                with path.open("r", encoding=encoding, newline="") as handle:
                    rows = list(csv.reader(handle))
                break
            except UnicodeDecodeError:
                continue
        if rows is None:
            raise ValueError(f"Unable to decode bathymetry: {path}")

        keyed = {row[0].strip(): row for row in rows[:7] if row}
        if "DLX" not in keyed or "LAYER" not in keyed:
            raise ValueError(f"Unexpected bathymetry layout: {path}")

        segment_count = 0
        for value in rows[1][1:]:
            try:
                segment_count = max(segment_count, int(value))
            except (TypeError, ValueError):
                pass
        layer_start = next(i for i, row in enumerate(rows) if row and row[0].strip() == "LAYER") + 1
        layer_rows = rows[layer_start:]
        kmx = len(layer_rows)
        if segment_count < INTERFACE_SEG or kmx < 3:
            raise ValueError("Bathymetry does not cover the active macro domain")

        # Arrays retain Fortran's 1-based indices.  Element zero is unused.
        dlx = np.zeros(segment_count + 1, dtype=float)
        dlx[1:] = [float(value) for value in keyed["DLX"][1 : segment_count + 1]]
        h = np.zeros(kmx + 1, dtype=float)
        width = np.zeros((kmx + 1, segment_count + 1), dtype=float)
        for k, row in enumerate(layer_rows, start=1):
            h[k] = float(row[0])
            width[k, 1:] = [float(value or 0.0) for value in row[1 : segment_count + 1]]

        elevation = np.zeros(kmx + 1, dtype=float)
        elevation[kmx] = elbot
        for k in range(kmx - 1, 0, -1):
            elevation[k] = elevation[k + 1] + h[k]

        kb = np.ones(segment_count + 1, dtype=int)
        for segment in range(1, segment_count + 1):
            k = 2
            while k <= kmx and width[k, segment] > 0.0:
                kb[segment] = k
                k += 1
        kbi = kb.copy()

        suffix_area = np.zeros_like(width)
        for segment in range(1, segment_count + 1):
            running = 0.0
            for k in range(kbi[segment], 0, -1):
                running += width[k, segment] * h[k]
                suffix_area[k, segment] = running

        return cls(dlx, h, width, elevation, kb, kbi, suffix_area)

    @property
    def kmx(self) -> int:
        return len(self.h) - 1

    def reach_length(self, upstream: int = DOMAIN_US, downstream: int = INTERFACE_SEG) -> float:
        return float(
            sum(
                0.5 * (self.dlx[segment] + self.dlx[segment + 1])
                for segment in range(upstream, downstream)
            )
        )

    def profile_fraction(
        self,
        segment: int,
        upstream: int = DOMAIN_US,
        downstream: int = INTERFACE_SEG,
    ) -> float:
        total = self.reach_length(upstream, downstream)
        distance = sum(
            0.5 * (self.dlx[it] + self.dlx[it + 1])
            for it in range(upstream, segment)
        )
        return float(np.clip(distance / max(total, 1.0), 0.0, 1.0))

    def section_props_array(
        self, segment: int, stage: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Vector replica of ``TAIL_SECTION_PROPS`` from ``w2_main.f90``."""

        stage = np.asarray(stage, dtype=float)
        levels = self.elevation[2 : self.kmx]
        # First K in 2..KMX-1 satisfying EL(K) < WSE, then KTTOP=K-1.
        ktop = np.searchsorted(-levels, -stage, side="right") + 1
        ktop = np.clip(ktop, 1, self.kmx - 1).astype(int)
        bottom_index = ktop + 1
        area = np.maximum(
            (stage - self.elevation[bottom_index]) * self.width[ktop, segment],
            0.0,
        )
        include = bottom_index <= self.kbi[segment]
        area = area + np.where(
            include, self.suffix_area[bottom_index, segment], 0.0
        )
        bed = self.elevation[self.kb[segment] + 1]
        depth = np.maximum(stage - bed, 1.0e-6)
        top_width = np.maximum(self.width[ktop, segment], 1.0e-6)
        hydraulic_radius = area / np.maximum(top_width + 2.0 * depth, 1.0e-6)
        ok = (area > 1.0e-8) & (hydraulic_radius > 1.0e-8)
        return area, hydraulic_radius, ok

    def aggregate_components_array(
        self,
        upstream_stage: np.ndarray,
        downstream_stage: np.ndarray,
        neff: float,
        upstream: int = DOMAIN_US,
        downstream: int = INTERFACE_SEG,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Return flow, friction term, velocity term and validity mask."""

        wup, wdn = np.broadcast_arrays(
            np.asarray(upstream_stage, dtype=float),
            np.asarray(downstream_stage, dtype=float),
        )
        rfric = np.zeros(wup.shape, dtype=float)
        valid = np.isfinite(wup) & np.isfinite(wdn)
        previous_resistance = None
        previous_segment = upstream
        area_up = np.zeros(wup.shape, dtype=float)
        area_dn = np.zeros(wup.shape, dtype=float)

        for segment in range(upstream, downstream + 1):
            fraction = self.profile_fraction(segment, upstream, downstream)
            local_stage = wup + fraction * (wdn - wup)
            area, radius, section_ok = self.section_props_array(segment, local_stage)
            valid &= section_ok
            resistance = (
                neff / np.maximum(area * radius ** (2.0 / 3.0), 1.0e-6)
            ) ** 2
            if segment == upstream:
                area_up = area
            else:
                dx = max(
                    0.5 * (self.dlx[previous_segment] + self.dlx[segment]), 1.0
                )
                rfric += 0.5 * (previous_resistance + resistance) * dx
            previous_resistance = resistance
            previous_segment = segment
            area_dn = area

        rvel = (
            1.0 / np.maximum(area_dn, 1.0e-6) ** 2
            - 1.0 / np.maximum(area_up, 1.0e-6) ** 2
        ) / (2.0 * G)
        coefficient = rfric + rvel
        head = wup - wdn
        valid &= (head > 1.0e-8) & (coefficient > 1.0e-16)
        flow = np.full(wup.shape, np.nan, dtype=float)
        flow[valid] = np.sqrt(head[valid] / coefficient[valid])
        return flow, rfric, rvel, valid

    def aggregate_flow_array(
        self,
        upstream_stage: np.ndarray,
        downstream_stage: np.ndarray,
        neff: float,
        upstream: int = DOMAIN_US,
        downstream: int = INTERFACE_SEG,
    ) -> np.ndarray:
        """Vector replica of ``COMPUTE_TAIL_AGGREGATE_LINK_FLOW``."""

        flow, _, _, _ = self.aggregate_components_array(
            upstream_stage, downstream_stage, neff, upstream, downstream
        )
        return flow

    def profile_volume_array(
        self,
        upstream_stage: np.ndarray,
        downstream_stage: np.ndarray,
        upstream: int = DOMAIN_US,
        downstream_owned: int = DOMAIN_DS,
        profile_downstream: int = INTERFACE_SEG,
    ) -> np.ndarray:
        """Replica of ``TAIL_PROFILE_VOLUME`` for the tail-owned segments."""

        wup, wdn = np.broadcast_arrays(
            np.asarray(upstream_stage, dtype=float),
            np.asarray(downstream_stage, dtype=float),
        )
        volume = np.zeros(wup.shape, dtype=float)
        valid = np.isfinite(wup) & np.isfinite(wdn)
        for segment in range(upstream, downstream_owned + 1):
            fraction = self.profile_fraction(segment, upstream, profile_downstream)
            local_stage = wup + fraction * (wdn - wup)
            area, _, section_ok = self.section_props_array(segment, local_stage)
            volume += area * self.dlx[segment]
            valid &= section_ok
        volume[~valid] = np.nan
        return volume

    def solve_upstream_stage_array(
        self,
        target_flow: np.ndarray,
        downstream_stage: np.ndarray,
        neff: float,
        iterations: int = 42,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Replica of ``SOLVE_TAIL_PROFILE_STAGE`` plus the production cap."""

        target, wdn = np.broadcast_arrays(
            np.asarray(target_flow, dtype=float),
            np.asarray(downstream_stage, dtype=float),
        )
        low = wdn.copy()
        for segment in range(DOMAIN_US, DOMAIN_DS + 1):
            fraction = self.profile_fraction(segment)
            bed_min = self.elevation[self.kb[segment] + 1] + 0.05
            if 1.0 - fraction > 1.0e-10:
                required = (bed_min - fraction * wdn) / (1.0 - fraction)
                low = np.maximum(low, required)

        high = low + 1.0
        q_high = self.aggregate_flow_array(high, wdn, neff)
        base_valid = np.isfinite(target) & (target >= 0.0) & np.isfinite(wdn)
        for _ in range(40):
            need_expand = base_valid & (~np.isfinite(q_high) | (q_high < target))
            if not need_expand.any():
                break
            increment = np.maximum(1.0, 0.5 * (high - low))
            high = np.where(need_expand, high + increment, high)
            q_high = self.aggregate_flow_array(high, wdn, neff)
        solved_ok = base_valid & np.isfinite(q_high) & (q_high >= target)

        for _ in range(iterations):
            middle = 0.5 * (low + high)
            q_middle = self.aggregate_flow_array(middle, wdn, neff)
            move_high = q_middle >= target
            high = np.where(move_high, middle, high)
            low = np.where(move_high, low, middle)
        solved_uncapped = 0.5 * (low + high)
        q_at_cap = self.aggregate_flow_array(wdn + MAX_STAGE_RISE_M, wdn, neff)
        representable_within_cap = (
            solved_ok & np.isfinite(q_at_cap) & (q_at_cap >= target)
        )
        solved = np.minimum(solved_uncapped, wdn + MAX_STAGE_RISE_M)
        solved[~solved_ok] = np.nan
        return solved, representable_within_cap


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
        "--bathymetry",
        type=Path,
        default=Path("cases/xld_2021_base/InputFiles/BTH/DIXING20250226.csv"),
    )
    parser.add_argument(
        "--reference-log",
        type=Path,
        default=Path(
            "analysis/.runs/v38_active_macro_scan/"
            "nseg_26_i028_neff_0p0725_tmend_44436p50_case/w2.wrn"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("analysis/verification/v42_multiyear_macro_closure"),
    )
    return parser.parse_args()


def isolated_spike_mask(series: pd.Series, threshold_m: float = 5.0) -> pd.Series:
    """Flag only isolated hourly deviations, preserving sustained real changes."""

    previous = series.shift(1)
    following = series.shift(-1)
    neighbor_midpoint = 0.5 * (previous + following)
    neighbors_agree = (previous - following).abs() <= threshold_m
    return series.notna() & neighbors_agree & ((series - neighbor_midpoint).abs() > threshold_m)


def prepare_observations(water: pd.DataFrame, flow: pd.DataFrame, geometry: TailGeometry) -> tuple[pd.DataFrame, dict[str, object]]:
    index = pd.date_range("2020-01-01", "2025-12-31 23:00:00", freq="h")
    frame = pd.concat([water.reindex(index), flow.reindex(index)], axis=1)

    qc_counts: dict[str, object] = {}
    for column in [name for name in frame if name.endswith("_WL")]:
        raw = frame[column].copy()
        valid_range = raw.between(500.0, 650.0, inclusive="both")
        cleaned = raw.where(valid_range)
        spikes = isolated_spike_mask(cleaned)
        frame[column] = cleaned.mask(spikes)
        qc_counts[column] = {
            "numeric": int(raw.notna().sum()),
            "out_of_range": int((raw.notna() & ~valid_range).sum()),
            "isolated_spikes": int(spikes.sum()),
            "retained": int(frame[column].notna().sum()),
        }

    raw_q = frame["BHT_Q_TD"].copy()
    q_in_range = raw_q.between(0.0, 50000.0, inclusive="both")
    q_clean = raw_q.where(q_in_range)
    q_observed = q_clean.notna()
    q_filled = q_clean.interpolate(method="time", limit=1, limit_area="inside")
    q_short_fill = q_filled.notna() & ~q_observed
    frame["BHT_Q"] = q_filled
    frame["BHT_Q_SOURCE"] = np.where(
        q_observed,
        "observed",
        np.where(q_short_fill, "one_hour_linear", "missing"),
    )
    qc_counts["BHT_Q"] = {
        "numeric": int(raw_q.notna().sum()),
        "out_of_range": int((raw_q.notna() & ~q_in_range).sum()),
        "observed": int(q_observed.sum()),
        "one_hour_linear": int(q_short_fill.sum()),
        "retained": int(q_filled.notna().sum()),
    }

    x_sj = geometry.profile_fraction(SJ_SEG)
    x_iface = geometry.profile_fraction(INTERFACE_SEG)
    x_ymt = geometry.profile_fraction(YMT_SEG, DOMAIN_US, 222)
    # Use absolute model center distance for the SJ-YMT interpolation because
    # YMT lies outside the active 2:28 macro domain.
    def center_distance(segment: int) -> float:
        return float(
            sum(
                0.5 * (geometry.dlx[it] + geometry.dlx[it + 1])
                for it in range(DOMAIN_US, segment)
            )
        )

    d_sj = center_distance(SJ_SEG)
    d_iface = center_distance(INTERFACE_SEG)
    d_ymt = center_distance(YMT_SEG)
    interpolation_weight = (d_iface - d_sj) / (d_ymt - d_sj)
    frame["WDN_SJ_YMT"] = frame["SJ_WL"] + interpolation_weight * (
        frame["YMT_WL"] - frame["SJ_WL"]
    )
    boundary_spatial_gross = (
        (frame["SJ_WL"] > frame["BHT_WL"] + 10.0)
        | (frame["YMT_WL"] > frame["SJ_WL"] + 10.0)
        | (frame["SJ_WL"] - frame["YMT_WL"] > 30.0)
    )
    frame.loc[boundary_spatial_gross, "WDN_SJ_YMT"] = np.nan
    frame["WDN_SJ_DIRECT"] = frame["SJ_WL"]
    frame["HEAD_OBS"] = frame["BHT_WL"] - frame["WDN_SJ_YMT"]
    frame["YEAR"] = frame.index.year

    q_slope = (frame["BHT_Q"].shift(-3) - frame["BHT_Q"].shift(3)) / 6.0
    bht_slope = (frame["BHT_WL"].shift(-3) - frame["BHT_WL"].shift(3)) / 6.0
    wdn_slope = (frame["WDN_SJ_YMT"].shift(-3) - frame["WDN_SJ_YMT"].shift(3)) / 6.0
    frame["Q_SLOPE_6H"] = q_slope
    frame["BHT_STAGE_SLOPE_6H"] = bht_slope
    frame["WDN_STAGE_SLOPE_6H"] = wdn_slope
    frame["HYDRAULIC_REGIME"] = np.select(
        [
            (q_slope.abs() <= 100.0)
            & (bht_slope.abs() <= 0.03)
            & (wdn_slope.abs() <= 0.03),
            q_slope > 100.0,
            q_slope < -100.0,
        ],
        ["stable", "rising_flow", "falling_flow"],
        default="stage_moving_or_mixed",
    )

    qc_counts["boundary_mapping"] = {
        "method": "linear interpolation between SJ segment 26 and YMT segment 57",
        "interface_segment": INTERFACE_SEG,
        "interpolation_weight": interpolation_weight,
        "sj_distance_m_from_segment_2": d_sj,
        "interface_distance_m_from_segment_2": d_iface,
        "ymt_distance_m_from_segment_2": d_ymt,
        "unused_profile_fraction_diagnostic_sj": x_sj,
        "unused_profile_fraction_diagnostic_interface": x_iface,
        "unused_profile_fraction_diagnostic_ymt_to_222": x_ymt,
        "gross_spatial_inconsistency_excluded_hours": int(
            boundary_spatial_gross.sum()
        ),
        "gross_spatial_rules_m": {
            "SJ_above_BHT": 10.0,
            "YMT_above_SJ": 10.0,
            "SJ_minus_YMT_upper": 30.0,
        },
    }
    return frame, qc_counts


def calculate_predictions(frame: pd.DataFrame, geometry: TailGeometry) -> pd.DataFrame:
    result = frame.copy()
    required = result[["BHT_Q", "BHT_WL", "WDN_SJ_YMT"]].notna().all(axis=1)
    result["INPUT_COMPLETE"] = required
    result["POSITIVE_HEAD"] = result["HEAD_OBS"] > 0.05
    result["WITHIN_STAGE_CAP"] = result["HEAD_OBS"] <= MAX_STAGE_RISE_M

    q_obs = result["BHT_Q"].to_numpy(dtype=float)
    wup_obs = result["BHT_WL"].to_numpy(dtype=float)
    wdn_primary = result["WDN_SJ_YMT"].to_numpy(dtype=float)
    result["TAIL_PROFILE_VOLUME_M3"] = geometry.profile_volume_array(
        wup_obs, wdn_primary
    )
    for window_hours in (2, 6, 12, 24):
        half_window = window_hours // 2
        storage_rate = (
            result["TAIL_PROFILE_VOLUME_M3"].shift(-half_window)
            - result["TAIL_PROFILE_VOLUME_M3"].shift(half_window)
        ) / (window_hours * 3600.0)
        result[f"DSTORAGE_DT_{window_hours}H_M3S"] = storage_rate
        result[f"Q_INTERFACE_CONTINUITY_{window_hours}H"] = (
            result["BHT_Q"] - storage_rate
        )
    for boundary_name, boundary_column in (
        ("interp", "WDN_SJ_YMT"),
        ("sj", "WDN_SJ_DIRECT"),
    ):
        wdn = result[boundary_column].to_numpy(dtype=float)
        for neff in NEFF_VALUES:
            tag = str(neff).replace(".", "p")
            q_pred = geometry.aggregate_flow_array(wup_obs, wdn, neff)
            wup_pred, representable = geometry.solve_upstream_stage_array(q_obs, wdn, neff)
            result[f"Q_PRED_{boundary_name}_{tag}"] = q_pred
            result[f"WUP_PRED_{boundary_name}_{tag}"] = wup_pred
            result[f"REPRESENTABLE_{boundary_name}_{tag}"] = representable

    primary_q, primary_rfric, primary_rvel, primary_valid = geometry.aggregate_components_array(
        wup_obs, wdn_primary, PRIMARY_NEFF
    )
    result["Q_PRED_interp_0p0725"] = primary_q
    result["RFRIC_PRIMARY"] = primary_rfric
    result["RVEL_PRIMARY"] = primary_rvel
    head_term = result["HEAD_OBS"].to_numpy(dtype=float) / np.maximum(q_obs, 1.0e-12) ** 2 - primary_rvel
    friction_per_n2 = primary_rfric / PRIMARY_NEFF**2
    neff_squared = head_term / friction_per_n2
    result["NEFF_REQUIRED"] = np.sqrt(np.maximum(neff_squared, 0.0))
    result.loc[
        ~primary_valid
        | ~np.isfinite(result["NEFF_REQUIRED"])
        | (neff_squared <= 0.0),
        "NEFF_REQUIRED",
    ] = np.nan
    return result


def error_metrics(observed: pd.Series, predicted: pd.Series) -> dict[str, float | int]:
    valid = observed.notna() & predicted.notna()
    obs = observed[valid].to_numpy(dtype=float)
    pred = predicted[valid].to_numpy(dtype=float)
    if len(obs) == 0:
        return {
            "samples": 0,
            "bias": math.nan,
            "mae": math.nan,
            "rmse": math.nan,
            "correlation": math.nan,
            "within_0p5m_percent": math.nan,
            "within_1p0m_percent": math.nan,
        }
    error = pred - obs
    correlation = float(np.corrcoef(obs, pred)[0, 1]) if len(obs) > 1 and np.std(obs) > 0 and np.std(pred) > 0 else math.nan
    return {
        "samples": int(len(obs)),
        "bias": float(np.mean(error)),
        "mae": float(np.mean(np.abs(error))),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "correlation": correlation,
        "within_0p5m_percent": float(100.0 * np.mean(np.abs(error) <= 0.5)),
        "within_1p0m_percent": float(100.0 * np.mean(np.abs(error) <= 1.0)),
    }


def flow_metrics(observed: pd.Series, predicted: pd.Series) -> dict[str, float | int]:
    valid = observed.notna() & predicted.notna() & (observed > 0.0)
    obs = observed[valid].to_numpy(dtype=float)
    pred = predicted[valid].to_numpy(dtype=float)
    if len(obs) == 0:
        return {"samples": 0, "bias_m3s": math.nan, "mae_m3s": math.nan, "rmse_m3s": math.nan, "median_ratio": math.nan, "within_20pct_percent": math.nan}
    error = pred - obs
    relative = np.abs(error) / obs
    return {
        "samples": int(len(obs)),
        "bias_m3s": float(np.mean(error)),
        "mae_m3s": float(np.mean(np.abs(error))),
        "rmse_m3s": float(np.sqrt(np.mean(error**2))),
        "median_ratio": float(np.median(pred / obs)),
        "within_20pct_percent": float(100.0 * np.mean(relative <= 0.2)),
    }


def summarize_by_year_and_regime(result: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    base = result[result["INPUT_COMPLETE"] & result["POSITIVE_HEAD"]]
    groups: list[tuple[str, pd.DataFrame]] = [("all", base)]
    groups.extend((name, base[base["HYDRAULIC_REGIME"] == name]) for name in sorted(base["HYDRAULIC_REGIME"].unique()))
    groups.extend(("observed_flow_only", base[base["BHT_Q_SOURCE"] == "observed"]) for _ in [0])

    for group_name, group in groups:
        for year in YEARS:
            subset = group[group["YEAR"] == year]
            for neff in NEFF_VALUES:
                tag = str(neff).replace(".", "p")
                stage = error_metrics(subset["BHT_WL"], subset[f"WUP_PRED_interp_{tag}"])
                flow = flow_metrics(subset["BHT_Q"], subset[f"Q_PRED_interp_{tag}"])
                representable = subset[f"REPRESENTABLE_interp_{tag}"]
                records.append(
                    {
                        "group": group_name,
                        "year": year,
                        "neff": neff,
                        "input_samples": int(len(subset)),
                        "representable_samples": int(representable.sum()),
                        "representable_percent": float(100.0 * representable.mean()) if len(subset) else math.nan,
                        "stage_bias_m": stage["bias"],
                        "stage_mae_m": stage["mae"],
                        "stage_rmse_m": stage["rmse"],
                        "stage_correlation": stage["correlation"],
                        "stage_within_0p5m_percent": stage["within_0p5m_percent"],
                        "stage_within_1p0m_percent": stage["within_1p0m_percent"],
                        **flow,
                    }
                )
    return pd.DataFrame.from_records(records)


def summarize_regime_matrix(result: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    base = result[
        result["INPUT_COMPLETE"]
        & result["POSITIVE_HEAD"]
        & result["WUP_PRED_interp_0p0725"].notna()
    ].copy()
    for year in YEARS:
        subset = base[base["YEAR"] == year].copy()
        if len(subset) < 12:
            continue
        q_threshold = float(subset["BHT_Q"].median())
        stage_threshold = float(subset["WDN_SJ_YMT"].median())
        subset["q_class"] = np.where(subset["BHT_Q"] <= q_threshold, "low_q", "high_q")
        subset["stage_class"] = np.where(subset["WDN_SJ_YMT"] <= stage_threshold, "low_stage", "high_stage")
        for q_class in ("low_q", "high_q"):
            for stage_class in ("low_stage", "high_stage"):
                cell = subset[(subset["q_class"] == q_class) & (subset["stage_class"] == stage_class)]
                metrics = error_metrics(cell["BHT_WL"], cell["WUP_PRED_interp_0p0725"])
                records.append(
                    {
                        "year": year,
                        "q_class": q_class,
                        "stage_class": stage_class,
                        "q_threshold_m3s": q_threshold,
                        "downstream_stage_threshold_m": stage_threshold,
                        "samples": metrics["samples"],
                        "stage_bias_m": metrics["bias"],
                        "stage_mae_m": metrics["mae"],
                        "stage_rmse_m": metrics["rmse"],
                        "stage_within_1p0m_percent": metrics["within_1p0m_percent"],
                        "required_neff_p10": float(cell["NEFF_REQUIRED"].quantile(0.10)) if cell["NEFF_REQUIRED"].notna().any() else math.nan,
                        "required_neff_median": float(cell["NEFF_REQUIRED"].median()) if cell["NEFF_REQUIRED"].notna().any() else math.nan,
                        "required_neff_p90": float(cell["NEFF_REQUIRED"].quantile(0.90)) if cell["NEFF_REQUIRED"].notna().any() else math.nan,
                        "required_neff_inside_frozen_interval_percent": float(100.0 * cell["NEFF_REQUIRED"].between(0.070, 0.075).mean()) if cell["NEFF_REQUIRED"].notna().any() else math.nan,
                    }
                )
    return pd.DataFrame.from_records(records)


def summarize_required_neff(result: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    base = result[
        result["INPUT_COMPLETE"]
        & result["POSITIVE_HEAD"]
        & result["WITHIN_STAGE_CAP"]
        & result["NEFF_REQUIRED"].between(0.001, 0.5)
    ]
    for year in YEARS:
        subset = base[base["YEAR"] == year]["NEFF_REQUIRED"]
        records.append(
            {
                "year": year,
                "samples": int(len(subset)),
                "neff_p10": float(subset.quantile(0.10)) if len(subset) else math.nan,
                "neff_median": float(subset.median()) if len(subset) else math.nan,
                "neff_p90": float(subset.quantile(0.90)) if len(subset) else math.nan,
                "inside_frozen_0p070_0p075_percent": float(100.0 * subset.between(0.070, 0.075).mean()) if len(subset) else math.nan,
            }
        )
    return pd.DataFrame.from_records(records)


def summarize_storage_continuity(result: pd.DataFrame) -> pd.DataFrame:
    """Compare hydraulic target flow with continuity-derived interface flow."""

    records: list[dict[str, object]] = []
    base = result[result["INPUT_COMPLETE"] & result["POSITIVE_HEAD"]]
    for window_hours in (2, 6, 12, 24):
        observed_column = f"Q_INTERFACE_CONTINUITY_{window_hours}H"
        for group_name, group in [
            ("all", base),
            *[
                (regime, base[base["HYDRAULIC_REGIME"] == regime])
                for regime in sorted(base["HYDRAULIC_REGIME"].unique())
            ],
        ]:
            for year in YEARS:
                subset = group[group["YEAR"] == year].copy()
                physical = subset[observed_column].between(0.0, 50000.0)
                subset = subset[physical]
                metrics = flow_metrics(
                    subset[observed_column], subset["Q_PRED_interp_0p0725"]
                )
                storage_rate = subset[f"DSTORAGE_DT_{window_hours}H_M3S"]
                records.append(
                    {
                        "group": group_name,
                        "year": year,
                        "derivative_window_hours": window_hours,
                        "samples": metrics["samples"],
                        "median_storage_rate_m3s": float(storage_rate.median()) if len(storage_rate) else math.nan,
                        "p10_storage_rate_m3s": float(storage_rate.quantile(0.10)) if len(storage_rate) else math.nan,
                        "p90_storage_rate_m3s": float(storage_rate.quantile(0.90)) if len(storage_rate) else math.nan,
                        "closure_bias_m3s": metrics["bias_m3s"],
                        "closure_mae_m3s": metrics["mae_m3s"],
                        "closure_rmse_m3s": metrics["rmse_m3s"],
                        "closure_median_ratio": metrics["median_ratio"],
                        "closure_within_20pct_percent": metrics["within_20pct_percent"],
                    }
                )
    return pd.DataFrame.from_records(records)


def summarize_declared_periods(result: pd.DataFrame) -> pd.DataFrame:
    """Revisit the original V38 selection and V40 holdout dates without tuning."""

    periods = {
        "v38_selection": (pd.Timestamp("2021-08-22 00:00"), pd.Timestamp("2021-08-28 12:00")),
        "v40_strict_holdout": (pd.Timestamp("2021-08-28 13:00"), pd.Timestamp("2021-10-15 00:00")),
        "v39_full_window": (pd.Timestamp("2021-08-22 00:00"), pd.Timestamp("2021-10-15 00:00")),
    }
    records: list[dict[str, object]] = []
    for period, (start, end) in periods.items():
        subset = result.loc[start:end]
        subset = subset[subset["INPUT_COMPLETE"] & subset["POSITIVE_HEAD"]]
        for neff in NEFF_VALUES:
            tag = str(neff).replace(".", "p")
            stage = error_metrics(subset["BHT_WL"], subset[f"WUP_PRED_interp_{tag}"])
            flow = flow_metrics(subset["BHT_Q"], subset[f"Q_PRED_interp_{tag}"])
            records.append(
                {
                    "period": period,
                    "start": start,
                    "end": end,
                    "neff": neff,
                    "samples": stage["samples"],
                    "stage_bias_m": stage["bias"],
                    "stage_mae_m": stage["mae"],
                    "stage_rmse_m": stage["rmse"],
                    "stage_correlation": stage["correlation"],
                    "stage_within_1p0m_percent": stage["within_1p0m_percent"],
                    "flow_bias_m3s": flow["bias_m3s"],
                    "flow_rmse_m3s": flow["rmse_m3s"],
                    "flow_median_ratio": flow["median_ratio"],
                }
            )
    return pd.DataFrame.from_records(records)


def summarize_boundary_sensitivity(result: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    base = result[result["INPUT_COMPLETE"] & result["POSITIVE_HEAD"]]
    for year in YEARS:
        subset = base[base["YEAR"] == year]
        for boundary in ("interp", "sj"):
            metrics = error_metrics(
                subset["BHT_WL"], subset[f"WUP_PRED_{boundary}_0p0725"]
            )
            records.append(
                {
                    "year": year,
                    "boundary_method": boundary,
                    "samples": metrics["samples"],
                    "stage_bias_m": metrics["bias"],
                    "stage_mae_m": metrics["mae"],
                    "stage_rmse_m": metrics["rmse"],
                    "within_1p0m_percent": metrics["within_1p0m_percent"],
                }
            )
    return pd.DataFrame.from_records(records)


def summarize_sample_acceptance(result: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for year in YEARS:
        subset = result[result["YEAR"] == year]
        complete = subset["INPUT_COMPLETE"]
        positive = complete & subset["POSITIVE_HEAD"]
        within_cap = positive & subset["WITHIN_STAGE_CAP"]
        representable = positive & subset["REPRESENTABLE_interp_0p0725"]
        evaluable = positive & subset["Q_PRED_interp_0p0725"].notna()
        records.append(
            {
                "year": year,
                "calendar_hours": int(len(subset)),
                "complete_input_hours": int(complete.sum()),
                "complete_input_percent": float(100.0 * complete.mean()),
                "complete_observed_flow_hours": int(
                    (complete & (subset["BHT_Q_SOURCE"] == "observed")).sum()
                ),
                "complete_one_hour_interpolated_flow_hours": int(
                    (complete & (subset["BHT_Q_SOURCE"] == "one_hour_linear")).sum()
                ),
                "nonpositive_or_near_zero_head_hours": int(
                    (complete & ~subset["POSITIVE_HEAD"]).sum()
                ),
                "positive_head_hours": int(positive.sum()),
                "observed_stage_closure_evaluable_hours": int(evaluable.sum()),
                "positive_head_above_25m_cap_hours": int(
                    (positive & ~subset["WITHIN_STAGE_CAP"]).sum()
                ),
                "within_observed_25m_head_cap_hours": int(within_cap.sum()),
                "target_flow_representable_hours": int(representable.sum()),
                "target_flow_representable_percent_of_positive_head": float(
                    100.0 * representable.sum() / positive.sum()
                )
                if positive.sum()
                else math.nan,
            }
        )
    return pd.DataFrame.from_records(records)


def summarize_head_feasibility(result: pd.DataFrame) -> pd.DataFrame:
    labels = [
        "head_le_0",
        "head_0_to_0p05",
        "head_0p05_to_1",
        "head_1_to_5",
        "head_5_to_15",
        "head_15_to_25",
        "head_gt_25",
    ]
    bins = [-np.inf, 0.0, 0.05, 1.0, 5.0, 15.0, 25.0, np.inf]
    records: list[dict[str, object]] = []
    complete = result[result["INPUT_COMPLETE"]].copy()
    complete["HEAD_CLASS"] = pd.cut(
        complete["HEAD_OBS"], bins=bins, labels=labels, right=True
    )
    for year in YEARS:
        year_data = complete[complete["YEAR"] == year]
        for label in labels:
            subset = year_data[year_data["HEAD_CLASS"] == label]
            records.append(
                {
                    "year": year,
                    "head_class": label,
                    "hours": int(len(subset)),
                    "percent_of_complete": float(100.0 * len(subset) / len(year_data)) if len(year_data) else math.nan,
                    "median_head_m": float(subset["HEAD_OBS"].median()) if len(subset) else math.nan,
                    "median_flow_m3s": float(subset["BHT_Q"].median()) if len(subset) else math.nan,
                    "p90_flow_m3s": float(subset["BHT_Q"].quantile(0.90)) if len(subset) else math.nan,
                }
            )
    return pd.DataFrame.from_records(records)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


ACTIVE_MACRO_PATTERN = re.compile(
    r"\[V38_ACTIVE_MACRO\].*?NEFF=\s*(?P<neff>[+\-0-9.E]+).*?"
    r"QTARGET=\s*(?P<qtarget>[+\-0-9.E]+).*?"
    r"WUP=\s*(?P<wup>[+\-0-9.E]+).*?WDN=\s*(?P<wdn>[+\-0-9.E]+)"
)


def verify_against_reference_log(path: Path, geometry: TailGeometry) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    if not path.exists():
        return pd.DataFrame.from_records(records)
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        match = ACTIVE_MACRO_PATTERN.search(line)
        if not match:
            continue
        values = {name: float(value) for name, value in match.groupdict().items()}
        predicted = float(
            geometry.aggregate_flow_array(
                np.array([values["wup"]]),
                np.array([values["wdn"]]),
                values["neff"],
            )[0]
        )
        records.append(
            {
                "line_number": line_number,
                **values,
                "python_flow_m3s": predicted,
                "python_minus_logged_target_m3s": predicted - values["qtarget"],
                "note": "logged QTARGET is an old/new average after the first step",
            }
        )
        if len(records) >= 200:
            break
    return pd.DataFrame.from_records(records)


def main() -> None:
    args = parse_args()
    geometry = TailGeometry.from_bathymetry(args.bathymetry)
    water = read_timeseries_workbook(args.water_level_workbook, WATER_LEVEL_COLUMNS)
    flow = read_timeseries_workbook(args.flow_workbook, FLOW_COLUMNS)
    prepared, qc = prepare_observations(water, flow, geometry)
    result = calculate_predictions(prepared, geometry)

    annual = summarize_by_year_and_regime(result)
    matrix = summarize_regime_matrix(result)
    required_neff = summarize_required_neff(result)
    storage_continuity = summarize_storage_continuity(result)
    declared_periods = summarize_declared_periods(result)
    boundary = summarize_boundary_sensitivity(result)
    acceptance = summarize_sample_acceptance(result)
    head_feasibility = summarize_head_feasibility(result)
    reference = verify_against_reference_log(args.reference_log, geometry)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "annual_and_regime_metrics.csv": annual,
        "stage_flow_regime_matrix.csv": matrix,
        "required_neff_diagnostic.csv": required_neff,
        "storage_continuity_metrics.csv": storage_continuity,
        "declared_period_metrics.csv": declared_periods,
        "boundary_mapping_sensitivity.csv": boundary,
        "sample_acceptance.csv": acceptance,
        "head_feasibility.csv": head_feasibility,
        "fortran_replica_check.csv": reference,
    }
    for name, table in outputs.items():
        table.to_csv(args.output_dir / name, index=False, encoding="utf-8-sig")

    diagnostic_columns = [
        "YEAR",
        "BHT_Q",
        "BHT_Q_SOURCE",
        "BHT_WL",
        "SJ_WL",
        "YMT_WL",
        "WDN_SJ_YMT",
        "HEAD_OBS",
        "HYDRAULIC_REGIME",
        "INPUT_COMPLETE",
        "POSITIVE_HEAD",
        "WITHIN_STAGE_CAP",
        "Q_PRED_interp_0p0725",
        "WUP_PRED_interp_0p0725",
        "REPRESENTABLE_interp_0p0725",
        "NEFF_REQUIRED",
        "TAIL_PROFILE_VOLUME_M3",
        "DSTORAGE_DT_6H_M3S",
        "Q_INTERFACE_CONTINUITY_6H",
    ]
    result.loc[result["INPUT_COMPLETE"], diagnostic_columns].to_csv(
        args.output_dir / "hourly_diagnostics.csv.gz",
        index=True,
        index_label="timestamp",
        compression="gzip",
    )

    first_reference_error = math.nan
    if len(reference):
        first_reference_error = float(reference.iloc[0]["python_minus_logged_target_m3s"])
    manifest = {
        "purpose": "frozen cross-year validation; no parameter retuning",
        "source_workbooks": [str(args.water_level_workbook), str(args.flow_workbook)],
        "source_sha256": {
            str(args.water_level_workbook): sha256_file(args.water_level_workbook),
            str(args.flow_workbook): sha256_file(args.flow_workbook),
        },
        "raw_workbooks_modified": False,
        "hourly_diagnostics_git_policy": "local-only; aggregate summaries are publishable",
        "bathymetry": str(args.bathymetry),
        "domain": {
            "owned_segments": [DOMAIN_US, DOMAIN_DS],
            "interface_segment": INTERFACE_SEG,
            "reach_length_m": geometry.reach_length(),
            "maximum_upstream_stage_rise_m": MAX_STAGE_RISE_M,
        },
        "frozen_neff_values": list(NEFF_VALUES),
        "primary_neff": PRIMARY_NEFF,
        "qc": qc,
        "fortran_replica_first_logged_step_error_m3s": first_reference_error,
        "limitations": [
            "This is a quasi-steady component test, not a complete 2020-2025 CE-QUAL-W2 simulation.",
            "Full-model runs require complete meteorology, temperature, tributary and operating boundary inputs.",
            "The downstream segment-28 stage is spatially interpolated from SJ and YMT observations.",
            "One-hour internal BHT discharge gaps are linearly interpolated and separately labelled.",
            "Storage derivatives are centered finite differences; 2/6/12/24-hour windows quantify derivative sensitivity.",
        ],
        "files": [*outputs, "hourly_diagnostics.csv.gz"],
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"reach_length_m={geometry.reach_length():.3f}")
    print(f"prepared_complete_hours={int(result['INPUT_COMPLETE'].sum())}")
    print("\nAnnual primary metrics:")
    print(
        annual[
            (annual["group"] == "all") & (annual["neff"] == PRIMARY_NEFF)
        ].to_string(index=False)
    )
    print("\nRequired n diagnostic:")
    print(required_neff.to_string(index=False))
    if len(reference):
        print("\nFortran replica first row:")
        print(reference.head(1).to_string(index=False))


if __name__ == "__main__":
    main()
