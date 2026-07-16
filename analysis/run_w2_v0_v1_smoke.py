from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_CASE = REPO_ROOT / "cases" / "xld_2021_base"
FALLBACK_BTH_FILE = SOURCE_CASE / "InputFiles" / "BTH" / "DIXING20250226.csv"
WORK_ROOT = REPO_ROOT / "analysis" / ".runs" / "w2_v0_v1_smoke"
CASE_ROOT = WORK_ROOT / "case"
RESULTS_ROOT = WORK_ROOT / "results"
DEFAULT_EXE = REPO_ROOT / "w2source_v455_2_11_2026" / "build_console" / "w2_v455_console.exe"
DEFAULT_TMEND = 44435.4
CASE_TIMEOUT_SECONDS = 45 * 60
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
    "model.log",
    "_complete.flag",
)
REQUIRED_MARKERS = [
    "[V0_BOUNDARY_INIT]",
    "[V0_BOUNDARY_SHIFT]",
    "[V0_SOURCE_PLACE]",
    "[V3_INNER_ITER]",
    "[V7_TAIL_STAGE]",
    "[V9_TAIL_FEEDBACK]",
    "[V10_TAIL_REACH]",
    "[V11_TAIL_DOMAIN]",
    "[V12_Q_STATE]",
    "[V13_TRANSITION_REACH]",
    "[V14_COUPLED_HYBRID]",
    "[V15_TAIL_DOMAIN_MULTI]",
    "[V16_SEGMENT_Q_STATE]",
    "[V17_SEGMENT_TRANSITION]",
    "[V18_MULTI_HYBRID]",
    "[V19_INTERFACE_RESIDUAL]",
    "[V20_INTERFACE_ITER]",
    "[V21_INTERFACE_SOLVE]",
    "[V24_INTERFACE_MASS]",
    "[V24_INTERFACE_COMMIT]",
    "[V26_DOMAIN_OWNER]",
    "[V26_BOUNDARY_CONSUMER]",
    "[V27_PROFILE_STORAGE]",
    "[V29_ACCEPTED_TAIL]",
    "[V31_SINGLE_STEP]",
    "[V32_SEGMENT_VOLUME]",
]
LATE_SEG2_PATTERN = "Add segments 2 through 2"
V11_TAIL_DOMAIN_PATTERN = re.compile(
    r"\[V11_TAIL_DOMAIN\].*?JB=(?P<jb>\d+).*?US=(?P<us>\d+).*?DS=(?P<ds>\d+)"
    r".*?NSEG=(?P<nseg>\d+).*?LINK_US=(?P<link_us>\d+).*?LINK_DN=(?P<link_dn>\d+)"
    r".*?DEFINED=(?P<defined>[TF])",
    re.IGNORECASE,
)
V15_TAIL_DOMAIN_PATTERN = re.compile(
    r"\[V15_TAIL_DOMAIN_MULTI\].*?JB=(?P<jb>\d+).*?US=(?P<us>\d+).*?DS=(?P<ds>\d+).*?NSEG=(?P<nseg>\d+).*?COUPLE=(?P<couple>\d+)",
    re.IGNORECASE,
)
V16_SEGMENT_Q_STATE_PATTERN = re.compile(
    r"\[V16_SEGMENT_Q_STATE\].*?JB=(?P<jb>\d+).*?IS=(?P<is>\d+).*?ISEG=(?P<iseg>\d+).*?Q=(?P<q>[-+0-9.eE]+).*?STAGE=(?P<stage>[-+0-9.eE]+)",
    re.IGNORECASE,
)
V17_SEGMENT_TRANSITION_PATTERN = re.compile(
    r"\[V17_SEGMENT_TRANSITION\].*?JB=(?P<jb>\d+).*?IS=(?P<is>\d+).*?MODE=(?P<mode>\d+).*?TRANS=(?P<trans>[-+0-9.eE]+).*?SUB=(?P<sub>[-+0-9.eE]+).*?SLOPE=(?P<slope>[-+0-9.eE]+).*?FR=(?P<fr>[-+0-9.eE]+)",
    re.IGNORECASE,
)
V18_MULTI_HYBRID_PATTERN = re.compile(
    r"\[V18_MULTI_HYBRID\].*?JB=(?P<jb>\d+).*?PASS=(?P<pass>\d+).*?COMMIT=(?P<commit>[FT]).*?QLINK=(?P<qlink>[-+0-9.eE]+).*?WSE_DN=(?P<wse_dn>[-+0-9.eE]+)",
    re.IGNORECASE,
)
V19_INTERFACE_RESIDUAL_PATTERN = re.compile(
    r"\[V19_INTERFACE_RESIDUAL\].*?JB=\s*(?P<jb>\d+).*?DETA=\s*(?P<deta>[-+0-9.eE]+).*?DQ=\s*(?P<dq>[-+0-9.eE]+).*?ETA_P=\s*(?P<eta_p>[-+0-9.eE]+).*?ETA_C=\s*(?P<eta_c>[-+0-9.eE]+).*?Q_P=\s*(?P<q_p>[-+0-9.eE]+).*?Q_C=\s*(?P<q_c>[-+0-9.eE]+)",
    re.IGNORECASE,
)
V20_INTERFACE_ITER_PATTERN = re.compile(
    r"\[V20_INTERFACE_ITER\].*?JB=\s*(?P<jb>\d+).*?ITER=\s*(?P<iter>\d+).*?DETA=\s*(?P<deta>[-+0-9.eE]+).*?DQ=\s*(?P<dq>[-+0-9.eE]+).*?RELAX=\s*(?P<relax>[-+0-9.eE]+).*?CONV=\s*(?P<conv>[TF])",
    re.IGNORECASE,
)
V21_INTERFACE_SOLVE_PATTERN = re.compile(
    r"\[V21_INTERFACE_SOLVE\].*?JB=\s*(?P<jb>\d+).*?ITER=\s*(?P<iter>\d+).*?DETA_STEP=\s*(?P<deta_step>[-+0-9.eE]+).*?DQ_STEP=\s*(?P<dq_step>[-+0-9.eE]+).*?ETA=\s*(?P<eta>[-+0-9.eE]+).*?Q=\s*(?P<q>[-+0-9.eE]+)",
    re.IGNORECASE,
)
V24_INTERFACE_MASS_PATTERN = re.compile(
    r"\[V24_INTERFACE_MASS\].*?JB=\s*(?P<jb>\d+).*?QPHYS=\s*(?P<qphys>[-+0-9.eE]+)"
    r".*?QIFACE=\s*(?P<qiface>[-+0-9.eE]+).*?QRES=\s*(?P<qres>[-+0-9.eE]+)"
    r".*?DSTORAGE=\s*(?P<dstorage>[-+0-9.eE]+).*?RTAIL=\s*(?P<rtail>[-+0-9.eE]+)"
    r".*?RFLUX=\s*(?P<rflux>[-+0-9.eE]+).*?RCOMB=\s*(?P<rcomb>[-+0-9.eE]+)"
    r".*?SEGLOSS=\s*(?P<segloss>[-+0-9.eE]+)",
    re.IGNORECASE,
)
V24_INTERFACE_COMMIT_PATTERN = re.compile(
    r"\[V24_INTERFACE_COMMIT\].*?JB=\s*(?P<jb>\d+).*?QRES=\s*(?P<qres>[-+0-9.eE]+)"
    r".*?QCOMMIT=\s*(?P<qcommit>[-+0-9.eE]+).*?ETA_PREV=\s*(?P<eta_prev>[-+0-9.eE]+)"
    r".*?ETA_COMMIT=\s*(?P<eta_commit>[-+0-9.eE]+).*?DETA_APPLIED=\s*(?P<deta_applied>[-+0-9.eE]+)"
    r".*?EVALUATED=\s*(?P<evaluated>[TF])",
    re.IGNORECASE,
)
V26_DOMAIN_OWNER_PATTERN = re.compile(
    r"\[V26_DOMAIN_OWNER\].*?JB=\s*(?P<jb>\d+).*?CUS=\s*(?P<cus>\d+)"
    r".*?TAIL_US=\s*(?P<tail_us>\d+).*?TAIL_DS=\s*(?P<tail_ds>\d+)"
    r".*?COUPLE=\s*(?P<couple>\d+).*?EXCLUSIVE=\s*(?P<exclusive>[TF])",
    re.IGNORECASE,
)
V26_BOUNDARY_CONSUMER_PATTERN = re.compile(
    r"\[V26_BOUNDARY_CONSUMER\].*?JB=\s*(?P<jb>\d+).*?QPHYS=\s*(?P<qphys>[-+0-9.eE]+)"
    r".*?QRES=\s*(?P<qres>[-+0-9.eE]+).*?QTHERM=\s*(?P<qtherm>[-+0-9.eE]+)"
    r".*?QVOL=\s*(?P<qvol>[-+0-9.eE]+)",
    re.IGNORECASE,
)
V12_Q_STATE_PATTERN = re.compile(
    r"\[V12_Q_STATE\].*?JB=\s*(?P<jb>\d+).*?LENGTH=\s*(?P<length>[-+0-9.eE]+)",
    re.IGNORECASE,
)
V27_PROFILE_STORAGE_PATTERN = re.compile(
    r"\[V27_PROFILE_STORAGE\].*?JB=\s*(?P<jb>\d+).*?VSTATE=\s*(?P<vstate>[-+0-9.eE]+)"
    r".*?VPROFILE=\s*(?P<vprofile>[-+0-9.eE]+).*?VGAP=\s*(?P<vgap>[-+0-9.eE]+)"
    r".*?WUP=\s*(?P<wup>[-+0-9.eE]+).*?WDN=\s*(?P<wdn>[-+0-9.eE]+)",
    re.IGNORECASE,
)
V31_SINGLE_STEP_PATTERN = re.compile(
    r"\[V31_SINGLE_STEP\].*?JB=\s*(?P<jb>\d+).*?VPRE=\s*(?P<vpre>[-+0-9.eE]+)"
    r".*?VFINAL=\s*(?P<vfinal>[-+0-9.eE]+).*?RATE=\s*(?P<rate>[-+0-9.eE]+)"
    r".*?RTAIL=\s*(?P<rtail>[-+0-9.eE]+).*?RATEGAP=\s*(?P<rategap>[-+0-9.eE]+)",
    re.IGNORECASE,
)
V32_SEGMENT_VOLUME_PATTERN = re.compile(
    r"\[V32_SEGMENT_VOLUME\].*?JB=\s*(?P<jb>\d+).*?VTOTAL=\s*(?P<vtotal>[-+0-9.eE]+)"
    r".*?VSEG=\s*(?P<vseg>[-+0-9.eE]+).*?VGAP=\s*(?P<vgap>[-+0-9.eE]+)",
    re.IGNORECASE,
)


@dataclass
class SmokeResult:
    case_dir: Path
    warn_path: Path
    log_path: Path
    err_path: Path
    missing_markers: list[str]
    has_late_seg2_add: bool
    has_runtime_error: bool
    computational_warning_count: int
    has_v2_front_state: bool
    has_required_outputs: bool
    has_v3_inner_iter: bool
    has_v4_front_geom: bool
    has_v5_transition: bool
    has_v6_coupling: bool
    has_v7_tail_stage: bool
    has_v8_front_sync: bool
    has_v9_tail_feedback: bool
    has_v10_tail_reach: bool
    has_v11_tail_domain: bool
    has_v12_q_state: bool
    has_v13_transition_reach: bool
    has_v14_coupled_hybrid: bool
    has_v15_tail_domain_multi: bool
    has_v16_segment_q_state: bool
    has_v17_segment_transition: bool
    has_v18_multi_hybrid: bool
    has_v19_interface_residual: bool
    has_v20_interface_iter: bool
    has_v21_interface_solve: bool
    has_v24_interface_mass: bool
    has_v24_interface_commit: bool
    has_v26_domain_owner: bool
    has_v26_boundary_consumer: bool
    has_v27_profile_storage: bool
    tail_predictor_pass_count: int
    tail_corrector_pass_count: int
    tail_iface_resid_max_eta: float
    tail_iface_resid_max_q: float
    tail_iface_iter_max: int
    tail_iface_iter_converged_count: int
    tail_iface_linear_updates: int
    tail_interface_mass_count: int
    tail_mass_resid_max: float
    tail_flux_gap_max: float
    tail_combined_mass_resid_max: float
    tail_segment_q_loss_max: float
    tail_interface_commit_count: int
    tail_interface_commit_q_gap_max: float
    tail_interface_commit_eta_applied_max: float
    tail_interface_commit_all_evaluated: bool
    tail_link_dn: int
    tail_couple_seg: int
    tail_interface_boundary_aligned: bool
    tail_active_cus: int
    tail_domain_owner_exclusive: bool
    reservoir_boundary_consumer_count: int
    reservoir_boundary_flux_gap_max: float
    tail_profile_storage_count: int
    tail_profile_storage_gap_max: float
    tail_reach_length_min: float
    tail_reach_length_max: float
    accepted_tail_state_count: int
    tail_single_step_count: int
    tail_full_storage_resid_max: float
    tail_storage_rate_gap_max: float
    tail_segment_volume_count: int
    tail_segment_volume_gap_max: float
    tail_domain_nseg_min: int
    tail_segment_state_count: int
    tail_mode_set: str
    seg2_valid_count: int
    seg222_valid_count: int


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "gbk", "latin-1"):
        try:
            return path.read_text(encoding=encoding, errors="ignore")
        except OSError:
            continue
    return path.read_text(encoding="latin-1", errors="ignore")


def count_computational_warnings(text: str) -> int:
    return text.count("COMPUTATIONAL WARNING AT JULIAN DAY")


def parse_v26_contract(text: str, branch: int = 1) -> dict[str, int | float | bool]:
    domain_match = next(
        (match for match in V26_DOMAIN_OWNER_PATTERN.finditer(text) if int(match.group("jb")) == branch),
        None,
    )
    consumer_matches = [
        match for match in V26_BOUNDARY_CONSUMER_PATTERN.finditer(text) if int(match.group("jb")) == branch
    ]
    consumer_gap = max(
        (
            max(
                abs(float(match.group("qres")) - float(match.group("qtherm"))),
                abs(float(match.group("qres")) - float(match.group("qvol"))),
            )
            for match in consumer_matches
        ),
        default=0.0,
    )
    return {
        "has_domain_owner": domain_match is not None,
        "has_boundary_consumer": bool(consumer_matches),
        "active_cus": int(domain_match.group("cus")) if domain_match else 0,
        "couple": int(domain_match.group("couple")) if domain_match else 0,
        "exclusive": bool(domain_match) and domain_match.group("exclusive").upper() == "T",
        "consumer_count": len(consumer_matches),
        "consumer_gap_max": consumer_gap,
    }


def parse_v27_profile_contract(text: str, branch: int = 1) -> dict[str, int | float | bool]:
    profile_matches = [
        match for match in V27_PROFILE_STORAGE_PATTERN.finditer(text) if int(match.group("jb")) == branch
    ]
    length_matches = [match for match in V12_Q_STATE_PATTERN.finditer(text) if int(match.group("jb")) == branch]
    lengths = [float(match.group("length")) for match in length_matches]
    return {
        "has_profile_storage": bool(profile_matches),
        "profile_count": len(profile_matches),
        "profile_gap_max": max((abs(float(match.group("vgap"))) for match in profile_matches), default=0.0),
        "reach_length_min": min(lengths, default=0.0),
        "reach_length_max": max(lengths, default=0.0),
    }


def parse_v31_single_step_contract(text: str, branch: int = 1) -> dict[str, int | float | bool]:
    matches = [match for match in V31_SINGLE_STEP_PATTERN.finditer(text) if int(match.group("jb")) == branch]
    return {
        "has_single_step": bool(matches),
        "count": len(matches),
        "full_storage_resid_max": max((abs(float(match.group("rtail"))) for match in matches), default=0.0),
        "storage_rate_gap_max": max((abs(float(match.group("rategap"))) for match in matches), default=0.0),
    }


def parse_v32_segment_volume_contract(text: str, branch: int = 1) -> dict[str, int | float | bool]:
    matches = [match for match in V32_SEGMENT_VOLUME_PATTERN.finditer(text) if int(match.group("jb")) == branch]
    return {
        "has_segment_volume": bool(matches),
        "count": len(matches),
        "segment_volume_gap_max": max((abs(float(match.group("vgap"))) for match in matches), default=0.0),
    }


def ensure_dirs() -> None:
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)


def clone_case_tree(dst: Path) -> None:
    if dst.exists():
        remove_tree(dst)
    shutil.copytree(SOURCE_CASE, dst, ignore=OUTPUT_IGNORE)
    ensure_fallback_inputs(dst)


def remove_tree(path: Path) -> None:
    if not path.exists():
        return
    for _ in range(5):
        try:
            if path.is_dir() and not path.is_symlink():
                entries = sorted(path.rglob("*"), key=lambda item: len(item.parts), reverse=True)
                for entry in entries:
                    try:
                        if entry.is_dir() and not entry.is_symlink():
                            entry.rmdir()
                        else:
                            entry.unlink(missing_ok=True)
                    except OSError:
                        continue
                path.rmdir()
            else:
                path.unlink(missing_ok=True)
            return
        except OSError:
            continue
    raise RuntimeError(f"Unable to remove existing case tree: {path}")


def ensure_fallback_inputs(case_root: Path) -> None:
    target = case_root / "InputFiles" / "BTH" / "DIXING20250226.csv"
    if target.exists():
        return
    if not FALLBACK_BTH_FILE.exists():
        raise FileNotFoundError(f"Missing fallback BTH input: {FALLBACK_BTH_FILE}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(FALLBACK_BTH_FILE, target)


def update_tmend(w2_path: Path, tmend: float) -> None:
    lines = w2_path.read_text(encoding="gbk", errors="ignore").splitlines(keepends=True)
    for idx, line in enumerate(lines[:-1]):
        if line.startswith("TMSTRT"):
            parts = lines[idx + 1].rstrip("\r\n").split(",")
            if len(parts) < 2:
                raise RuntimeError(f"TMEND row malformed in {w2_path}")
            parts[1] = trim_float(tmend)
            lines[idx + 1] = ",".join(parts) + "\n"
            w2_path.write_text("".join(lines), encoding="gbk", newline="")
            return
    raise RuntimeError(f"TMSTRT/TMEND row not found in {w2_path}")


def trim_float(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.6f}".rstrip("0").rstrip(".")


def stage_exe(case_dir: Path, exe_path: Path) -> None:
    target = case_dir / "w2_v455_console.exe"
    shutil.copy2(exe_path, target)


def run_case(case_dir: Path) -> Path:
    log_path = case_dir / "model.log"
    exe_path = case_dir / "w2_v455_console.exe"
    with open(log_path, "w", encoding="utf-8") as handle:
        proc = subprocess.run(
            [str(exe_path)],
            cwd=str(case_dir),
            stdout=handle,
            stderr=subprocess.STDOUT,
            timeout=CASE_TIMEOUT_SECONDS,
            check=False,
        )
    if proc.returncode != 0:
        raise RuntimeError(f"Executable failed with exit code {proc.returncode}. See {log_path}")
    return log_path


def evaluate(case_dir: Path) -> SmokeResult:
    warn_path = case_dir / "w2.wrn"
    log_path = case_dir / "model.log"
    err_path = case_dir / "w2.err"
    warn_text = read_text(warn_path)
    log_text = read_text(log_path)
    err_text = read_text(err_path) if err_path.exists() else ""
    wl_path = case_dir / "wl.csv"
    has_required_outputs = wl_path.exists() and (case_dir / "flowbal.csv").exists()
    missing_markers = [marker for marker in REQUIRED_MARKERS if marker not in warn_text]
    has_late_seg2_add = LATE_SEG2_PATTERN in warn_text
    has_runtime_error = "Runtime error" in log_text or len(err_text.strip()) > 0
    computational_warning_count = count_computational_warnings(warn_text)
    has_v2_front_state = "[V2_FRONT_STATE] JB=1" in warn_text
    has_v3_inner_iter = "[V3_INNER_ITER]" in warn_text
    has_v4_front_geom = "[V4_FRONT_GEOM] JB=1" in warn_text
    has_v5_transition = "[V5_TRANSITION] JB=1" in warn_text
    has_v6_coupling = "[V6_COUPLING] JB=1" in warn_text
    has_v7_tail_stage = "[V7_TAIL_STAGE] JB=1" in warn_text
    has_v8_front_sync = "[V8_FRONT_SYNC] JB=1" in warn_text
    has_v9_tail_feedback = "[V9_TAIL_FEEDBACK] JB=1" in warn_text
    has_v10_tail_reach = "[V10_TAIL_REACH] JB=1" in warn_text
    v11_matches = list(V11_TAIL_DOMAIN_PATTERN.finditer(warn_text))
    has_v11_tail_domain = any(int(match.group("jb")) == 1 for match in v11_matches)
    has_v12_q_state = "[V12_Q_STATE] JB=1" in warn_text
    has_v13_transition_reach = "[V13_TRANSITION_REACH] JB=1" in warn_text
    has_v14_coupled_hybrid = "[V14_COUPLED_HYBRID] JB=1" in warn_text
    v15_matches = list(V15_TAIL_DOMAIN_PATTERN.finditer(warn_text))
    has_v15_tail_domain_multi = len(v15_matches) > 0
    v16_matches = list(V16_SEGMENT_Q_STATE_PATTERN.finditer(warn_text))
    has_v16_segment_q_state = len(v16_matches) > 0
    v17_matches = list(V17_SEGMENT_TRANSITION_PATTERN.finditer(warn_text))
    has_v17_segment_transition = len(v17_matches) > 0
    v18_matches = list(V18_MULTI_HYBRID_PATTERN.finditer(warn_text))
    has_v18_multi_hybrid = len(v18_matches) > 0
    v19_matches = list(V19_INTERFACE_RESIDUAL_PATTERN.finditer(warn_text))
    has_v19_interface_residual = len(v19_matches) > 0
    v20_matches = list(V20_INTERFACE_ITER_PATTERN.finditer(warn_text))
    has_v20_interface_iter = len(v20_matches) > 0
    v21_matches = list(V21_INTERFACE_SOLVE_PATTERN.finditer(warn_text))
    has_v21_interface_solve = len(v21_matches) > 0
    v24_matches = list(V24_INTERFACE_MASS_PATTERN.finditer(warn_text))
    has_v24_interface_mass = len(v24_matches) > 0
    v24_commit_matches = list(V24_INTERFACE_COMMIT_PATTERN.finditer(warn_text))
    has_v24_interface_commit = len(v24_commit_matches) > 0
    v26_contract = parse_v26_contract(warn_text)
    v27_contract = parse_v27_profile_contract(warn_text)
    v31_contract = parse_v31_single_step_contract(warn_text)
    v32_contract = parse_v32_segment_volume_contract(warn_text)
    accepted_tail_state_count = warn_text.count("[V29_ACCEPTED_TAIL] JB=1")
    tail_predictor_pass_count = sum(1 for match in v18_matches if match.group("pass") == "1")
    tail_corrector_pass_count = sum(1 for match in v18_matches if match.group("pass") == "2")
    tail_iface_resid_max_eta = max((abs(float(match.group("deta"))) for match in v19_matches), default=0.0)
    tail_iface_resid_max_q = max((abs(float(match.group("dq"))) for match in v19_matches), default=0.0)
    tail_iface_iter_max = max((int(match.group("iter")) for match in v20_matches), default=0)
    tail_iface_iter_converged_count = sum(1 for match in v20_matches if match.group("conv").upper() == "T")
    tail_iface_linear_updates = len(v21_matches)
    tail_interface_mass_count = len(v24_matches)
    tail_mass_resid_max = max((abs(float(match.group("rtail"))) for match in v24_matches), default=0.0)
    tail_flux_gap_max = max((abs(float(match.group("rflux"))) for match in v24_matches), default=0.0)
    tail_combined_mass_resid_max = max((abs(float(match.group("rcomb"))) for match in v24_matches), default=0.0)
    tail_segment_q_loss_max = max((abs(float(match.group("segloss"))) for match in v24_matches), default=0.0)
    tail_interface_commit_count = len(v24_commit_matches)
    tail_interface_commit_q_gap_max = max(
        (abs(float(match.group("qres")) - float(match.group("qcommit"))) for match in v24_commit_matches),
        default=0.0,
    )
    tail_interface_commit_eta_applied_max = max(
        (abs(float(match.group("deta_applied"))) for match in v24_commit_matches),
        default=0.0,
    )
    tail_interface_commit_all_evaluated = bool(v24_commit_matches) and all(
        match.group("evaluated").upper() == "T" for match in v24_commit_matches
    )
    branch_v11 = next((match for match in v11_matches if int(match.group("jb")) == 1), None)
    branch_v15 = next((match for match in v15_matches if int(match.group("jb")) == 1), None)
    tail_link_dn = int(branch_v11.group("link_dn")) if branch_v11 else 0
    tail_couple_seg = int(branch_v15.group("couple")) if branch_v15 else 0
    tail_interface_boundary_aligned = bool(branch_v11 and branch_v15) and (
        branch_v11.group("defined").upper() == "T"
        and tail_link_dn == tail_couple_seg
        and tail_link_dn == int(branch_v11.group("ds")) + 1
    )
    tail_domain_nseg_min = min((int(match.group("nseg")) for match in v15_matches), default=0)
    tail_segment_state_count = len(v16_matches)
    tail_mode_values = sorted({int(match.group("mode")) for match in v17_matches})
    tail_mode_set = ",".join(str(value) for value in tail_mode_values)
    seg2_valid_count = 0
    seg222_valid_count = 0
    if wl_path.exists():
        with wl_path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
            reader = csv.DictReader(handle)
            seg2_key = None
            seg222_key = None
            for row in reader:
                if seg2_key is None:
                    seg2_key = next((key for key in row.keys() if key.strip() == "SEG   2"), None)
                    seg222_key = next((key for key in row.keys() if key.strip() == "SEG 222"), None)
                if seg2_key:
                    try:
                        if float(row[seg2_key]) > -900.0:
                            seg2_valid_count += 1
                    except (TypeError, ValueError):
                        pass
                if seg222_key:
                    try:
                        if float(row[seg222_key]) > -900.0:
                            seg222_valid_count += 1
                    except (TypeError, ValueError):
                        pass
    return SmokeResult(
        case_dir=case_dir,
        warn_path=warn_path,
        log_path=log_path,
        err_path=err_path,
        missing_markers=missing_markers,
        has_late_seg2_add=has_late_seg2_add,
        has_runtime_error=has_runtime_error,
        computational_warning_count=computational_warning_count,
        has_v2_front_state=has_v2_front_state,
        has_required_outputs=has_required_outputs,
        has_v3_inner_iter=has_v3_inner_iter,
        has_v4_front_geom=has_v4_front_geom,
        has_v5_transition=has_v5_transition,
        has_v6_coupling=has_v6_coupling,
        has_v7_tail_stage=has_v7_tail_stage,
        has_v8_front_sync=has_v8_front_sync,
        has_v9_tail_feedback=has_v9_tail_feedback,
        has_v10_tail_reach=has_v10_tail_reach,
        has_v11_tail_domain=has_v11_tail_domain,
        has_v12_q_state=has_v12_q_state,
        has_v13_transition_reach=has_v13_transition_reach,
        has_v14_coupled_hybrid=has_v14_coupled_hybrid,
        has_v15_tail_domain_multi=has_v15_tail_domain_multi,
        has_v16_segment_q_state=has_v16_segment_q_state,
        has_v17_segment_transition=has_v17_segment_transition,
        has_v18_multi_hybrid=has_v18_multi_hybrid,
        has_v19_interface_residual=has_v19_interface_residual,
        has_v20_interface_iter=has_v20_interface_iter,
        has_v21_interface_solve=has_v21_interface_solve,
        has_v24_interface_mass=has_v24_interface_mass,
        has_v24_interface_commit=has_v24_interface_commit,
        has_v26_domain_owner=bool(v26_contract["has_domain_owner"]),
        has_v26_boundary_consumer=bool(v26_contract["has_boundary_consumer"]),
        has_v27_profile_storage=bool(v27_contract["has_profile_storage"]),
        tail_predictor_pass_count=tail_predictor_pass_count,
        tail_corrector_pass_count=tail_corrector_pass_count,
        tail_iface_resid_max_eta=tail_iface_resid_max_eta,
        tail_iface_resid_max_q=tail_iface_resid_max_q,
        tail_iface_iter_max=tail_iface_iter_max,
        tail_iface_iter_converged_count=tail_iface_iter_converged_count,
        tail_iface_linear_updates=tail_iface_linear_updates,
        tail_interface_mass_count=tail_interface_mass_count,
        tail_mass_resid_max=tail_mass_resid_max,
        tail_flux_gap_max=tail_flux_gap_max,
        tail_combined_mass_resid_max=tail_combined_mass_resid_max,
        tail_segment_q_loss_max=tail_segment_q_loss_max,
        tail_interface_commit_count=tail_interface_commit_count,
        tail_interface_commit_q_gap_max=tail_interface_commit_q_gap_max,
        tail_interface_commit_eta_applied_max=tail_interface_commit_eta_applied_max,
        tail_interface_commit_all_evaluated=tail_interface_commit_all_evaluated,
        tail_link_dn=tail_link_dn,
        tail_couple_seg=tail_couple_seg,
        tail_interface_boundary_aligned=tail_interface_boundary_aligned,
        tail_active_cus=int(v26_contract["active_cus"]),
        tail_domain_owner_exclusive=bool(v26_contract["exclusive"]),
        reservoir_boundary_consumer_count=int(v26_contract["consumer_count"]),
        reservoir_boundary_flux_gap_max=float(v26_contract["consumer_gap_max"]),
        tail_profile_storage_count=int(v27_contract["profile_count"]),
        tail_profile_storage_gap_max=float(v27_contract["profile_gap_max"]),
        tail_reach_length_min=float(v27_contract["reach_length_min"]),
        tail_reach_length_max=float(v27_contract["reach_length_max"]),
        accepted_tail_state_count=accepted_tail_state_count,
        tail_single_step_count=int(v31_contract["count"]),
        tail_full_storage_resid_max=float(v31_contract["full_storage_resid_max"]),
        tail_storage_rate_gap_max=float(v31_contract["storage_rate_gap_max"]),
        tail_segment_volume_count=int(v32_contract["count"]),
        tail_segment_volume_gap_max=float(v32_contract["segment_volume_gap_max"]),
        tail_domain_nseg_min=tail_domain_nseg_min,
        tail_segment_state_count=tail_segment_state_count,
        tail_mode_set=tail_mode_set,
        seg2_valid_count=seg2_valid_count,
        seg222_valid_count=seg222_valid_count,
    )


def write_summary(result: SmokeResult, exe_path: Path, tmend: float) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    summary_path = RESULTS_ROOT / f"smoke-summary-{stamp}.csv"
    with open(summary_path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["field", "value"])
        writer.writerow(["exe_path", str(exe_path)])
        writer.writerow(["tmend", trim_float(tmend)])
        writer.writerow(["warn_path", str(result.warn_path)])
        writer.writerow(["log_path", str(result.log_path)])
        writer.writerow(["err_path", str(result.err_path)])
        writer.writerow(["missing_markers", ";".join(result.missing_markers)])
        writer.writerow(["has_late_seg2_add", "1" if result.has_late_seg2_add else "0"])
        writer.writerow(["has_runtime_error", "1" if result.has_runtime_error else "0"])
        writer.writerow(["computational_warning_count", str(result.computational_warning_count)])
        writer.writerow(["has_v2_front_state", "1" if result.has_v2_front_state else "0"])
        writer.writerow(["has_required_outputs", "1" if result.has_required_outputs else "0"])
        writer.writerow(["has_v3_inner_iter", "1" if result.has_v3_inner_iter else "0"])
        writer.writerow(["has_v4_front_geom", "1" if result.has_v4_front_geom else "0"])
        writer.writerow(["has_v5_transition", "1" if result.has_v5_transition else "0"])
        writer.writerow(["has_v6_coupling", "1" if result.has_v6_coupling else "0"])
        writer.writerow(["has_v7_tail_stage", "1" if result.has_v7_tail_stage else "0"])
        writer.writerow(["has_v8_front_sync", "1" if result.has_v8_front_sync else "0"])
        writer.writerow(["has_v9_tail_feedback", "1" if result.has_v9_tail_feedback else "0"])
        writer.writerow(["has_v10_tail_reach", "1" if result.has_v10_tail_reach else "0"])
        writer.writerow(["has_v11_tail_domain", "1" if result.has_v11_tail_domain else "0"])
        writer.writerow(["has_v12_q_state", "1" if result.has_v12_q_state else "0"])
        writer.writerow(["has_v13_transition_reach", "1" if result.has_v13_transition_reach else "0"])
        writer.writerow(["has_v14_coupled_hybrid", "1" if result.has_v14_coupled_hybrid else "0"])
        writer.writerow(["has_v15_tail_domain_multi", "1" if result.has_v15_tail_domain_multi else "0"])
        writer.writerow(["has_v16_segment_q_state", "1" if result.has_v16_segment_q_state else "0"])
        writer.writerow(["has_v17_segment_transition", "1" if result.has_v17_segment_transition else "0"])
        writer.writerow(["has_v18_multi_hybrid", "1" if result.has_v18_multi_hybrid else "0"])
        writer.writerow(["has_v19_interface_residual", "1" if result.has_v19_interface_residual else "0"])
        writer.writerow(["has_v20_interface_iter", "1" if result.has_v20_interface_iter else "0"])
        writer.writerow(["has_v21_interface_solve", "1" if result.has_v21_interface_solve else "0"])
        writer.writerow(["has_v24_interface_mass", "1" if result.has_v24_interface_mass else "0"])
        writer.writerow(["has_v24_interface_commit", "1" if result.has_v24_interface_commit else "0"])
        writer.writerow(["has_v26_domain_owner", "1" if result.has_v26_domain_owner else "0"])
        writer.writerow(["has_v26_boundary_consumer", "1" if result.has_v26_boundary_consumer else "0"])
        writer.writerow(["has_v27_profile_storage", "1" if result.has_v27_profile_storage else "0"])
        writer.writerow(["tail_predictor_pass_count", str(result.tail_predictor_pass_count)])
        writer.writerow(["tail_corrector_pass_count", str(result.tail_corrector_pass_count)])
        writer.writerow(["tail_iface_resid_max_eta", f"{result.tail_iface_resid_max_eta:.6f}"])
        writer.writerow(["tail_iface_resid_max_q", f"{result.tail_iface_resid_max_q:.6f}"])
        writer.writerow(["tail_iface_iter_max", str(result.tail_iface_iter_max)])
        writer.writerow(["tail_iface_iter_converged_count", str(result.tail_iface_iter_converged_count)])
        writer.writerow(["tail_iface_linear_updates", str(result.tail_iface_linear_updates)])
        writer.writerow(["tail_interface_mass_count", str(result.tail_interface_mass_count)])
        writer.writerow(["tail_mass_resid_max", f"{result.tail_mass_resid_max:.6f}"])
        writer.writerow(["tail_flux_gap_max", f"{result.tail_flux_gap_max:.6f}"])
        writer.writerow(["tail_combined_mass_resid_max", f"{result.tail_combined_mass_resid_max:.6f}"])
        writer.writerow(["tail_segment_q_loss_max", f"{result.tail_segment_q_loss_max:.6f}"])
        writer.writerow(["tail_interface_commit_count", str(result.tail_interface_commit_count)])
        writer.writerow(["tail_interface_commit_q_gap_max", f"{result.tail_interface_commit_q_gap_max:.6f}"])
        writer.writerow(["tail_interface_commit_eta_applied_max", f"{result.tail_interface_commit_eta_applied_max:.6f}"])
        writer.writerow(
            ["tail_interface_commit_all_evaluated", "1" if result.tail_interface_commit_all_evaluated else "0"]
        )
        writer.writerow(["tail_link_dn", str(result.tail_link_dn)])
        writer.writerow(["tail_couple_seg", str(result.tail_couple_seg)])
        writer.writerow(["tail_interface_boundary_aligned", "1" if result.tail_interface_boundary_aligned else "0"])
        writer.writerow(["tail_active_cus", str(result.tail_active_cus)])
        writer.writerow(["tail_domain_owner_exclusive", "1" if result.tail_domain_owner_exclusive else "0"])
        writer.writerow(["reservoir_boundary_consumer_count", str(result.reservoir_boundary_consumer_count)])
        writer.writerow(["reservoir_boundary_flux_gap_max", f"{result.reservoir_boundary_flux_gap_max:.6f}"])
        writer.writerow(["tail_profile_storage_count", str(result.tail_profile_storage_count)])
        writer.writerow(["tail_profile_storage_gap_max", f"{result.tail_profile_storage_gap_max:.6f}"])
        writer.writerow(["tail_reach_length_min", f"{result.tail_reach_length_min:.6f}"])
        writer.writerow(["tail_reach_length_max", f"{result.tail_reach_length_max:.6f}"])
        writer.writerow(["accepted_tail_state_count", str(result.accepted_tail_state_count)])
        writer.writerow(["tail_single_step_count", str(result.tail_single_step_count)])
        writer.writerow(["tail_full_storage_resid_max", f"{result.tail_full_storage_resid_max:.12e}"])
        writer.writerow(["tail_storage_rate_gap_max", f"{result.tail_storage_rate_gap_max:.12e}"])
        writer.writerow(["tail_segment_volume_count", str(result.tail_segment_volume_count)])
        writer.writerow(["tail_segment_volume_gap_max", f"{result.tail_segment_volume_gap_max:.12e}"])
        writer.writerow(["tail_domain_nseg_min", str(result.tail_domain_nseg_min)])
        writer.writerow(["tail_segment_state_count", str(result.tail_segment_state_count)])
        writer.writerow(["tail_mode_set", result.tail_mode_set])
        writer.writerow(["seg2_valid_count", str(result.seg2_valid_count)])
        writer.writerow(["seg222_valid_count", str(result.seg222_valid_count)])
    return summary_path


def v24_conservation_errors(result: SmokeResult) -> list[str]:
    errors: list[str] = []
    if not result.has_v24_interface_mass:
        errors.append("Missing V24 interface-mass marker")
    if not result.has_v24_interface_commit:
        errors.append("Missing V24 interface-commit marker")
    if result.tail_interface_mass_count <= 0:
        errors.append("V24 interface-mass sample count is below 1")
    if result.tail_interface_commit_count <= 0:
        errors.append("V24 interface-commit sample count is below 1")
    if not result.tail_interface_commit_all_evaluated:
        errors.append("V24 interface commit contains an unevaluated state")
    conservation_tolerance = 1.0e-6
    if result.tail_interface_commit_q_gap_max > conservation_tolerance:
        errors.append(f"V24 committed interface flux gap exceeds tolerance: {result.tail_interface_commit_q_gap_max}")
    if result.tail_mass_resid_max > conservation_tolerance:
        errors.append(f"V24 tail mass residual exceeds tolerance: {result.tail_mass_resid_max}")
    if result.tail_flux_gap_max > conservation_tolerance:
        errors.append(f"V24 reservoir/tail flux gap exceeds tolerance: {result.tail_flux_gap_max}")
    if result.tail_combined_mass_resid_max > conservation_tolerance:
        errors.append(f"V24 combined mass residual exceeds tolerance: {result.tail_combined_mass_resid_max}")
    if result.tail_segment_q_loss_max > conservation_tolerance:
        errors.append(f"V24 segment flow loss exceeds tolerance: {result.tail_segment_q_loss_max}")
    return errors


def assert_v24_conservation(result: SmokeResult) -> None:
    errors = v24_conservation_errors(result)
    if errors:
        raise AssertionError(" | ".join(errors))


def assert_v25_boundary_alignment(result: SmokeResult) -> None:
    if not result.tail_interface_boundary_aligned:
        raise AssertionError(
            f"Tail interface boundary is not aligned: LINK_DN={result.tail_link_dn}, COUPLE={result.tail_couple_seg}"
        )


def assert_no_computational_warning(result: SmokeResult) -> None:
    if result.computational_warning_count > 0:
        raise AssertionError(f"Detected {result.computational_warning_count} computational warning(s)")


def assert_v26_domain_ownership(result: SmokeResult) -> None:
    errors: list[str] = []
    if not result.has_v26_domain_owner:
        errors.append("Missing V26 domain-owner marker")
    if not result.has_v26_boundary_consumer:
        errors.append("Missing V26 boundary-consumer marker")
    if not result.tail_domain_owner_exclusive:
        errors.append("Tail/reservoir domain ownership is not exclusive")
    if result.tail_active_cus != result.tail_couple_seg:
        errors.append(f"Active CUS does not match coupling segment: CUS={result.tail_active_cus}, COUPLE={result.tail_couple_seg}")
    if result.reservoir_boundary_consumer_count <= 0:
        errors.append("V26 reservoir boundary-consumer sample count is below 1")
    if result.reservoir_boundary_flux_gap_max > 1.0e-6:
        errors.append(f"V26 reservoir boundary consumer flux gap exceeds tolerance: {result.reservoir_boundary_flux_gap_max}")
    if errors:
        raise AssertionError(" | ".join(errors))


def assert_v27_profile_storage(result: SmokeResult) -> None:
    errors: list[str] = []
    if not result.has_v27_profile_storage:
        errors.append("Missing V27 profile-storage marker")
    if result.tail_profile_storage_count <= 0:
        errors.append("V27 profile-storage sample count is below 1")
    if result.tail_profile_storage_gap_max > 1.0e-2:
        errors.append(f"V27 profile storage gap exceeds tolerance: {result.tail_profile_storage_gap_max}")
    if abs(result.tail_reach_length_min-3855.0) > 1.0e-6 or abs(result.tail_reach_length_max-3855.0) > 1.0e-6:
        errors.append(
            f"V27 reach length does not match center distance: min={result.tail_reach_length_min}, max={result.tail_reach_length_max}"
        )
    if errors:
        raise AssertionError(" | ".join(errors))


def assert_v29_accepted_diagnostics(result: SmokeResult) -> None:
    if result.accepted_tail_state_count <= 0:
        raise AssertionError("V29 accepted tail-state sample count is below 1")


def assert_v31_single_step(result: SmokeResult) -> None:
    errors: list[str] = []
    if result.tail_single_step_count <= 0:
        errors.append("V31 single-step sample count is below 1")
    if result.tail_full_storage_resid_max > 1.0e-8:
        errors.append(f"V31 full-step tail residual exceeds tolerance: {result.tail_full_storage_resid_max:.12e}")
    if result.tail_storage_rate_gap_max > 1.0e-8:
        errors.append(f"V31 full/local storage-rate gap exceeds tolerance: {result.tail_storage_rate_gap_max:.12e}")
    if errors:
        raise AssertionError(" | ".join(errors))


def assert_v32_segment_volume(result: SmokeResult) -> None:
    errors: list[str] = []
    if result.tail_segment_volume_count <= 0:
        errors.append("V32 segment-volume sample count is below 1")
    if result.tail_segment_volume_gap_max > 1.0e-2:
        errors.append(f"V32 segment/total volume gap exceeds tolerance: {result.tail_segment_volume_gap_max:.12e}")
    if errors:
        raise AssertionError(" | ".join(errors))


def assert_pass(result: SmokeResult, tmend: float) -> None:
    errors: list[str] = []
    if result.missing_markers:
        errors.append(f"Missing diagnostics: {', '.join(result.missing_markers)}")
    if result.has_late_seg2_add:
        errors.append(f"Found late upstream activation pattern: {LATE_SEG2_PATTERN}")
    if result.has_runtime_error:
        errors.append(f"Detected runtime error output: {result.err_path}")
    if result.computational_warning_count > 0:
        errors.append(f"Detected {result.computational_warning_count} computational warning(s)")
    if not result.tail_domain_owner_exclusive and not result.has_v2_front_state:
        errors.append("Missing V2 front-state marker for non-exclusive tail domain")
    if not result.has_required_outputs:
        errors.append("Missing required smoke outputs wl.csv or flowbal.csv")
    if not result.has_v3_inner_iter:
        errors.append("Missing V3 inner-iteration marker")
    if not result.tail_domain_owner_exclusive and not result.has_v4_front_geom:
        errors.append("Missing V4 front-geometry marker for non-exclusive tail domain")
    if not result.tail_domain_owner_exclusive and not result.has_v5_transition:
        errors.append("Missing V5 transition marker for non-exclusive tail domain")
    if not result.tail_domain_owner_exclusive and not result.has_v6_coupling:
        errors.append("Missing V6 coupling marker for non-exclusive tail domain")
    if not result.has_v7_tail_stage:
        errors.append("Missing V7 tail-stage marker for JB=1")
    if not result.tail_domain_owner_exclusive and not result.has_v8_front_sync:
        errors.append("Missing V8 front-sync marker for non-exclusive tail domain")
    if not result.has_v9_tail_feedback:
        errors.append("Missing V9 tail-feedback marker for JB=1")
    if not result.has_v10_tail_reach:
        errors.append("Missing V10 tail-reach marker for JB=1")
    if not result.has_v11_tail_domain:
        errors.append("Missing V11 tail-domain marker for JB=1")
    if not result.has_v12_q_state:
        errors.append("Missing V12 q-state marker for JB=1")
    if not result.has_v13_transition_reach:
        errors.append("Missing V13 transition-reach marker for JB=1")
    if not result.has_v14_coupled_hybrid:
        errors.append("Missing V14 coupled-hybrid marker for JB=1")
    if not result.has_v15_tail_domain_multi:
        errors.append("Missing V15 tail-domain multi-segment marker")
    if not result.has_v16_segment_q_state:
        errors.append("Missing V16 segment Q-state marker")
    if not result.has_v17_segment_transition:
        errors.append("Missing V17 segment-transition marker")
    if not result.has_v18_multi_hybrid:
        errors.append("Missing V18 multi-hybrid marker")
    if not result.has_v19_interface_residual:
        errors.append("Missing V19 interface-residual marker")
    if not result.has_v20_interface_iter:
        errors.append("Missing V20 interface-iteration marker")
    if not result.has_v21_interface_solve:
        errors.append("Missing V21 interface-solve marker")
    if result.tail_predictor_pass_count <= 0:
        errors.append("V18 predictor pass count is below 1")
    if result.tail_corrector_pass_count <= 0:
        errors.append("V18 corrector pass count is below 1")
    if result.tail_iface_resid_max_eta > 1.0e-6:
        errors.append(f"V19 committed eta residual exceeds tolerance: {result.tail_iface_resid_max_eta:.6f}")
    if result.tail_iface_resid_max_q > 1.0e-6:
        errors.append(f"V19 committed q residual exceeds tolerance: {result.tail_iface_resid_max_q:.6f}")
    if result.tail_iface_iter_max <= 0:
        errors.append(f"V20 max interface iteration is below 1: {result.tail_iface_iter_max}")
    if result.tail_iface_iter_converged_count <= 0:
        errors.append("V20 converged interface-iteration count is below 1")
    if result.tail_iface_linear_updates <= 0:
        errors.append("V21 reduced implicit update count is below 1")
    errors.extend(v24_conservation_errors(result))
    if not result.tail_interface_boundary_aligned:
        errors.append(
            f"Tail interface boundary is not aligned: LINK_DN={result.tail_link_dn}, COUPLE={result.tail_couple_seg}"
        )
    if not result.has_v26_domain_owner:
        errors.append("Missing V26 domain-owner marker")
    if not result.has_v26_boundary_consumer:
        errors.append("Missing V26 boundary-consumer marker")
    if not result.tail_domain_owner_exclusive:
        errors.append("Tail/reservoir domain ownership is not exclusive")
    if result.tail_active_cus != result.tail_couple_seg:
        errors.append(f"Active CUS does not match coupling segment: CUS={result.tail_active_cus}, COUPLE={result.tail_couple_seg}")
    if result.reservoir_boundary_flux_gap_max > 1.0e-6:
        errors.append(f"V26 reservoir boundary consumer flux gap exceeds tolerance: {result.reservoir_boundary_flux_gap_max}")
    if not result.has_v27_profile_storage:
        errors.append("Missing V27 profile-storage marker")
    if result.tail_profile_storage_gap_max > 1.0e-2:
        errors.append(f"V27 profile storage gap exceeds tolerance: {result.tail_profile_storage_gap_max}")
    if abs(result.tail_reach_length_min-3855.0) > 1.0e-6 or abs(result.tail_reach_length_max-3855.0) > 1.0e-6:
        errors.append(
            f"V27 reach length does not match center distance: min={result.tail_reach_length_min}, max={result.tail_reach_length_max}"
        )
    if result.tail_single_step_count <= 0:
        errors.append("V31 single-step sample count is below 1")
    if result.tail_full_storage_resid_max > 1.0e-8:
        errors.append(f"V31 full-step tail residual exceeds tolerance: {result.tail_full_storage_resid_max:.12e}")
    if result.tail_storage_rate_gap_max > 1.0e-8:
        errors.append(f"V31 full/local storage-rate gap exceeds tolerance: {result.tail_storage_rate_gap_max:.12e}")
    if result.tail_segment_volume_count <= 0:
        errors.append("V32 segment-volume sample count is below 1")
    if result.tail_segment_volume_gap_max > 1.0e-2:
        errors.append(f"V32 segment/total volume gap exceeds tolerance: {result.tail_segment_volume_gap_max:.12e}")
    if result.tail_domain_nseg_min < 2:
        errors.append(f"Tail domain minimum segment count is below 2: {result.tail_domain_nseg_min}")
    if result.tail_segment_state_count < 2:
        errors.append(f"Tail segment state count is below 2: {result.tail_segment_state_count}")
    # Full 0/1/2 mode coverage is only required on the long validation window.
    if tmend >= 44458.0 and result.tail_mode_set != "0,1,2":
        errors.append(f"Tail mode set is incomplete for long window: {result.tail_mode_set or '(empty)'}")
    if result.seg2_valid_count <= 0:
        errors.append("SEG 2 still has no valid water-level output")
    if errors:
        raise AssertionError(" | ".join(errors))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Short-window smoke test for W2 V0+V1 hydrodynamic foundation.")
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE, help="Path to the executable to validate.")
    parser.add_argument("--tmend", type=float, default=DEFAULT_TMEND, help="Short-window TMEND value.")
    parser.add_argument("--keep-case", action="store_true", help="Keep the prepared case directory instead of refreshing it.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_dirs()
    if not args.keep_case:
      clone_case_tree(CASE_ROOT)
    update_tmend(CASE_ROOT / "w2_con.csv", args.tmend)
    stage_exe(CASE_ROOT, args.exe)
    run_case(CASE_ROOT)
    result = evaluate(CASE_ROOT)
    summary_path = write_summary(result, args.exe, args.tmend)
    print(f"Summary: {summary_path}")
    assert_pass(result, args.tmend)
    print("Smoke test passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI failure path
        print(f"SMOKE TEST FAILED: {exc}", file=sys.stderr)
        raise
