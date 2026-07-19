#!/usr/bin/env python3
"""Inventory observation-anchored tail-domain candidates before changing ownership."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

from analyze_v35_multistation_waterline import PRIMARY_STATIONS, write_csv


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BATHYMETRY = ROOT / "cases" / "xld_2021_base" / "InputFiles" / "BTH" / "DIXING20250226.csv"
DEFAULT_CONTROL = ROOT / "cases" / "xld_2021_base" / "w2_con.csv"
DEFAULT_OUTPUT = ROOT / "analysis" / ".runs" / "v36_macro_domain_preflight"
CURRENT_MAX_TAIL_SEG = 16


@dataclass(frozen=True)
class BranchConnection:
    branch: int
    first_segment: int
    last_segment: int
    upstream_host_segment: int
    downstream_host_segment: int


@dataclass(frozen=True)
class DomainCandidate:
    name: str
    tail_us: int
    tail_ds: int
    couple_segment: int
    required_state_zones: int
    addressed_observation_intervals: str
    review_status: str


CANDIDATES = (
    DomainCandidate(
        "current_v35_baseline",
        2,
        5,
        6,
        1,
        "none_between_new_stations",
        "accepted_baseline",
    ),
    DomainCandidate(
        "stop_before_br2_at_segment28",
        2,
        27,
        28,
        1,
        "BHT_to_SJ_near_downstream_boundary",
        "diagnostic_candidate_only",
    ),
    DomainCandidate(
        "two_zone_to_ymt",
        2,
        56,
        57,
        2,
        "BHT_to_SJ_and_SJ_to_YMT",
        "requires_new_source_and_state_contract",
    ),
)


def read_csv_rows(path: Path) -> list[list[str]]:
    with path.open("r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
        return list(csv.reader(handle))


def parse_dlx_rows(rows: list[list[str]]) -> dict[int, float]:
    for row in rows:
        if row and row[0].strip() == "DLX":
            values = {segment: float(row[segment]) for segment in range(1, len(row)) if row[segment].strip()}
            if 222 not in values:
                raise ValueError("Bathymetry DLX row does not include segment 222")
            return values
    raise ValueError("Bathymetry DLX row not found")


def parse_branch_connections(rows: list[list[str]], branch_count: int = 6) -> list[BranchConnection]:
    for index, row in enumerate(rows):
        if len(row) < branch_count or [value.strip() for value in row[:branch_count]] != [
            f"BR{branch}" for branch in range(1, branch_count + 1)
        ]:
            continue
        numeric_rows = rows[index + 1 : index + 5]
        if len(numeric_rows) != 4:
            break
        try:
            first = [int(float(value)) for value in numeric_rows[0][:branch_count]]
            last = [int(float(value)) for value in numeric_rows[1][:branch_count]]
            upstream_host = [int(float(value)) for value in numeric_rows[2][:branch_count]]
            downstream_host = [int(float(value)) for value in numeric_rows[3][:branch_count]]
        except ValueError:
            continue
        return [
            BranchConnection(branch, first[branch - 1], last[branch - 1], upstream_host[branch - 1], downstream_host[branch - 1])
            for branch in range(1, branch_count + 1)
        ]
    raise ValueError("Branch grid definition not found in control file")


def center_distance_m(dlx: dict[int, float], upstream_segment: int, downstream_segment: int) -> float:
    if downstream_segment <= upstream_segment:
        raise ValueError("Downstream segment must have a larger segment number")
    return sum(
        0.5 * (dlx[segment] + dlx[segment + 1])
        for segment in range(upstream_segment, downstream_segment)
    )


def station_codes_in_domain(tail_us: int, tail_ds: int) -> list[str]:
    return [station.code for station in PRIMARY_STATIONS if tail_us <= station.segment <= tail_ds]


def owned_branch_junctions(
    connections: list[BranchConnection], tail_us: int, tail_ds: int
) -> list[BranchConnection]:
    return [
        connection
        for connection in connections
        if connection.branch != 1 and tail_us <= connection.downstream_host_segment <= tail_ds
    ]


def boundary_branch_junctions(
    connections: list[BranchConnection], couple_segment: int
) -> list[BranchConnection]:
    return [
        connection
        for connection in connections
        if connection.branch != 1 and connection.downstream_host_segment == couple_segment
    ]


def candidate_row(
    candidate: DomainCandidate,
    dlx: dict[int, float],
    connections: list[BranchConnection],
) -> dict[str, int | float | str]:
    owned_junctions = owned_branch_junctions(connections, candidate.tail_us, candidate.tail_ds)
    boundary_junctions = boundary_branch_junctions(connections, candidate.couple_segment)
    owned_count = candidate.tail_ds - candidate.tail_us + 1
    source_contract = ["BHT_QIN", f"Q_INTERFACE_SEG{candidate.couple_segment}"]
    if owned_junctions:
        source_contract.extend(f"BR{connection.branch}_Q_T_C" for connection in owned_junctions)
    return {
        "candidate": candidate.name,
        "tail_us": candidate.tail_us,
        "tail_ds": candidate.tail_ds,
        "couple_segment": candidate.couple_segment,
        "owned_segment_count": owned_count,
        "center_to_center_length_km": center_distance_m(dlx, candidate.tail_us, candidate.couple_segment) / 1000.0,
        "fits_current_max_tail_seg": str(owned_count <= CURRENT_MAX_TAIL_SEG),
        "required_state_zones": candidate.required_state_zones,
        "stations_in_owned_domain": ";".join(station_codes_in_domain(candidate.tail_us, candidate.tail_ds)),
        "owned_branch_junctions": ";".join(
            f"BR{connection.branch}@SEG{connection.downstream_host_segment}" for connection in owned_junctions
        ),
        "junctions_at_coupling_boundary": ";".join(
            f"BR{connection.branch}@SEG{connection.downstream_host_segment}" for connection in boundary_junctions
        ),
        "required_source_contract": ";".join(source_contract),
        "addressed_observation_intervals": candidate.addressed_observation_intervals,
        "review_status": candidate.review_status,
    }


def run_preflight(
    bathymetry_path: Path,
    control_path: Path,
    output_dir: Path,
) -> list[dict[str, object]]:
    dlx = parse_dlx_rows(read_csv_rows(bathymetry_path))
    connections = parse_branch_connections(read_csv_rows(control_path))
    rows = [candidate_row(candidate, dlx, connections) for candidate in CANDIDATES]
    write_csv(output_dir / "domain_candidates.csv", rows)
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bathymetry", type=Path, default=DEFAULT_BATHYMETRY)
    parser.add_argument("--control", type=Path, default=DEFAULT_CONTROL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = run_preflight(args.bathymetry, args.control, args.output)
    for row in rows:
        print(" ".join(f"{key}={value}" for key, value in row.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
