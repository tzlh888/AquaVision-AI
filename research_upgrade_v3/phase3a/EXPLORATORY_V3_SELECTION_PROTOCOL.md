# AquaVision exploratory v3 模型选择冻结协议

冻结日期：2026-10-12  
适用范围：未来 Phase 3B exploratory proxy-segmentation；**本轮未训练模型，本协议不改变任何历史获选模型。**

## 1. 研究目标与证据等级

目标是预测 processed/resampled CyAN DN 的 Low/Moderate/High 像素 bin，并提高 High proxy 的识别质量。它不是现场危险、毒素、细胞数或部署级预警任务。所有 v2 validation/test 结果已查看，均为 legacy，不能用于选择 v3 配置。

## 2. 数据资格门槛（先于任何训练）

只有同时满足以下条件，才允许执行本选择协议：

1. 每条样本必须有可验证的 Sentinel product/scene ID、sensing timestamp、CRS、footprint、waterbody ID、source hashes 和 label-generation version。
2. Train、Validation、sealed Test 之间不得共享 waterbody、scene/product、物理 footprint、author-grid component、sample ID 或 Sentinel array hash。相交 waterbody/footprint 的所有 patch 必须作为同一 group。
3. Validation 至少有 **3 个已核实、含 High 的独立地理评估单元**，并覆盖至少 2 个 waterbody 和 3 个 scene/product；Train 至少 3 个；sealed Test 至少 3 个。这里的“单元”按 `waterbody × non-overlapping scene/event cluster` 定义，不能用 patch 或 pixel 替代。
4. 每个含 High 单元至少有 2 个日期、跨度≥30 天、≥3 个含 High patch、≥100 个 High reference pixels；这些只是最低可计算门槛，不是统计功效证明。
5. 三类必须在 Train 和每个 aggregate Validation partition 中出现；每个 Validation High 单元必须有正类。无法计算的指标触发 `NO QUALIFIED MODEL`，不得用 0 或丢弃该单元掩盖。
6. 当前 v2 Validation 只有 1 个 candidate component，且 lake/scene/footprint 未核实，因此**当前数据不通过本数据门槛**。

## 3. 候选与训练控制

- 候选模型、预处理、loss、class weighting、bands、seed、epoch 上限和停止规则必须在首次 fit 前写入独立 preregistration。
- 所有 normalization、sampling、augmentation、class weights 和 calibration 只能在对应 Train fold 内拟合。
- Validation 只用于资格和候选选择；sealed Test 在唯一配置冻结后只打开一次。
- legacy v2 Test/Validation 不得决定 architecture、loss、weight、threshold、band subset、epoch 或 calibration。
- 不允许从多个 seed 中事后挑最优；固定 seed 列表，报告全部 seed 和 group-level 分布。

## 4. 模型资格门槛

以下阈值是最低 exploratory competence floor，不是部署标准，也不是根据旧 Test F1 倒推：

| 指标（Validation） | 门槛 | 理由 |
|---|---:|---|
| High Recall | ≥0.50 | 至少识别多数 proxy High；低于此值与 High 识别目标不一致 |
| High F1 | ≥0.50 | 防止仅靠广泛预测 High 获得 recall |
| Low F1 | ≥0.50 | 防止多数类灾难性退化 |
| Moderate F1 | ≥0.40 | 要求非零且有实质区分，避免二类化 |
| Macro-F1 | ≥0.50 | 三类总体最低能力 |
| 每个 High component recall | >0 | 任何独立 High 单元完全漏检即不合格 |
| 可计算性 | 全部定义 | 预测正例为零时 precision/F1 必须显式 undefined；模型不合格 |

必须同时输出三类 confusion matrix、support、precision/recall/F1、pooled metric、equal-component macro、每 component metric 和每 seed metric。Precision 不是独立资格阈值，但通过 High F1 约束进入资格；其实际值必须完整报告。

## 5. 选择顺序

先应用全部 hard gates。若无模型通过，输出 **NO QUALIFIED MODEL** 并停止；不得放宽阈值或指定“最佳失败模型”为 winner。

若多个模型合格，按以下冻结顺序选择：

1. equal-component mean High F1（每个 verified High component 权重相等）；
2. equal-component mean High Recall；
3. pooled Macro-F1；
4. 更小的跨 seed/component 离散度；
5. 参数更少、流程更简单者；
6. 固定 experiment ID 字典序。

像素池化 High F1 不能作为首要选择指标，避免大 component 主导。不得以 sealed Test 打破平局。

## 6. 不确定性

- Validation 单元不足 10 个时，只报告每单元值、equal-unit 均值、范围和 leave-one-unit-out sensitivity，不报告总体 population CI。
- 达到至少 10 个验证单元后，才允许以 verified unit 为 resampling cluster 的 bootstrap 95% interval；禁止 pixel bootstrap。
- 日期/patch 是单元内重复测量，不增加独立地理样本数。
- CI 或 CV 只描述本开发分布的不确定性，不保证部署可靠性。

## 7. 当前历史规则的问题

Phase 4 历史规则以 Validation Macro-F1 为 primary、High F1 为 secondary，只要求 Low F1≥0.50、Moderate F1≥0.25；没有 High Recall/High F1 hard gate。因此 NDCI 可在 Validation High F1=0 时仍成为历史 winner。规则同时依赖单一 Validation component，无法检验跨地理稳定性。历史规则当时有 preregistration 且结果保存完整，但与现在的 High 识别目标不一致。

历史 NDCI winner、LR/RF/CNN 结果和 diagnostic weighted DeepLab 全部保留；v3 协议不追溯改写历史选择。

## 8. 停止与失败解释

- 数据资格不满足：停止，状态 `DATA GATE FAILED`。
- 无模型通过全部门槛：停止，状态 `NO QUALIFIED MODEL`。
- High 改善但 Low/Moderate 或 Macro gate 失败：解释为 proxy sensitivity–specificity trade-off，不宣称改进模型。
- 单元间不稳定或单元数过少：只作 exploratory association，不作跨地域泛化结论。
- 任一 provenance/hash/split 冲突：隔离问题样本，重新冻结 manifest；不得静默修补。

## 9. 本轮状态

协议文本和自动化资格函数已经冻结并测试，但当前 v2 数据门槛失败。因此它已“设计完成”，尚未“具备可靠执行条件”。

