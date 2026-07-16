from __future__ import annotations

import argparse
import csv
import math
import re
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path

from analyze_v29_qstate_response import correlation, quantile, slope


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASE = REPO_ROOT / "analysis" / ".runs" / "v21_bht_redistribution_scan" / "redistribute_bht_a00_case"
PATTERN = re.compile(
    r"\[V33_LOCAL_TARGET\].*?JB=\s*(?P<jb>\d+).*?IS=\s*(?P<is>\d+).*?ISEG=\s*(?P<iseg>\d+)"
    r".*?QCOMMIT=\s*(?P<qcommit>[-+0-9.eE]+).*?QTARGET=\s*(?P<qtarget>[-+0-9.eE]+)"
    r".*?WUP=\s*(?P<wup>[-+0-9.eE]+).*?WDN=\s*(?P<wdn>[-+0-9.eE]+)"
    r".*?DX=\s*(?P<dx>[-+0-9.eE]+).*?STORAGE=\s*(?P<storage>[-+0-9.eE]+)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class LocalTargetSample:
    interface_index: int
    upstream_segment: int
    qcommit: float
    qtarget: float
    wup: float
    wdn: float
    dx: float
    storage: float


def parse_local_targets(text: str, branch: int = 1) -> list[LocalTargetSample]:
    samples: list[LocalTargetSample] = []
    for line in text.splitlines():
        if "[V33_LOCAL_TARGET]" not in line:
            continue
        match = PATTERN.search(line)
        if match is None or int(match.group("jb")) != branch:
            continue
        samples.append(
            LocalTargetSample(
                interface_index=int(match.group("is")),
                upstream_segment=int(match.group("iseg")),
                qcommit=float(match.group("qcommit")),
                qtarget=float(match.group("qtarget")),
                wup=float(match.group("wup")),
                wdn=float(match.group("wdn")),
                dx=float(match.group("dx")),
                storage=float(match.group("storage")),
            )
        )
    return samples


def summarize_interface(samples: list[LocalTargetSample]) -> dict[str, float | int]:
    if not samples:
        raise ValueError("No V33 local-target samples found")
    commits = [sample.qcommit for sample in samples]
    targets = [sample.qtarget for sample in samples]
    ratios = [sample.qtarget / sample.qcommit for sample in samples if sample.qcommit > 1.0]
    gaps = [target - commit for target, commit in zip(targets, commits)]
    return {
        "interface_index": samples[0].interface_index,
        "upstream_segment": samples[0].upstream_segment,
        "count": len(samples),
        "qcommit_mean": statistics.mean(commits),
        "qtarget_mean": statistics.mean(targets),
        "qtarget_median": statistics.median(targets),
        "target_commit_corr": correlation(commits, targets),
        "target_per_commit_slope": slope(commits, targets),
        "target_minus_commit_mean": statistics.mean(gaps),
        "target_minus_commit_rmse": math.sqrt(statistics.mean(value * value for value in gaps)),
        "target_commit_ratio_mean": statistics.mean(ratios),
        "target_commit_ratio_median": statistics.median(ratios),
        "target_commit_ratio_p10": quantile(ratios, 0.10),
        "target_commit_ratio_p90": quantile(ratios, 0.90),
        "target_commit_ratio_within_20pct_fraction": sum(0.8 <= value <= 1.2 for value in ratios) / len(ratios),
        "head_mean": statistics.mean(sample.wup - sample.wdn for sample in samples),
        "dx_mean": statistics.mean(sample.dx for sample in samples),
    }


def summarize(samples: list[LocalTargetSample]) -> list[dict[str, float | int]]:
    grouped: dict[int, list[LocalTargetSample]] = {}
    for sample in samples:
        grouped.setdefault(sample.interface_index, []).append(sample)
    return [summarize_interface(grouped[index]) for index in sorted(grouped)]


def write_outputs(case_dir: Path, samples: list[LocalTargetSample], rows: list[dict[str, float | int]]) -> None:
    with (case_dir / "v33_local_target_samples.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(samples[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(sample) for sample in samples)
    with (case_dir / "v33_local_target_summary.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze V33 shadow local hydraulic targets.")
    parser.add_argument("--case", type=Path, default=DEFAULT_CASE)
    parser.add_argument("--branch", type=int, default=1)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    text = (args.case / "w2.wrn").read_text(encoding="utf-8", errors="ignore")
    samples = parse_local_targets(text, args.branch)
    if not samples:
        raise RuntimeError("No V33 local-target samples were found")
    rows = summarize(samples)
    write_outputs(args.case, samples, rows)
    for row in rows:
        print(" ".join(f"{key}={value}" for key, value in row.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
