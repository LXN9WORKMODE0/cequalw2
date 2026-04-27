# XLD Multifactors

`analysis/run_xld_matrix.py` 会在不改动 `实际案例` 原目录的前提下：

- 复制实验 case 到 `analysis/xld_multifactor/cases/`
- 批量修改 distributed、几何和支流入流方案
- 调用 `preW2-v45_64.exe` 与 `w2_v455_console.exe`
- 产出 `summary_screen.csv`、`summary_full.csv`、`ranking.md`
- 为每个 case 输出坝前水位对比图、水面线图、日均流量表和层/段事件摘要

脚本默认使用：

- screening 窗口：`44430-44458`
- full 窗口：`44430-44484`
- 并行数：`2`

当前版本只依赖 Python 标准库。
