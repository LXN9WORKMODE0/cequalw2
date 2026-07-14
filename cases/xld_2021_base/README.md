# XLD 2021 baseline case

This is the single Git-tracked baseline used by the analysis and verification
scripts. It contains model inputs and observations only. Generated executables,
logs, model outputs, and experiment copies belong under `analysis/.runs/` and
are intentionally ignored by Git.

`fixtures/distributed_flow/` contains the reference distributed-flow series used by
`analysis/run_xld_matrix.py`; it is analysis input, not model runtime output.

Build the console model before running experiments. Scripts stage the executable
from `w2source_v455_2_11_2026/build_console/w2_v455_console.exe` into each run.
