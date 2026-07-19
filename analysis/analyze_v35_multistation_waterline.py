#!/usr/bin/env python3
"""Audit and compare the V35 multi-station water-level observations."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from analyze_v24_residual_structure import linear_slope, pearson
from run_v21_bht_redistribution_scan import (
    WINDOW_START,
    interpolate_series,
    parse_wl,
    read_npt_with_header,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASE = ROOT / "analysis" / ".runs" / "v21_bht_redistribution_scan" / "redistribute_bht_a00_case"
DEFAULT_OBSERVATIONS = ROOT / "outputs" / "xld_waterlevel_inputs_2021_2023" / "2021"
DEFAULT_GAPS = ROOT / "outputs" / "xld_waterlevel_inputs_2021_2023" / "processing_gaps.csv"
DEFAULT_AUDIT = ROOT / "outputs" / "xld_waterlevel_inputs_2021_2023" / "processing_audit.csv"
DEFAULT_OUTPUT = ROOT / "analysis" / ".runs" / "v35_multistation_waterline"
DEFAULT_TMEND = 44436.5


@dataclass(frozen=True)
class Station:
    code: str
    name: str
    chainage_km: float
    segment: int
    mapping_variant: str = "source_mapping"


@dataclass(frozen=True)
class StationSample:
    station: Station
    jday: float
    qphysical: float
    observed: float
    simulated: float

    @property
    def error(self) -> float:
        return self.simulated - self.observed


PRIMARY_STATIONS = (
    Station("XLD", "溪洛渡坝前", 0.0, 222, "project_endpoint"),
    Station("SS", "双狮", 6.3, 215, "downstream_boundary_origin"),
    Station("HH", "黄华", 50.0, 168),
    Station("SLB", "双龙坝", 95.0, 116),
    Station("YMT", "幺米沱", 148.0, 57),
    Station("SJ", "山江", 172.0, 26),
    Station("BHT", "白鹤滩坝下", 193.981, 2, "project_endpoint"),
)
SS_ALTERNATIVE = Station("SS", "双狮", 6.3, 214, "segment222_center_origin")
EXPECTED_2021_START = 44197.0
EXPECTED_2021_END = 44561.95
EXPECTED_2021_COUNT = 8760
YEAR_CONTRACTS = {
    2021: (44197.0, 44561.95, 8760),
    2023: (44927.0, 45291.95, 8760),
}
STATION_CODES_BY_YEAR = {
    2021: ("XLD", "SS", "HH", "SLB", "YMT", "SJ", "BHT"),
    2023: ("SS", "HH", "SLB", "YMT", "SJ"),
}


def observation_path(root: Path, station_code: str, year: int = 2021) -> Path:
    return root / f"el_obs_{station_code.lower()}_{year}.npt"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mean(values: list[float]) -> float:
    return statistics.mean(values) if values else float("nan")


def rmse(values: list[float]) -> float:
    return math.sqrt(mean([value * value for value in values])) if values else float("nan")


def safe_ratio(numerator: float, denominator: float, minimum_denominator: float = 1e-5) -> float:
    return numerator / denominator if abs(denominator) >= minimum_denominator else float("nan")


def validate_npt(path: Path, year: int = 2021) -> dict[str, float | int | str]:
    expected_start, expected_end, expected_count = YEAR_CONTRACTS[year]
    header, data = read_npt_with_header(path)
    normalized_header = [line.strip() for line in header]
    if normalized_header != ["eleobs", "bal", "JDAY  el_obs"]:
        raise ValueError(f"Unexpected NPT header in {path}: {normalized_header}")
    if len(data) != expected_count:
        raise ValueError(f"Expected {expected_count} records in {path}, found {len(data)}")
    times = [item[0] for item in data]
    values = [item[1] for item in data]
    if len(set(times)) != len(times) or any(right <= left for left, right in zip(times, times[1:])):
        raise ValueError(f"JDAY values are duplicated or not strictly increasing in {path}")
    steps = [right - left for left, right in zip(times, times[1:])]
    if any(step < 0.039 or step > 0.051 for step in steps):
        raise ValueError(f"JDAY is not an hourly series rounded to two decimals in {path}")
    if not math.isclose(times[0], expected_start, abs_tol=1e-9):
        raise ValueError(f"Unexpected first JDAY in {path}: {times[0]}")
    if not math.isclose(times[-1], expected_end, abs_tol=1e-9):
        raise ValueError(f"Unexpected last JDAY in {path}: {times[-1]}")
    if any(not math.isfinite(value) or value < 500.0 or value > 650.0 for value in values):
        raise ValueError(f"Non-finite or out-of-contract water level in {path}")
    return {
        "year": year,
        "station_code": path.stem.split("_")[2].upper(),
        "file": path.name,
        "record_count": len(data),
        "first_jday": times[0],
        "last_jday": times[-1],
        "minimum_m": min(values),
        "maximum_m": max(values),
        "sha256": sha256(path),
    }


def excel_jday(value: str) -> float:
    epoch = datetime(1899, 12, 30)
    return (datetime.fromisoformat(value) - epoch).total_seconds() / 86400.0


def read_gap_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_processing_audit(
    audit_path: Path, gaps_path: Path, package_root: Path
) -> list[dict[str, int | str | bool]]:
    with audit_path.open("r", encoding="utf-8-sig", newline="") as handle:
        audit_rows = list(csv.DictReader(handle))
    gap_rows = read_gap_rows(gaps_path)
    results: list[dict[str, int | str | bool]] = []
    for row in audit_rows:
        matching = [
            gap
            for gap in gap_rows
            if gap["year"] == row["year"] and gap["station_code"] == row["station_code"]
        ]
        category_total = sum(
            int(row[key])
            for key in (
                "raw_missing",
                "raw_out_of_range",
                "raw_temporal_inconsistent",
                "raw_spatial_inconsistent",
            )
        )
        gap_hours = sum(int(gap["hours"]) for gap in matching)
        gap_count = len(matching)
        max_gap = max((int(gap["hours"]) for gap in matching), default=0)
        reported_total = int(row["interpolated_total"])
        reconciled = (
            reported_total == category_total == gap_hours
            and int(row["gap_count"]) == gap_count
            and int(row["max_gap_hours"]) == max_gap
        )
        if not reconciled:
            raise ValueError(f"Processing audit does not reconcile for {row['year']} {row['station_code']}")
        output_exists = (package_root / row["output_file"]).is_file()
        if not output_exists:
            raise ValueError(f"Missing processed NPT declared by audit: {row['output_file']}")
        results.append(
            {
                "year": row["year"],
                "station_code": row["station_code"],
                "reported_interpolated": reported_total,
                "gap_hours": gap_hours,
                "gap_count": gap_count,
                "max_gap_hours": max_gap,
                "reconciled": reconciled,
                "output_exists": output_exists,
            }
        )
    return results


def validate_input_package(package_root: Path) -> list[dict[str, float | int | str | bool]]:
    rows: list[dict[str, float | int | str | bool]] = []
    endpoint_copies = verify_endpoint_copies(package_root / "2021")
    for year, station_codes in STATION_CODES_BY_YEAR.items():
        year_root = package_root / str(year)
        for station_code in station_codes:
            row = validate_npt(observation_path(year_root, station_code, year), year)
            row["endpoint_byte_copy"] = endpoint_copies.get(station_code, "not_applicable")
            rows.append(row)
    return rows


def flagged_points_in_window(
    gap_rows: list[dict[str, str]], station_code: str, start: float, end: float
) -> int:
    count = 0
    for row in gap_rows:
        if row["year"] != "2021" or row["station_code"] != station_code:
            continue
        gap_start = excel_jday(row["start_time"])
        gap_end = excel_jday(row["end_time"])
        overlap_start = max(start, gap_start)
        overlap_end = min(end, gap_end)
        if overlap_start <= overlap_end + 1e-9:
            count += int(round((overlap_end - overlap_start) * 24.0)) + 1
    return count


def verify_endpoint_copies(observation_root: Path) -> dict[str, bool]:
    expected = {
        "XLD": ROOT / "cases" / "xld_2021_base" / "el_obs2021.npt",
        "BHT": ROOT / "cases" / "xld_2021_base" / "el_obs_upstream.npt",
    }
    return {
        code: sha256(observation_path(observation_root, code)) == sha256(source)
        for code, source in expected.items()
    }


def build_station_samples(
    station: Station,
    observations: list[tuple[float, float]],
    simulation: list[tuple[float, float]],
    qphysical: list[tuple[float, float]],
    start: float,
    end: float,
) -> list[StationSample]:
    samples: list[StationSample] = []
    for jday, observed in observations:
        if jday < start or jday > end:
            continue
        simulated = interpolate_series(simulation, jday)
        if observed <= -900.0 or simulated <= -900.0:
            continue
        samples.append(
            StationSample(
                station=station,
                jday=jday,
                qphysical=interpolate_series(qphysical, jday),
                observed=observed,
                simulated=simulated,
            )
        )
    return samples


def summarize_station(samples: list[StationSample], flagged_points: int) -> dict[str, float | int | str]:
    if not samples:
        raise ValueError("No valid station samples")
    station = samples[0].station
    observed = [sample.observed for sample in samples]
    simulated = [sample.simulated for sample in samples]
    errors = [sample.error for sample in samples]
    flows = [sample.qphysical for sample in samples]
    observed_q_slope = linear_slope(flows, observed)
    simulated_q_slope = linear_slope(flows, simulated)
    return {
        "station_code": station.code,
        "station_name": station.name,
        "mapping_variant": station.mapping_variant,
        "chainage_km_from_xld": station.chainage_km,
        "model_segment": station.segment,
        "count": len(samples),
        "flagged_points_in_window": flagged_points,
        "observed_mean_m": mean(observed),
        "simulated_mean_m": mean(simulated),
        "bias_m": mean(errors),
        "rmse_m": rmse(errors),
        "mae_m": mean([abs(error) for error in errors]),
        "observed_range_m": max(observed) - min(observed),
        "simulated_range_m": max(simulated) - min(simulated),
        "stage_correlation": pearson(observed, simulated),
        "observed_stage_q_slope_m_per_m3s": observed_q_slope,
        "simulated_stage_q_slope_m_per_m3s": simulated_q_slope,
        "stage_q_slope_ratio": safe_ratio(simulated_q_slope, observed_q_slope),
        "error_q_correlation": pearson(errors, flows),
    }


def common_samples(
    downstream: list[StationSample], upstream: list[StationSample]
) -> list[tuple[StationSample, StationSample]]:
    upstream_by_time = {round(sample.jday, 8): sample for sample in upstream}
    return [
        (sample, upstream_by_time[round(sample.jday, 8)])
        for sample in downstream
        if round(sample.jday, 8) in upstream_by_time
    ]


def summarize_interval(
    downstream: list[StationSample], upstream: list[StationSample]
) -> dict[str, float | int | str]:
    pairs = common_samples(downstream, upstream)
    if not pairs:
        raise ValueError("No common samples for station interval")
    down_station = pairs[0][0].station
    up_station = pairs[0][1].station
    flows = [down.qphysical for down, _ in pairs]
    observed_heads = [up.observed - down.observed for down, up in pairs]
    simulated_heads = [up.simulated - down.simulated for down, up in pairs]
    errors = [sim - obs for obs, sim in zip(observed_heads, simulated_heads)]
    observed_q_slope = linear_slope(flows, observed_heads)
    simulated_q_slope = linear_slope(flows, simulated_heads)
    return {
        "interval": f"{down_station.code}->{up_station.code}",
        "downstream_segment": down_station.segment,
        "upstream_segment": up_station.segment,
        "length_km": up_station.chainage_km - down_station.chainage_km,
        "count": len(pairs),
        "observed_head_mean_m": mean(observed_heads),
        "simulated_head_mean_m": mean(simulated_heads),
        "head_bias_m": mean(errors),
        "head_rmse_m": rmse(errors),
        "observed_head_q_slope_m_per_m3s": observed_q_slope,
        "simulated_head_q_slope_m_per_m3s": simulated_q_slope,
        "head_q_slope_ratio": safe_ratio(simulated_q_slope, observed_q_slope),
        "head_error_q_correlation": pearson(errors, flows),
    }


def summarize_linear_profile_preflight(
    downstream: list[StationSample],
    interior: list[StationSample],
    upstream: list[StationSample],
) -> dict[str, float | int | str]:
    interior_by_time = {round(sample.jday, 8): sample for sample in interior}
    upstream_by_time = {round(sample.jday, 8): sample for sample in upstream}
    triples = [
        (down, interior_by_time[key], upstream_by_time[key])
        for down in downstream
        for key in [round(down.jday, 8)]
        if key in interior_by_time and key in upstream_by_time
    ]
    if not triples:
        raise ValueError("No common samples for linear-profile preflight")
    down_station, inside_station, up_station = (sample.station for sample in triples[0])
    fraction = (inside_station.chainage_km - down_station.chainage_km) / (
        up_station.chainage_km - down_station.chainage_km
    )
    predicted = [
        down.observed + fraction * (up.observed - down.observed)
        for down, _, up in triples
    ]
    actual = [inside.observed for _, inside, _ in triples]
    residuals = [estimate - observed for estimate, observed in zip(predicted, actual)]
    return {
        "candidate": f"single_linear_{up_station.code}_to_{down_station.code}_at_{inside_station.code}",
        "downstream_anchor": down_station.code,
        "interior_station": inside_station.code,
        "upstream_anchor": up_station.code,
        "interior_fraction_from_downstream": fraction,
        "count": len(triples),
        "observed_interior_mean_m": mean(actual),
        "linear_prediction_mean_m": mean(predicted),
        "prediction_minus_observation_bias_m": mean(residuals),
        "prediction_rmse_m": rmse(residuals),
        "prediction_error_min_m": min(residuals),
        "prediction_error_max_m": max(residuals),
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def run_analysis(
    case_dir: Path,
    observation_root: Path,
    audit_path: Path,
    gaps_path: Path,
    output_dir: Path,
    start: float,
    end: float,
) -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    package_root = observation_root.parent
    qa_rows = validate_input_package(package_root)
    processing_rows = validate_processing_audit(audit_path, gaps_path, package_root)

    gap_rows = read_gap_rows(gaps_path)
    all_stations = (*PRIMARY_STATIONS, SS_ALTERNATIVE)
    segments = sorted({station.segment for station in all_stations})
    simulations = parse_wl(case_dir / "wl.csv", segments)
    _, qphysical = read_npt_with_header(case_dir / "InputFiles" / "BHT" / "BHTOUTFLOW.npt")
    observations = {
        station.code: read_npt_with_header(observation_path(observation_root, station.code))[1]
        for station in PRIMARY_STATIONS
    }
    samples_by_key: dict[tuple[str, str], list[StationSample]] = {}
    station_rows: list[dict[str, object]] = []
    for station in all_stations:
        flagged = flagged_points_in_window(gap_rows, station.code, start, end)
        samples = build_station_samples(
            station,
            observations[station.code],
            simulations[station.segment],
            qphysical,
            start,
            end,
        )
        samples_by_key[(station.code, station.mapping_variant)] = samples
        station_rows.append(summarize_station(samples, flagged))

    interval_rows: list[dict[str, object]] = []
    for downstream, upstream in zip(PRIMARY_STATIONS, PRIMARY_STATIONS[1:]):
        interval_rows.append(
            summarize_interval(
                samples_by_key[(downstream.code, downstream.mapping_variant)],
                samples_by_key[(upstream.code, upstream.mapping_variant)],
            )
        )
    interval_rows.append(
        summarize_interval(
            samples_by_key[(PRIMARY_STATIONS[0].code, PRIMARY_STATIONS[0].mapping_variant)],
            samples_by_key[(PRIMARY_STATIONS[-1].code, PRIMARY_STATIONS[-1].mapping_variant)],
        )
    )
    profile_rows = [
        summarize_linear_profile_preflight(
            samples_by_key[("YMT", "source_mapping")],
            samples_by_key[("SJ", "source_mapping")],
            samples_by_key[("BHT", "project_endpoint")],
        )
    ]

    write_csv(output_dir / "input_qa.csv", qa_rows)
    write_csv(output_dir / "processing_qa.csv", processing_rows)
    write_csv(output_dir / "station_metrics.csv", station_rows)
    write_csv(output_dir / "interval_metrics.csv", interval_rows)
    write_csv(output_dir / "profile_preflight.csv", profile_rows)
    return qa_rows, processing_rows, station_rows, interval_rows, profile_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, default=DEFAULT_CASE)
    parser.add_argument("--observations", type=Path, default=DEFAULT_OBSERVATIONS)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--gaps", type=Path, default=DEFAULT_GAPS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--start", type=float, default=WINDOW_START)
    parser.add_argument("--end", type=float, default=DEFAULT_TMEND)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    qa_rows, processing_rows, station_rows, interval_rows, profile_rows = run_analysis(
        args.case, args.observations, args.audit, args.gaps, args.output, args.start, args.end
    )
    print(f"validated_inputs={len(qa_rows)}")
    print(f"reconciled_processing_rows={len(processing_rows)}")
    for row in station_rows:
        print(
            f"station={row['station_code']} segment={row['model_segment']} "
            f"variant={row['mapping_variant']} bias={row['bias_m']:.6f} "
            f"rmse={row['rmse_m']:.6f} flagged={row['flagged_points_in_window']}"
        )
    for row in interval_rows:
        print(
            f"interval={row['interval']} obs_head={row['observed_head_mean_m']:.6f} "
            f"sim_head={row['simulated_head_mean_m']:.6f} bias={row['head_bias_m']:.6f}"
        )
    for row in profile_rows:
        print(
            f"candidate={row['candidate']} bias={row['prediction_minus_observation_bias_m']:.6f} "
            f"rmse={row['prediction_rmse_m']:.6f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
