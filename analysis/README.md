# Analysis workspace

分析脚本统一读取 Git 跟踪的基线 `cases/xld_2021_base/`，并把案例副本、
模型输出、日志和汇总结果写入被 Git 忽略的 `analysis/.runs/`。运行脚本前需先
生成 `w2source_v455_2_11_2026/build_console/w2_v455_console.exe`。

主要入口：

- `run_xld_matrix.py`：distributed、几何与支流入流多因素矩阵；输出到
  `.runs/xld_multifactor/`。
- `run_structural_minimal_tests.py`：结构参数最小试验；输出到
  `.runs/structural_minimal/`。
- `run_w2_v0_v1_smoke.py`：可执行文件 smoke 验证；输出到
  `.runs/w2_v0_v1_smoke/`。
- `run_v21_bht_redistribution_scan.py`：BHT 重分配扫描；输出到
  `.runs/v21_bht_redistribution_scan/`。

2026-07-15 整理前的本地运行产物保存在
`.runs/archive_pre_v24/`，仅供追溯，不应作为新实验的完成状态复用。V21/V23 的
已提交汇总表继续保存在 `verification/v21_bht_redistribution_scan/`。

当前脚本只依赖 Python 标准库。
