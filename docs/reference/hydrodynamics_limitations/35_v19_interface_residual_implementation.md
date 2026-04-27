# V19 Interface Residual Implementation

本页回答什么问题：`V19` 是否已经把 tailreach/reservoir 接口残差显式化，残差量级大概有多大，以及这一步在当前代码线上是否稳定。

Updated: 2026-04-24

## 实现内容

`V19` 这一步没有改接口求解方式本身，而是先把原来隐含在 `V18` predictor/corrector 之间的接口差异显式记录出来。

本次实际落地了两部分：

- 在 `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2modules.F90`、`input.F90`、`init.F90` 中新增并初始化了：
  - `TAIL_IFACE_ETA_PRED / TAIL_IFACE_ETA_CORR`
  - `TAIL_IFACE_Q_PRED / TAIL_IFACE_Q_CORR`
  - `TAIL_IFACE_DETA / TAIL_IFACE_DQ`
  - `TAIL_IFACE_MAX_DETA / TAIL_IFACE_MAX_DQ`
- 在 `C:\Users\NING\Desktop\v455\w2source_v455_2_11_2026\w2_main.f90` 中，把 predictor 后和 corrector 后的接口状态显式写成：
  - `ETA_P, ETA_C`
  - `Q_P, Q_C`
  - `DETA = ETA_C - ETA_P`
  - `DQ = Q_C - Q_P`

对应的新诊断 marker 是：

```text
[V19_INTERFACE_RESIDUAL] JB=... DETA=... DQ=... ETA_P=... ETA_C=... Q_P=... Q_C=...
```

## 调试过程

这一版按 TDD 先把 smoke gate 接成红灯，再改 Fortran。

初始红灯发生了两次：

1. 先在 harness 里加入 `V19` marker 要求，现有 exe 在 profiling window 下确实因为缺少 `V19` 失败。
2. Fortran 实现完成后，第一次 `44435.4` 短窗 smoke 仍然失败，但根因不是求解器没输出，而是 harness 的 `V19` 正则没有容纳 `=` 后的空格。

这个根因已经确认：

- `w2.wrn` 里实际存在 `V19_INTERFACE_RESIDUAL`
- 失败是解析层问题，不是数值层问题

修正正则后，对同一份短窗结果重新评估，`V19` 就被正确识别了。

## 验证结果

### 1. Profiling 窗口红灯确认

使用 `TMEND=44431.0` 跑旧 exe，得到：

- `C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\results\smoke-summary-20260423-234749.csv`

这一步确认：

- `V19` 当时确实缺失
- 红灯建立是有效的

### 2. 短窗 `TMEND=44435.4`

短窗完整运行后得到：

- `C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\results\smoke-summary-20260424-001818.csv`

这份 summary 当时仍然报 `V19` 缺失，但后续已经证明那只是正则解析问题。对同一份 case 重新评估后，结果是：

- `has_v19_interface_residual = 1`
- `tail_iface_resid_max_eta = 1.3552`
- `tail_iface_resid_max_q = 5851.6`

而且短窗重评估已通过完整 smoke gate。

### 3. 扩展窗 `TMEND=44436.5`

扩展窗完整通过：

- `C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\results\smoke-summary-20260424-005831.csv`

关键字段：

- `missing_markers = 空`
- `has_runtime_error = 0`
- `has_v19_interface_residual = 1`
- `tail_iface_resid_max_eta = 1.3552`
- `tail_iface_resid_max_q = 5851.6`

### 4. 长窗 `TMEND=44458`

长窗不是 harness 默认 45 分钟内能收完，所以我改成手动 3 小时超时运行同一套 case 流程，得到：

- `C:\Users\NING\Desktop\v455\analysis\verification\w2_v0_v1_smoke\results\smoke-summary-20260424-044339.csv`

长窗结果显示：

- `missing_markers = 空`
- `has_runtime_error = 0`
- `has_v19_interface_residual = 1`
- `tail_iface_resid_max_eta = 1.3552`
- `tail_iface_resid_max_q = 5851.6`
- `seg2_valid_count = 281`
- `seg222_valid_count = 281`

这说明 `V19` 在长窗里本身是成立的。

长窗最终没有通过完整 smoke gate 的原因是：

- `tail_mode_set = 1,2`

这是现有长窗 gate 里的旧约束，属于当前 `V18`/`V17` 线上尚未解决的问题，不是 `V19` 这一步新引入的问题。

## 这一步回答了什么

`V19` 把一个之前只能靠“感觉接口不收敛”来描述的问题，变成了显式可追踪的量：

- 接口水位残差 `DETA`
- 接口流量残差 `DQ`

而且在当前案例里，初始暴露出来的量级已经很有信息量：

- `max |DETA| ≈ 1.3552 m`
- `max |DQ| ≈ 5851.6 m3/s`

这说明：

- `V18` 的接口 mismatch 不是微小噪声
- 后续 `V20/V21` 做真正的 interface iteration 和 reduced implicit correction 是有必要的

## 当前结论

`V19` 现在可以记成：

- 功能上已落地
- 短窗和扩展窗已验证通过
- 长窗中 `V19` 本身成立，但完整长窗 smoke 仍受既有 `tail_mode_set` 约束影响

所以它是一个有效完成、但尚未解决所有长窗历史门槛的阶段版本。
