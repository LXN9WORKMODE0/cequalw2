# CE-QUAL-W2 水动力局限性专题档案

本页回答什么问题：这个专题目录研究什么、为什么单独建档、应该先读哪几页，以及这些结论最终要服务什么决策。

Updated: 2026-04-14

## 目录定位

这个目录面向你当前正在研究的单个中间水库。

目标不是复述 CE-QUAL-W2 的全部能力，而是集中回答一个更具体的问题：

CE-QUAL-W2 在“低水位快流河道态”和“高水位淹没回水态”之间连续切换时，为什么会出现纵向前沿推进偏快、垂向响应偏硬，以及在保留 laterally averaged 框架的前提下还能怎么优化。

四库串联仍然是重要背景，但这里只把它视为边界和调度语境，不把整个四库系统当作这批文档的主模型对象。

## 阅读顺序

1. [01_core_conclusions.md](./01_core_conclusions.md)
2. [02_solver_principles.md](./02_solver_principles.md)
3. [04_failure_mechanisms_in_variable_backwater.md](./04_failure_mechanisms_in_variable_backwater.md)
4. [05_optimization_roadmap.md](./05_optimization_roadmap.md)
5. [03_literature_review.md](./03_literature_review.md)
6. [06_multiagent_discussion.md](./06_multiagent_discussion.md)
7. [07_xld_2021_case_waterlevel_analysis.md](./07_xld_2021_case_waterlevel_analysis.md)
8. [08_conversation_findings_log.md](./08_conversation_findings_log.md)
9. [09_structural_minimal_test_set.md](./09_structural_minimal_test_set.md)
10. [10_code_logic_review.md](./10_code_logic_review.md)
11. [11_hydrodynamic_design_and_tailriver_limitations.md](./11_hydrodynamic_design_and_tailriver_limitations.md)
12. [13_channel_slope_and_river_mode_limitations.md](./13_channel_slope_and_river_mode_limitations.md)
13. [14_methodology_group3_borrowed_mechanisms.md](./14_methodology_group3_borrowed_mechanisms.md)
14. [15_w2_hydrodynamic_upgrade_blueprint.md](./15_w2_hydrodynamic_upgrade_blueprint.md)
15. [16_v0_v1_foundation_implementation.md](./16_v0_v1_foundation_implementation.md)
16. [17_v2_continuous_front_implementation.md](./17_v2_continuous_front_implementation.md)
17. [18_v3_inner_coupling_implementation.md](./18_v3_inner_coupling_implementation.md)
18. [19_v4_front_geometry_implementation.md](./19_v4_front_geometry_implementation.md)
19. [20_v5_transition_closure_implementation.md](./20_v5_transition_closure_implementation.md)
20. [21_v6_tailreach_scaffold_implementation.md](./21_v6_tailreach_scaffold_implementation.md)
21. [22_v7_minimal_tailreach_stage_implementation.md](./22_v7_minimal_tailreach_stage_implementation.md)
22. [23_v8_v9_tail_feedback_implementation.md](./23_v8_v9_tail_feedback_implementation.md)
23. [24_v10_tail_discharge_coupling_implementation.md](./24_v10_tail_discharge_coupling_implementation.md)
24. [25_hybrid_tailreach_completion_blueprint.md](./25_hybrid_tailreach_completion_blueprint.md)
25. [26_v11_fixed_tail_domain_implementation.md](./26_v11_fixed_tail_domain_implementation.md)
26. [27_v12_reach_state_evolution_implementation.md](./27_v12_reach_state_evolution_implementation.md)
27. [28_v13_transition_state_reach_implementation.md](./28_v13_transition_state_reach_implementation.md)
28. [29_v14_stronger_coupled_hybrid_implementation.md](./29_v14_stronger_coupled_hybrid_implementation.md)
29. [30_v15_multisegment_tail_domain_implementation.md](./30_v15_multisegment_tail_domain_implementation.md)
30. [31_v16_segmentwise_reach_state_implementation.md](./31_v16_segmentwise_reach_state_implementation.md)
31. [32_v17_segmentwise_transition_closure_implementation.md](./32_v17_segmentwise_transition_closure_implementation.md)
32. [33_v18_multisegment_hybrid_coupling_implementation.md](./33_v18_multisegment_hybrid_coupling_implementation.md)
33. [34_v18_performance_rigidity_diagnosis.md](./34_v18_performance_rigidity_diagnosis.md)
34. [35_v19_interface_residual_implementation.md](./35_v19_interface_residual_implementation.md)
35. [36_v20_interface_iteration_implementation.md](./36_v20_interface_iteration_implementation.md)
36. [37_v21_reduced_implicit_interface_implementation.md](./37_v21_reduced_implicit_interface_implementation.md)
37. [38_v22_distributed_path_diagnosis.md](./38_v22_distributed_path_diagnosis.md)
38. [39_v23_q_update_mode_diagnosis.md](./39_v23_q_update_mode_diagnosis.md)
39. [40_v24_interface_conservation_design.md](./40_v24_interface_conservation_design.md)
40. [references.md](./references.md)

## 已固定的研究口径

- CE-QUAL-W2 的主水动力更接近“侧向平均、静压、自由液面隐式解、速度后校正”的框架，而不是完整的全耦合动波求解器。
- 这个模型不是不能做回水，而是“不擅长强切换、强顶托、结构物流量频繁变工况、回水末端来回摆动”的场景。
- 你当前最值得关注的短板不是横向平均本身，而是分裂推进、边界和内部水头处理、结构物流量硬切换、诊断式垂向速度和阈值式层调整的叠加效应。
- 如果继续沿 W2 路线优化，优先级应该放在每步内迭代耦合、结构物流量平滑切换、边界松弛、垂向混合与层调整迟滞、局部网格和时间步加密，而不是一上来就换成全库 3D。

## 文件分工

- `01_core_conclusions.md`: 先给结论，适合快速对齐口径。
- `02_solver_principles.md`: 解释代码里的求解顺序和物理含义。
- `03_literature_review.md`: 整理官方手册、综述、方法论文和工程应用。
- `04_failure_mechanisms_in_variable_backwater.md`: 把“偏快”和“偏硬”拆成可定位的机理链。
- `05_optimization_roadmap.md`: 面向后续源码改造，给出优先级、接口和风险。
- `06_multiagent_discussion.md`: 保留多 agent 讨论过程和采纳口径。
- `07_xld_2021_case_waterlevel_analysis.md`: 记录 `实际案例` 目录下 XLD 2021 案例的坝前水位、水面线与误差源分析。
- `08_conversation_findings_log.md`: 保留对话推进过程中逐步确认、修正和固定下来的关键发现。
- `09_structural_minimal_test_set.md`: 记录“剥离输入误差后检验 W2 结构性局限”的最小实验集及其结论。
- `10_code_logic_review.md`: 直接从源码出发审查导致 `SEG 2` 晚激活和水面线塌缩的关键逻辑。
- `11_hydrodynamic_design_and_tailriver_limitations.md`: 从水动力设计思想出发，解释 W2 为什么适合库区但不适合当前库尾河流段。
- `13_channel_slope_and_river_mode_limitations.md`: 解释 W2 纯河道模拟中的 `channel slope/GRAV` 项意味着什么，以及这为什么进一步说明它对库尾河流态-回水态过渡并非天然合适。
- `14_methodology_group3_borrowed_mechanisms.md`: 从“借鉴 EFDC/MIKE 的哪些数值思想”角度，整理可移植机制与升级顺序。
- `15_w2_hydrodynamic_upgrade_blueprint.md`: 给出正式的升级蓝图、版本管理策略、成组落地原则、各版本束的文件范围与止损条件。
- `16_v0_v1_foundation_implementation.md`: 记录第一版真正落地的 `V0 + 保守 V1` 基础实现、调试过程中确认过的边界语义、以及 smoke test 验证结果。
- `17_v2_continuous_front_implementation.md`: 记录前沿缓冲段状态机、迟滞、代理湿润深度和 V2 smoke 验证结果，明确说明它已经超出纯日志层，但还没进入完整湿润单元求解。
- `18_v3_inner_coupling_implementation.md`: 记录 V3 的真实边界，即“第二次源汇刷新与差值诊断”已经稳定落地，但完整双次水动力推进在当前框架下会失稳，因此被有意收缩。
- `19_v4_front_geometry_implementation.md`: 记录 front buffer 的连续代理几何 `AREA/VOLUME/HRAD` 已经落地，并说明它们目前仍是几何表示层，还没反馈进主水动力矩阵。
- `20_v5_transition_closure_implementation.md`: 记录 front state/geometry 已经开始反馈进局部底摩阻闭合，同时说明 `GRAV` 仍保持诊断态，尚未进入全套状态相关动力闭合。
- `21_v6_tailreach_scaffold_implementation.md`: 记录 `tailreach <-> reservoir` 的耦合面已经正式变成代码对象，并说明这还只是混合尾段求解器的脚手架，不是完整 1D 子模型。
- `references.md`: 统一编号、链接、引用方式和结论映射。

## 与现有文档体系的关系

- 这个目录属于 `docs/reference/`，因为它是“原理、局限性、改造路线”的长期研究档案。
- 它不是 `docs/current/` 的运行基线，不替代当前可运行案例和最近工作记录。
- 它也不是 `docs/history/` 的构建调试记录，不以时间顺序保存临时状态。

## 使用建议

- 如果你要和别人快速说明“为什么现在的模拟不够准”，优先看 `01`、`04`、`07`、`09`、`10` 和 `11`。
- 如果你要开始动源码，先看 `02` 再看 `05`。
- 如果你要写报告、开题或和其他模型对比，优先看 `03`、`06` 和 `references.md`。
