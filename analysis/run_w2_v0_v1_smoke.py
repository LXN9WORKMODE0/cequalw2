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
SOURCE_CASE = REPO_ROOT / "实际案例"
FALLBACK_BTH_FILE = SOURCE_CASE / "InputFiles" / "BTH" / "DIXING20250226.csv"
WORK_ROOT = REPO_ROOT / "analysis" / "verification" / "w2_v0_v1_smoke"
CASE_ROOT = WORK_ROOT / "case"
RESULTS_ROOT = WORK_ROOT / "results"
DEFAULT_EXE = SOURCE_CASE / "w2_v455_console.exe"
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
    "[V0_SEGMENT_ADD_CHECK]",
    "[V2_FRONT_STATE]",
    "[V3_INNER_ITER]",
    "[V4_FRONT_GEOM]",
    "[V5_TRANSITION]",
    "[V6_COUPLING]",
    "[V7_TAIL_STAGE]",
    "[V8_FRONT_SYNC]",
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
    "[V18_PREDICT_REUSE]",
    "[V19_INTERFACE_RESIDUAL]",
    "[V20_INTERFACE_ITER]",
    "[V21_INTERFACE_SOLVE]",
]
LATE_SEG2_PATTERN = "Add segments 2 through 2"
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
V18_PREDICT_REUSE_PATTERN = re.compile(
    r"\[V18_PREDICT_REUSE\].*?JB=(?P<jb>\d+).*?SKIP=(?P<skip>\d+).*?QLINK=(?P<qlink>[-+0-9.eE]+).*?WSE_DN=(?P<wse_dn>[-+0-9.eE]+)",
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


@dataclass
class SmokeResult:
    case_dir: Path
    warn_path: Path
    log_path: Path
    err_path: Path
    missing_markers: list[str]
    has_late_seg2_add: bool
    has_runtime_error: bool
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
    has_v18_predict_reuse: bool
    has_v19_interface_residual: bool
    has_v20_interface_iter: bool
    has_v21_interface_solve: bool
    tail_predictor_pass_count: int
    tail_corrector_pass_count: int
    tail_predictor_skip_count: int
    tail_iface_resid_max_eta: float
    tail_iface_resid_max_q: float
    tail_iface_iter_max: int
    tail_iface_iter_converged_count: int
    tail_iface_linear_updates: int
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
    has_v2_front_state = "[V2_FRONT_STATE] JB=1" in warn_text
    has_v3_inner_iter = "[V3_INNER_ITER]" in warn_text
    has_v4_front_geom = "[V4_FRONT_GEOM] JB=1" in warn_text
    has_v5_transition = "[V5_TRANSITION] JB=1" in warn_text
    has_v6_coupling = "[V6_COUPLING] JB=1" in warn_text
    has_v7_tail_stage = "[V7_TAIL_STAGE] JB=1" in warn_text
    has_v8_front_sync = "[V8_FRONT_SYNC] JB=1" in warn_text
    has_v9_tail_feedback = "[V9_TAIL_FEEDBACK] JB=1" in warn_text
    has_v10_tail_reach = "[V10_TAIL_REACH] JB=1" in warn_text
    has_v11_tail_domain = "[V11_TAIL_DOMAIN] JB=1" in warn_text
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
    v18_skip_matches = list(V18_PREDICT_REUSE_PATTERN.finditer(warn_text))
    has_v18_predict_reuse = len(v18_skip_matches) > 0
    v19_matches = list(V19_INTERFACE_RESIDUAL_PATTERN.finditer(warn_text))
    has_v19_interface_residual = len(v19_matches) > 0
    v20_matches = list(V20_INTERFACE_ITER_PATTERN.finditer(warn_text))
    has_v20_interface_iter = len(v20_matches) > 0
    v21_matches = list(V21_INTERFACE_SOLVE_PATTERN.finditer(warn_text))
    has_v21_interface_solve = len(v21_matches) > 0
    tail_predictor_pass_count = sum(1 for match in v18_matches if match.group("pass") == "1")
    tail_corrector_pass_count = sum(1 for match in v18_matches if match.group("pass") == "2")
    tail_predictor_skip_count = len(v18_skip_matches)
    tail_iface_resid_max_eta = max((abs(float(match.group("deta"))) for match in v19_matches), default=0.0)
    tail_iface_resid_max_q = max((abs(float(match.group("dq"))) for match in v19_matches), default=0.0)
    tail_iface_iter_max = max((int(match.group("iter")) for match in v20_matches), default=0)
    tail_iface_iter_converged_count = sum(1 for match in v20_matches if match.group("conv").upper() == "T")
    tail_iface_linear_updates = len(v21_matches)
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
        has_v18_predict_reuse=has_v18_predict_reuse,
        has_v19_interface_residual=has_v19_interface_residual,
        has_v20_interface_iter=has_v20_interface_iter,
        has_v21_interface_solve=has_v21_interface_solve,
        tail_predictor_pass_count=tail_predictor_pass_count,
        tail_corrector_pass_count=tail_corrector_pass_count,
        tail_predictor_skip_count=tail_predictor_skip_count,
        tail_iface_resid_max_eta=tail_iface_resid_max_eta,
        tail_iface_resid_max_q=tail_iface_resid_max_q,
        tail_iface_iter_max=tail_iface_iter_max,
        tail_iface_iter_converged_count=tail_iface_iter_converged_count,
        tail_iface_linear_updates=tail_iface_linear_updates,
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
        writer.writerow(["has_v18_predict_reuse", "1" if result.has_v18_predict_reuse else "0"])
        writer.writerow(["has_v19_interface_residual", "1" if result.has_v19_interface_residual else "0"])
        writer.writerow(["has_v20_interface_iter", "1" if result.has_v20_interface_iter else "0"])
        writer.writerow(["has_v21_interface_solve", "1" if result.has_v21_interface_solve else "0"])
        writer.writerow(["tail_predictor_pass_count", str(result.tail_predictor_pass_count)])
        writer.writerow(["tail_corrector_pass_count", str(result.tail_corrector_pass_count)])
        writer.writerow(["tail_predictor_skip_count", str(result.tail_predictor_skip_count)])
        writer.writerow(["tail_iface_resid_max_eta", f"{result.tail_iface_resid_max_eta:.6f}"])
        writer.writerow(["tail_iface_resid_max_q", f"{result.tail_iface_resid_max_q:.6f}"])
        writer.writerow(["tail_iface_iter_max", str(result.tail_iface_iter_max)])
        writer.writerow(["tail_iface_iter_converged_count", str(result.tail_iface_iter_converged_count)])
        writer.writerow(["tail_iface_linear_updates", str(result.tail_iface_linear_updates)])
        writer.writerow(["tail_domain_nseg_min", str(result.tail_domain_nseg_min)])
        writer.writerow(["tail_segment_state_count", str(result.tail_segment_state_count)])
        writer.writerow(["tail_mode_set", result.tail_mode_set])
        writer.writerow(["seg2_valid_count", str(result.seg2_valid_count)])
        writer.writerow(["seg222_valid_count", str(result.seg222_valid_count)])
    return summary_path


def assert_pass(result: SmokeResult, tmend: float) -> None:
    errors: list[str] = []
    if result.missing_markers:
        errors.append(f"Missing diagnostics: {', '.join(result.missing_markers)}")
    if result.has_late_seg2_add:
        errors.append(f"Found late upstream activation pattern: {LATE_SEG2_PATTERN}")
    if result.has_runtime_error:
        errors.append(f"Detected runtime error output: {result.err_path}")
    if not result.has_v2_front_state:
        errors.append("Missing V2 front-state marker for JB=1")
    if not result.has_required_outputs:
        errors.append("Missing required smoke outputs wl.csv or flowbal.csv")
    if not result.has_v3_inner_iter:
        errors.append("Missing V3 inner-iteration marker")
    if not result.has_v4_front_geom:
        errors.append("Missing V4 front-geometry marker for JB=1")
    if not result.has_v5_transition:
        errors.append("Missing V5 transition marker for JB=1")
    if not result.has_v6_coupling:
        errors.append("Missing V6 coupling marker for JB=1")
    if not result.has_v7_tail_stage:
        errors.append("Missing V7 tail-stage marker for JB=1")
    if not result.has_v8_front_sync:
        errors.append("Missing V8 front-sync marker for JB=1")
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
    if not result.has_v18_predict_reuse:
        errors.append("Missing V18 predictor-reuse marker")
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
    if result.tail_predictor_skip_count <= 0:
        errors.append("V18 predictor skip count is below 1")
    if result.tail_iface_resid_max_eta <= 0.0:
        errors.append(f"V19 max eta residual is non-positive: {result.tail_iface_resid_max_eta:.6f}")
    if result.tail_iface_resid_max_q <= 0.0:
        errors.append(f"V19 max q residual is non-positive: {result.tail_iface_resid_max_q:.6f}")
    if result.tail_iface_iter_max <= 0:
        errors.append(f"V20 max interface iteration is below 1: {result.tail_iface_iter_max}")
    if result.tail_iface_iter_converged_count <= 0:
        errors.append("V20 converged interface-iteration count is below 1")
    if result.tail_iface_linear_updates <= 0:
        errors.append("V21 reduced implicit update count is below 1")
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
