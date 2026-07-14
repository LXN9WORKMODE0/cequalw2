# Git 工作流

## 远端与分支职责

- `origin`：`git@github.com:LXN9WORKMODE0/cequalw2.git`
- `main`：原始导入基线，仅接收已经验证、准备长期保留的合并。
- `codex/w2-hydro-v0-v1-foundation`：V0-V21 历史基础快照。
- `codex/w2-hydro-v23-diagnostics`：V22/V23 诊断代码、测试、文档与紧凑结果快照。
- `codex/w2-hydro-v24-interface-conservation`：当前开发分支，用于接口拓扑与守恒改造。

功能开发使用独立的 `codex/<主题>` 分支。验证完成后再合并到 `main`，不在 `main` 上直接试验。

## 每次开始工作

```powershell
git status --short --branch
git fetch --prune origin
git switch codex/w2-hydro-v24-interface-conservation
git pull --ff-only
```

`pull.ff=only` 已在本仓库中配置。远端和本地出现分叉时，Git 会停止并要求人工判断，不会自动生成合并提交。

## 提交与同步

只暂存本次目标涉及的明确路径，不使用 `git add .`：

```powershell
git add <文件或目录>
git diff --cached --check
git diff --cached --stat
git commit -m "说明本次完成的单一目标"
git push
```

提交前至少运行与改动直接相关的测试。V23 诊断脚本的基础测试命令为：

```powershell
python -B analysis/test_v21_bht_redistribution_scan.py
```

## 仓库卫生

- 不提交 `.mod`、`.obj`、重新生成的 `.exe`、临时日志和完整运行输出。
- 历史提交中已有部分构建产物；后续重新编译造成的变化不再暂存。
- 案例输入、可复现实验所需配置、汇总 CSV 和诊断文档可以提交。
- 推送到公开仓库前检查凭据、私钥、本机令牌和不应公开的数据。
- 不强制推送 `main`，不改写已经同步的公共历史。

## 建议的里程碑顺序

V24 按以下顺序形成独立、可验证的提交：

1. 修正尾水域与水库的接口拓扑。
2. 建立双方共享的唯一界面通量及离散守恒检查。
3. 保留跨时间步的尾水分段状态。
4. 增加完整时段的精度、守恒、稳定性和性能验收。
